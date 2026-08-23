from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from email_service import send_daily_exercise_email, send_weekly_progress_email, send_test_email
import models
import random
from plan_guard import check_feature_access

router = APIRouter(prefix="/email", tags=["email"])


@router.post("/test")
def test_email(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    success = send_test_email(current_user, db)
    if success:
        return {"message": f"Test email sent to {current_user.email}"}
    raise HTTPException(status_code=500, detail="Failed to send test email")


@router.post("/send-daily")
def send_daily(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    check_feature_access(current_user, "daily_exercises")
    user_program = db.query(models.UserProgram).filter(
        models.UserProgram.user_id == current_user.id,
        models.UserProgram.status == "active"
    ).first()

    if user_program:
        program = db.query(models.Program).filter(
            models.Program.id == user_program.program_id
        ).first()
        categories = program.focus.split(",") if program.focus else ["pause_control"]
        day_index = (user_program.current_day - 1) % len(categories)
        category = categories[day_index].strip()
        exercises = db.query(models.Exercise).filter(
            models.Exercise.category == category
        ).all()
    else:
        exercises = db.query(models.Exercise).all()

    if not exercises:
        raise HTTPException(status_code=404, detail="No exercises found")

    exercise = random.choice(exercises)
    background_tasks.add_task(send_daily_exercise_email, current_user, exercise, db)
    return {"message": f"Daily exercise email sending to {current_user.email}", "exercise": exercise.title}


@router.post("/send-weekly")
def send_weekly(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    reports = db.query(models.Report).filter(
        models.Report.user_id == current_user.id
    ).order_by(models.Report.created_at.desc()).all()

    if not reports:
        raise HTTPException(status_code=404, detail="No reports found — record first")

    latest = reports[0]
    prev = reports[1] if len(reports) > 1 else None
    background_tasks.add_task(send_weekly_progress_email, current_user, latest, prev, db)
    return {"message": f"Weekly progress email sending to {current_user.email}"}


@router.get("/logs")
def get_email_logs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logs = db.query(models.EmailLog).filter(
        models.EmailLog.user_id == current_user.id
    ).order_by(models.EmailLog.sent_at.desc()).limit(20).all()

    return [
        {
            "id":            log.id,
            "email_type":    log.email_type,
            "email_subject": log.email_subject,
            "status":        log.status,
            "sent_at":       log.sent_at,
        }
        for log in logs
    ]


@router.post("/send-missed-practice")
def send_missed_practice(db: Session = Depends(get_db)):
    from datetime import datetime, timedelta, date
    from email_service import send_missed_practice_email

    three_days_ago = (datetime.utcnow() - timedelta(days=3)).date().isoformat()
    users = db.query(models.User).all()
    sent = 0

    for user in users:
        last_activity = db.query(models.StreakLog).filter(
            models.StreakLog.user_id == user.id
        ).order_by(models.StreakLog.activity_date.desc()).first()

        has_recordings = db.query(models.Recording).filter(
            models.Recording.user_id == user.id
        ).count() > 0

        if has_recordings:
            if not last_activity or last_activity.activity_date <= three_days_ago:
                days_missed = 3
                if last_activity:
                    last = date.fromisoformat(last_activity.activity_date)
                    days_missed = (date.today() - last).days
                send_missed_practice_email(user, days_missed, db)
                sent += 1

    return {"sent": sent}


@router.post("/send-monthly")
def send_monthly_reports(db: Session = Depends(get_db)):
    from email_service import send_monthly_report_email
    users = db.query(models.User).all()
    sent = 0
    for user in users:
        has_recordings = db.query(models.Recording).filter(
            models.Recording.user_id == user.id
        ).count() > 0
        if has_recordings:
            if send_monthly_report_email(user, db):
                sent += 1
    return {"sent": sent}


@router.post("/send-exercise-recommendation")
def send_exercise_recommendation(db: Session = Depends(get_db)):
    from email_service import send_exercise_recommendation_email
    users = db.query(models.User).all()
    sent = 0
    for user in users:
        has_report = db.query(models.Report).filter(
            models.Report.user_id == user.id
        ).first()
        if has_report:
            if send_exercise_recommendation_email(user, db):
                sent += 1
    return {"sent": sent, "message": f"Exercise recommendation emails sent to {sent} users"}


@router.post("/send-morning")
def send_morning_emails(db: Session = Depends(get_db)):
    """Runs at 8 AM — Morning Blueprint email"""
    from email_service import send_morning_email
    users = db.query(models.User).all()
    sent = 0
    for user in users:
        has_report = db.query(models.Report).filter(
            models.Report.user_id == user.id
        ).first()
        if has_report:
            if send_morning_email(user, db):
                sent += 1
    return {"sent": sent, "message": f"Morning blueprint emails sent to {sent} users"}


@router.post("/send-afternoon")
def send_afternoon_emails(db: Session = Depends(get_db)):
    """Runs at 1 PM — Score Report email"""
    from email_service import send_afternoon_email
    users = db.query(models.User).all()
    sent = 0
    for user in users:
        has_report = db.query(models.Report).filter(
            models.Report.user_id == user.id
        ).first()
        if has_report:
            if send_afternoon_email(user, db):
                sent += 1
    return {"sent": sent, "message": f"Afternoon report emails sent to {sent} users"}


@router.post("/send-evening")
def send_evening_emails(db: Session = Depends(get_db)):
    """Runs at 6 PM — Evening Progress Review email"""
    from email_service import send_evening_email
    users = db.query(models.User).all()
    sent = 0
    for user in users:
        has_report = db.query(models.Report).filter(
            models.Report.user_id == user.id
        ).first()
        if has_report:
            if send_evening_email(user, db):
                sent += 1
    return {"sent": sent, "message": f"Evening review emails sent to {sent} users"}