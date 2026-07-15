import stripe
import os
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

PLAN_PRICES = {
    "pro":       os.getenv("STRIPE_PRO_PRICE_ID"),
    "executive": os.getenv("STRIPE_EXECUTIVE_PRICE_ID"),
}

router = APIRouter(prefix="/stripe", tags=["stripe"])


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    body = await request.json()
    plan = body.get("plan")

    if plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail="Invalid plan")

    price_id = PLAN_PRICES[plan]
    if not price_id:
        raise HTTPException(status_code=400, detail="Price ID not configured")

    # Existing customer check
    subscription = db.query(models.Subscription).filter(
        models.Subscription.user_id == current_user.id
    ).first()

    customer_id = subscription.stripe_customer_id if subscription else None

    try:
        # Stripe customer banao agar nahi hai
        if not customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.name,
                metadata={"user_id": str(current_user.id)}
            )
            customer_id = customer.id

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{FRONTEND_URL}/dashboard?payment=success&plan={plan}",
            cancel_url=f"{FRONTEND_URL}/pricing?payment=canceled",
            metadata={
                "user_id": str(current_user.id),
                "plan":    plan,
            },
            subscription_data={
                "metadata": {
                    "user_id": str(current_user.id),
                    "plan":    plan,
                }
            }
        )

        # Save customer id agar naya hai
        if not subscription:
            new_sub = models.Subscription(
                user_id=current_user.id,
                stripe_customer_id=customer_id,
                plan="free",
                status="pending"
            )
            db.add(new_sub)
            db.commit()
        elif not subscription.stripe_customer_id:
            subscription.stripe_customer_id = customer_id
            db.commit()

        return {"checkout_url": session.url, "session_id": session.id}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = int(session["metadata"].get("user_id", 0))
        plan = session["metadata"].get("plan", "free")
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        if user_id:
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if user:
                user.plan = plan
                db.commit()
                print(f"✅ User {user_id} plan updated to {plan}")

            sub = db.query(models.Subscription).filter(
                models.Subscription.user_id == user_id
            ).first()

            if sub:
                sub.plan = plan
                sub.status = "active"
                sub.stripe_customer_id = customer_id
                sub.stripe_subscription_id = subscription_id
                db.commit()
            else:
                new_sub = models.Subscription(
                    user_id=user_id,
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription_id,
                    plan=plan,
                    status="active"
                )
                db.add(new_sub)
                db.commit()

    elif event["type"] == "customer.subscription.updated":
        stripe_sub = event["data"]["object"]
        subscription_id = stripe_sub["id"]
        status = stripe_sub["status"]
        plan_meta = stripe_sub.get("metadata", {}).get("plan", "free")
        period_end = datetime.fromtimestamp(stripe_sub["current_period_end"])

        sub = db.query(models.Subscription).filter(
            models.Subscription.stripe_subscription_id == subscription_id
        ).first()

        if sub:
            sub.status = status
            sub.current_period_end = period_end
            if status == "active":
                sub.plan = plan_meta
                user = db.query(models.User).filter(
                    models.User.id == sub.user_id
                ).first()
                if user:
                    user.plan = plan_meta
                    db.commit()

    elif event["type"] == "customer.subscription.deleted":
        stripe_sub = event["data"]["object"]
        subscription_id = stripe_sub["id"]

        sub = db.query(models.Subscription).filter(
            models.Subscription.stripe_subscription_id == subscription_id
        ).first()

        if sub:
            sub.status = "canceled"
            sub.plan = "free"
            user = db.query(models.User).filter(
                models.User.id == sub.user_id
            ).first()
            if user:
                user.plan = "free"
                db.commit()

    return {"received": True}

@router.get("/subscription")
def get_subscription(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    sub = db.query(models.Subscription).filter(
        models.Subscription.user_id == current_user.id
    ).first()

    return {
        "plan":                    current_user.plan,
        "stripe_subscription_id":  sub.stripe_subscription_id if sub else None,
        "status":                  sub.status if sub else "free",
        "current_period_end":      sub.current_period_end if sub else None,
    }


@router.post("/cancel")
async def cancel_subscription(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    sub = db.query(models.Subscription).filter(
        models.Subscription.user_id == current_user.id
    ).first()

    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(status_code=404, detail="No active subscription")

    try:
        stripe.Subscription.modify(
            sub.stripe_subscription_id,
            cancel_at_period_end=True
        )
        sub.status = "canceling"
        db.commit()
        return {"message": "Subscription will cancel at period end"}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))