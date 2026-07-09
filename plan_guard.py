from fastapi import HTTPException
from sqlalchemy.orm import Session
import models


PLAN_LIMITS = {
    "free": {
        "max_analyses": 1,
        "daily_exercises": False,
        "progress_tracking": False,
        "weekly_reports": False,
        "programs": False,
        "executive_program": False,
    },
    "pro": {
        "max_analyses": None,  # unlimited
        "daily_exercises": True,
        "progress_tracking": True,
        "weekly_reports": True,
        "programs": True,
        "executive_program": False,
    },
    "executive": {
        "max_analyses": None,
        "daily_exercises": True,
        "progress_tracking": True,
        "weekly_reports": True,
        "programs": True,
        "executive_program": True,
    },
}


def check_analysis_limit(user: models.User, db: Session):
    """Free user sirf 1 analysis kar sakta hai"""
    plan = user.plan or "free"
    limit = PLAN_LIMITS[plan]["max_analyses"]

    if limit is None:
        return  # unlimited

    total = db.query(models.Recording).filter(
        models.Recording.user_id == user.id
    ).count()

    if total >= limit:
        raise HTTPException(
            status_code=403,
            detail={
                "error":   "plan_limit_reached",
                "message": f"Free plan allows {limit} voice analysis. Upgrade to Pro for unlimited analyses.",
                "upgrade_url": "/pricing",
            }
        )


def check_feature_access(user: models.User, feature: str):
    """Feature access check karo plan ke mutabiq"""
    plan = user.plan or "free"
    has_access = PLAN_LIMITS.get(plan, {}).get(feature, False)

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail={
                "error":       "feature_locked",
                "message":     f"This feature requires a paid plan. Upgrade to access it.",
                "feature":     feature,
                "upgrade_url": "/pricing",
            }
        )


def get_plan_features(plan: str) -> dict:
    """User ka plan features return karo"""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])