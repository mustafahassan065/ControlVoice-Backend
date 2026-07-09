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
    # User ka active program check karo
    check_feature_access(current_user, "daily_exercises")
    user_program = db.query(models.UserProgram).filter(
        models.UserProgram.user_id == current_user.id,
        models.UserProgram.status == "active"
    ).first()

    # Exercise select karo
    if user_program:
        program = db.query(models.Program).filter(
            models.Program.id == user_program.program_id
        ).first()

        # Program focus ke mutabiq category
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

    background_tasks.add_task(
        send_daily_exercise_email,
        current_user,
        exercise,
        db
    )

    return {"message": f"Daily exercise email sending to {current_user.email}", "exercise": exercise.title}


@router.post("/send-weekly")
def send_weekly(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Latest report
    reports = db.query(models.Report).filter(
        models.Report.user_id == current_user.id
    ).order_by(models.Report.created_at.desc()).all()

    if not reports:
        raise HTTPException(status_code=404, detail="No reports found — record first")

    latest = reports[0]
    prev = reports[1] if len(reports) > 1 else None

    background_tasks.add_task(
        send_weekly_progress_email,
        current_user,
        latest,
        prev,
        db
    )

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