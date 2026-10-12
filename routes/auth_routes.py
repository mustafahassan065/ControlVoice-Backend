from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth
import os
import httpx

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://voicecontrol.tech")
BACKEND_URL = os.getenv("BACKEND_URL", "https://api.voicecontrol.tech")

# ─── Normal Register ───────────────────────────────────────────────────────────

@router.post("/register", response_model=schemas.Token)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = auth.hash_password(user_data.password)
    user = models.User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed,
        onboarding_completed=0
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        from email_service import send_welcome_email
        send_welcome_email(user, db)
    except Exception as e:
        print(f"Welcome email error: {e}")

    token = auth.create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "onboarding_required": True
    }

# ─── Normal Login ──────────────────────────────────────────────────────────────

@router.post("/login", response_model=schemas.Token)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()
    if not user or not user.password_hash or not auth.verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = auth.create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "onboarding_required": user.onboarding_completed == 0
    }

# ─── Google OAuth ──────────────────────────────────────────────────────────────

@router.get("/google")
def google_login():
    """Redirect user to Google OAuth consent screen"""
    redirect_uri = f"{BACKEND_URL}/auth/google/callback"
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback — exchange code for token, create/login user"""
    redirect_uri = f"{BACKEND_URL}/auth/google/callback"

    # 1. Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
        )
    token_data = token_resp.json()
    access_token_google = token_data.get("access_token")

    if not access_token_google:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=google_failed")

    # 2. Get user info from Google
    async with httpx.AsyncClient() as client:
        user_info_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token_google}"}
        )
    user_info = user_info_resp.json()

    google_id = user_info.get("id")
    email = user_info.get("email")
    name = user_info.get("name", "")
    avatar_url = user_info.get("picture", "")

    if not email or not google_id:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=google_no_email")

    # 3. Find or create user
    user = db.query(models.User).filter(models.User.google_id == google_id).first()

    if not user:
        # Check if email already exists (user signed up normally before)
        user = db.query(models.User).filter(models.User.email == email).first()
        if user:
            # Link Google to existing account
            user.google_id = google_id
            user.avatar_url = avatar_url
        else:
            # Brand new user via Google
            user = models.User(
                name=name,
                email=email,
                google_id=google_id,
                avatar_url=avatar_url,
                password_hash=None,
                onboarding_completed=0
            )
            db.add(user)
            db.flush()

            try:
                from email_service import send_welcome_email
                send_welcome_email(user, db)
            except Exception as e:
                print(f"Welcome email error: {e}")

    db.commit()
    db.refresh(user)

    # 4. Create JWT and redirect to frontend
    jwt_token = auth.create_access_token({"sub": str(user.id)})
    onboarding = "true" if user.onboarding_completed == 0 else "false"

    return RedirectResponse(
        url=f"{FRONTEND_URL}/auth/google/success?token={jwt_token}&onboarding={onboarding}&name={name}"
    )


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user