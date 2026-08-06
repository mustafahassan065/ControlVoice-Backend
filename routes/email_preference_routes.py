from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from auth import get_current_user
import models

router = APIRouter(prefix="/email-preferences", tags=["email-preferences"])


class PreferenceUpdate(BaseModel):
    weekly_reports:    int = 1
    practice_reminders: int = 1
    achievement_emails: int = 1
    assessment_complete: int = 1
    product_updates:   int = 1
    marketing_emails:  int = 1

@router.get("/")
def get_preferences(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    pref = db.query(models.EmailPreference).filter(
        models.EmailPreference.user_id == current_user.id
    ).first()

    if not pref:
        return {
            "weekly_reports":     1,
            "practice_reminders": 1,
            "achievement_emails": 1,
            "assessment_complete": 1,
        }

    return {
        "weekly_reports":     pref.weekly_reports     if pref else 1,
        "practice_reminders": pref.practice_reminders if pref else 1,
        "achievement_emails": pref.achievement_emails if pref else 1,
        "assessment_complete": pref.assessment_complete if pref else 1,
        "product_updates":    pref.product_updates    if pref else 1,
        "marketing_emails":   pref.marketing_emails   if pref else 1,
    }


@router.post("/")
def update_preferences(
    data: PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    pref = db.query(models.EmailPreference).filter(
        models.EmailPreference.user_id == current_user.id
    ).first()

    if pref:
        pref.weekly_reports     = data.weekly_reports
        pref.practice_reminders = data.practice_reminders
        pref.achievement_emails = data.achievement_emails
        pref.assessment_complete = data.assessment_complete
    else:
        pref = models.EmailPreference(
            user_id=current_user.id,
            weekly_reports=data.weekly_reports,
            practice_reminders=data.practice_reminders,
            achievement_emails=data.achievement_emails,
            assessment_complete=data.assessment_complete,
        )
        db.add(pref)

    db.commit()
    return {"message": "Preferences updated"}