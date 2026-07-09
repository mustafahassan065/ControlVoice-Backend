from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import SessionLocal
import models
import random
from email_service import send_daily_exercise_email, send_weekly_progress_email
import pytz


def send_daily_emails_job():
    print("⏰ Running daily email job...")
    db = SessionLocal()
    try:
        # All users with active programs
        active_programs = db.query(models.UserProgram).filter(
            models.UserProgram.status == "active"
        ).all()

        for up in active_programs:
            user = db.query(models.User).filter(
                models.User.id == up.user_id
            ).first()
            if not user:
                continue

            program = db.query(models.Program).filter(
                models.Program.id == up.program_id
            ).first()

            categories = program.focus.split(",") if program.focus else ["pause_control"]
            day_index = (up.current_day - 1) % len(categories)
            category = categories[day_index].strip()

            exercises = db.query(models.Exercise).filter(
                models.Exercise.category == category
            ).all()

            if exercises:
                exercise = random.choice(exercises)
                send_daily_exercise_email(user, exercise, db)
                print(f"✅ Daily email sent to {user.email}")

    except Exception as e:
        print(f"Daily job error: {e}")
    finally:
        db.close()


def send_weekly_emails_job():
    print("⏰ Running weekly email job...")
    db = SessionLocal()
    try:
        users = db.query(models.User).all()
        for user in users:
            reports = db.query(models.Report).filter(
                models.Report.user_id == user.id
            ).order_by(models.Report.created_at.desc()).all()

            if len(reports) >= 1:
                latest = reports[0]
                prev = reports[1] if len(reports) > 1 else None
                send_weekly_progress_email(user, latest, prev, db)
                print(f"✅ Weekly email sent to {user.email}")

    except Exception as e:
        print(f"Weekly job error: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.utc)

    # Daily at 8 AM UTC
    scheduler.add_job(
        send_daily_emails_job,
        CronTrigger(hour=8, minute=0),
        id="daily_exercise_email",
        replace_existing=True
    )

    # Weekly every Monday at 8 AM UTC
    scheduler.add_job(
        send_weekly_emails_job,
        CronTrigger(day_of_week="mon", hour=8, minute=0),
        id="weekly_progress_email",
        replace_existing=True
    )

    scheduler.start()
    print("✅ Email scheduler started — daily at 8 AM UTC, weekly on Mondays")
    return scheduler