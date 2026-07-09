import resend
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import models
import json
from datetime import datetime

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "coach@voicecontrol.ai")

CATEGORY_LABELS = {
    "pause_control":  "Pause Control",
    "strong_endings": "Strong Endings",
    "pitch_movement": "Pitch Movement",
    "pace_control":   "Pace Control",
}


def send_daily_exercise_email(user: models.User, exercise: models.Exercise, db: Session):
    subject = f"Your 3-Minute Voice Exercise — {exercise.title}"

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Voice Exercise</title>
</head>
<body style="margin:0;padding:0;background:#0A0E1A;font-family:'Inter',Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;padding:32px 16px;">

    <!-- HEADER -->
    <div style="text-align:center;margin-bottom:32px;">
      <p style="font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 8px;">VoiceControl AI</p>
      <h1 style="font-family:Georgia,serif;font-size:28px;font-weight:700;color:#FFFFFF;margin:0;line-height:1.2;">Your Daily Voice Exercise</h1>
    </div>

    <!-- GREETING -->
    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:15px;color:rgba(255,255,255,0.7);line-height:1.7;margin:0;">
        Hi <strong style="color:#FFFFFF;">{user.name.split()[0]}</strong>, here is your 3-minute exercise for today. Consistency is what separates good speakers from great ones.
      </p>
    </div>

    <!-- TODAY'S FOCUS -->
    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 6px;">Today's Focus</p>
      <p style="font-size:13px;color:rgba(201,168,76,0.8);margin:0 0 12px;">{CATEGORY_LABELS.get(exercise.category, exercise.category)}</p>
      <h2 style="font-family:Georgia,serif;font-size:22px;font-weight:700;color:#FFFFFF;margin:0;">{exercise.title}</h2>
    </div>

    <!-- HOW TO PRACTICE -->
    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.4);font-weight:600;margin:0 0 12px;">How to Practice</p>
      <p style="font-size:14px;color:rgba(255,255,255,0.7);line-height:1.7;margin:0;">{exercise.instruction}</p>
    </div>

    <!-- PRACTICE SENTENCE -->
    <div style="background:rgba(201,168,76,0.08);border:1px solid rgba(201,168,76,0.28);border-radius:12px;padding:24px;margin-bottom:16px;">
      <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 12px;">Practice Sentence</p>
      <p style="font-family:Georgia,serif;font-size:17px;color:#E8C97A;font-style:italic;line-height:1.6;margin:0;">"{exercise.practice_template}"</p>
    </div>

    <!-- TASK -->
    <div style="background:#111827;border-radius:12px;padding:20px 24px;margin-bottom:24px;border:1px solid rgba(255,255,255,0.08);display:flex;align-items:flex-start;gap:12px;">
      <span style="font-size:20px;">🎯</span>
      <p style="font-size:14px;color:rgba(255,255,255,0.7);line-height:1.6;margin:0;">
        <strong style="color:#FFFFFF;">Your task:</strong> Repeat this sentence 5 times. Record yourself on the last attempt and listen back. Focus on the technique above.
      </p>
    </div>

    <!-- CTA -->
    <div style="text-align:center;margin-bottom:32px;">
      <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/record"
         style="display:inline-block;background:#C9A84C;color:#0A0E1A;padding:13px 32px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">
        Record Today's Assessment
      </a>
    </div>

    <!-- FOOTER -->
    <div style="text-align:center;border-top:1px solid rgba(255,255,255,0.08);padding-top:20px;">
      <p style="font-size:12px;color:rgba(255,255,255,0.3);margin:0;">
        VoiceControl AI · You're receiving this because you're enrolled in a training program.<br>
        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard" style="color:rgba(201,168,76,0.6);text-decoration:none;">View Dashboard</a>
      </p>
    </div>

  </div>
</body>
</html>
"""

    try:
        response = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": user.email,
            "subject": subject,
            "html": html,
        })

        log = models.EmailLog(
            user_id=user.id,
            email_type="daily_exercise",
            email_subject=subject,
            status="sent",
            resend_id=response.get("id", ""),
        )
        db.add(log)
        db.commit()
        return True

    except Exception as e:
        log = models.EmailLog(
            user_id=user.id,
            email_type="daily_exercise",
            email_subject=subject,
            status="failed",
        )
        db.add(log)
        db.commit()
        print(f"Email error: {e}")
        return False


def send_weekly_progress_email(user: models.User, report: models.Report, prev_report: models.Report, db: Session):
    subject = "Your Voice Improved This Week 📈"

    feedback = json.loads(report.feedback) if report.feedback else {}
    prev_auth = round(prev_report.authority_score) if prev_report else round(report.authority_score) - 5

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#0A0E1A;font-family:'Inter',Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;padding:32px 16px;">

    <!-- HEADER -->
    <div style="text-align:center;margin-bottom:32px;">
      <p style="font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 8px;">VoiceControl AI</p>
      <h1 style="font-family:Georgia,serif;font-size:28px;font-weight:700;color:#FFFFFF;margin:0;">Your Weekly Progress Report</h1>
    </div>

    <!-- GREETING -->
    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:15px;color:rgba(255,255,255,0.7);line-height:1.7;margin:0;">
        Hi <strong style="color:#FFFFFF;">{user.name.split()[0]}</strong>, here is how your voice authority changed this week.
      </p>
    </div>

    <!-- AUTHORITY SCORE -->
    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(201,168,76,0.28);">
      <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 16px;">Authority Score</p>
      <div style="display:flex;align-items:center;gap:16px;">
        <div style="text-align:center;">
          <p style="font-size:11px;color:rgba(255,255,255,0.4);margin:0 0 4px;">Last Week</p>
          <p style="font-family:Georgia,serif;font-size:36px;font-weight:700;color:rgba(255,255,255,0.5);margin:0;">{prev_auth}</p>
        </div>
        <div style="font-size:24px;color:#4ADE80;">→</div>
        <div style="text-align:center;">
          <p style="font-size:11px;color:rgba(255,255,255,0.4);margin:0 0 4px;">This Week</p>
          <p style="font-family:Georgia,serif;font-size:36px;font-weight:700;color:#C9A84C;margin:0;">{round(report.authority_score)}</p>
        </div>
        <div style="margin-left:auto;text-align:center;">
          <p style="font-family:Georgia,serif;font-size:28px;font-weight:700;color:#4ADE80;margin:0;">+{round(report.authority_score) - prev_auth}</p>
          <p style="font-size:11px;color:#4ADE80;margin:4px 0 0;">improvement</p>
        </div>
      </div>
    </div>

    <!-- SCORE BREAKDOWN -->
    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.4);font-weight:600;margin:0 0 16px;">Score Breakdown</p>
      {_score_row("Confidence", round(report.confidence_score))}
      {_score_row("Presence", round(report.presence_score))}
      {_score_row("Leadership", round(report.leadership_score))}
      {_score_row("Pace Control", round(report.pace_score))}
      {_score_row("Pause Control", round(report.pause_score))}
    </div>

    <!-- LEVEL -->
    <div style="background:rgba(201,168,76,0.08);border:1px solid rgba(201,168,76,0.28);border-radius:12px;padding:20px 24px;margin-bottom:24px;text-align:center;">
      <p style="font-size:11px;color:#C9A84C;margin:0 0 6px;text-transform:uppercase;letter-spacing:0.15em;">Current Level</p>
      <p style="font-family:Georgia,serif;font-size:22px;font-weight:700;color:#E8C97A;margin:0;">{feedback.get('user_level', 'Developing Presence')}</p>
    </div>

    <!-- CTA -->
    <div style="text-align:center;margin-bottom:32px;">
      <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/record"
         style="display:inline-block;background:#C9A84C;color:#0A0E1A;padding:13px 32px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">
        Record This Week's Assessment
      </a>
    </div>

    <!-- FOOTER -->
    <div style="text-align:center;border-top:1px solid rgba(255,255,255,0.08);padding-top:20px;">
      <p style="font-size:12px;color:rgba(255,255,255,0.3);margin:0;">
        VoiceControl AI · Weekly Progress Report<br>
        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard" style="color:rgba(201,168,76,0.6);text-decoration:none;">View Dashboard</a>
      </p>
    </div>

  </div>
</body>
</html>
"""

    try:
        response = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": user.email,
            "subject": subject,
            "html": html,
        })

        log = models.EmailLog(
            user_id=user.id,
            email_type="weekly_progress",
            email_subject=subject,
            status="sent",
            resend_id=response.get("id", ""),
        )
        db.add(log)
        db.commit()
        return True

    except Exception as e:
        log = models.EmailLog(
            user_id=user.id,
            email_type="weekly_progress",
            email_subject=subject,
            status="failed",
        )
        db.add(log)
        db.commit()
        print(f"Weekly email error: {e}")
        return False


def _score_row(label: str, score: int) -> str:
    bar_width = score
    return f"""
    <div style="margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
        <span style="font-size:13px;color:rgba(255,255,255,0.6);">{label}</span>
        <span style="font-size:13px;font-weight:600;color:#C9A84C;">{score}</span>
      </div>
      <div style="background:rgba(255,255,255,0.06);border-radius:4px;height:5px;">
        <div style="background:#C9A84C;height:5px;border-radius:4px;width:{bar_width}%;"></div>
      </div>
    </div>
    """


def send_test_email(user: models.User, db: Session):
    """Test email — sirf verify karne ke liye"""
    subject = "✅ VoiceControl AI — Email System Working"

    html = f"""
<!DOCTYPE html>
<html>
<body style="background:#0A0E1A;font-family:Arial,sans-serif;padding:40px;">
  <div style="max-width:480px;margin:0 auto;background:#111827;border-radius:12px;padding:32px;border:1px solid rgba(201,168,76,0.3);">
    <p style="font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 12px;">VoiceControl AI</p>
    <h1 style="font-family:Georgia,serif;font-size:24px;color:#FFFFFF;margin:0 0 16px;">Email System Working ✅</h1>
    <p style="font-size:14px;color:rgba(255,255,255,0.6);line-height:1.7;margin:0 0 16px;">
      Hi {user.name.split()[0]}, this is a test email confirming that the Resend integration is working correctly for VoiceControl AI.
    </p>
    <p style="font-size:14px;color:rgba(255,255,255,0.6);line-height:1.7;margin:0;">
      Daily exercise emails and weekly progress reports are now ready to send.
    </p>
  </div>
</body>
</html>
"""

    try:
        response = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": user.email,
            "subject": subject,
            "html": html,
        })

        log = models.EmailLog(
            user_id=user.id,
            email_type="test",
            email_subject=subject,
            status="sent",
            resend_id=response.get("id", ""),
        )
        db.add(log)
        db.commit()
        return True

    except Exception as e:
        print(f"Test email error: {e}")
        return False