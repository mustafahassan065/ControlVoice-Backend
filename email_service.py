import resend
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import models
import json
from datetime import datetime

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
FROM_EMAIL = f"Voice Control AI <{os.getenv('FROM_EMAIL', 'info@voicecontrol.tech')}>"

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
    subject = "Your Weekly Voice Progress Report 📊"

    feedback = json.loads(report.feedback) if report.feedback else {}
    prev_auth = round(prev_report.authority_score) if prev_report else round(report.authority_score) - 5
    improvement = round(report.authority_score) - prev_auth
    improvement_text = f"+{improvement}" if improvement >= 0 else str(improvement)
    improvement_color = "#4ADE80" if improvement >= 0 else "#F87171"

    # Personal bests this week
    personal_bests = feedback.get("personal_bests", [])
    pb_html = ""
    if personal_bests:
        pb_html = """<div style="background:#111827;border-radius:12px;padding:20px 24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);">
          <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 12px;">🏆 New Personal Bests This Week</p>"""
        for pb in personal_bests:
            pb_html += f"""<p style="font-size:14px;color:#4ADE80;margin:4px 0;">✅ {pb['metric'].title()} Score: {pb['new_score']}</p>"""
        pb_html += "</div>"

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0A0E1A;font-family:'Inter',Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;padding:32px 16px;">

    <div style="text-align:center;margin-bottom:32px;">
      <p style="font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 8px;">Voice Control AI</p>
      <h1 style="font-family:Georgia,serif;font-size:28px;font-weight:700;color:#FFFFFF;margin:0;">Your Weekly Progress</h1>
    </div>

    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:15px;color:rgba(255,255,255,0.7);line-height:1.7;margin:0;">
        Hi <strong style="color:#FFFFFF;">{user.name.split()[0]}</strong>, here is your voice authority progress this week.
      </p>
    </div>

    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(201,168,76,0.28);">
      <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 16px;">Authority Score</p>
      <div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;">
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
          <p style="font-family:Georgia,serif;font-size:28px;font-weight:700;color:{improvement_color};margin:0;">{improvement_text}</p>
          <p style="font-size:11px;color:{improvement_color};margin:4px 0 0;">this week</p>
        </div>
      </div>
    </div>

    {pb_html}

    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.4);font-weight:600;margin:0 0 16px;">Score Breakdown</p>
      {_score_row("Confidence", round(report.confidence_score))}
      {_score_row("Presence",   round(report.presence_score))}
      {_score_row("Leadership", round(report.leadership_score))}
    </div>

    <div style="background:rgba(201,168,76,0.08);border:1px solid rgba(201,168,76,0.28);border-radius:12px;padding:20px 24px;margin-bottom:24px;text-align:center;">
      <p style="font-size:11px;color:#C9A84C;margin:0 0 6px;text-transform:uppercase;letter-spacing:0.15em;">Current Level</p>
      <p style="font-family:Georgia,serif;font-size:22px;font-weight:700;color:#E8C97A;margin:0;">{feedback.get('user_level', 'Developing Presence')}</p>
    </div>

    <div style="text-align:center;margin-bottom:32px;">
      <a href="{os.getenv('FRONTEND_URL', 'https://voicecontrol.tech')}/record"
         style="display:inline-block;background:#C9A84C;color:#0A0E1A;padding:13px 32px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">
        Record This Week's Assessment
      </a>
    </div>

    <div style="text-align:center;border-top:1px solid rgba(255,255,255,0.08);padding-top:20px;">
      <p style="font-size:12px;color:rgba(255,255,255,0.3);margin:0;">
        Voice Control AI · Weekly Progress Report<br>
        <a href="{os.getenv('FRONTEND_URL', 'https://voicecontrol.tech')}/dashboard" style="color:rgba(201,168,76,0.6);text-decoration:none;">View Dashboard</a>
      </p>
    </div>
  </div>
</body>
</html>"""

    try:
        response = resend.Emails.send({
            "from":    FROM_EMAIL,
            "to":      user.email,
            "subject": subject,
            "html":    html,
        })
        log = models.EmailLog(
            user_id=user.id, email_type="weekly_progress",
            email_subject=subject, status="sent",
            resend_id=response.get("id", ""),
        )
        db.add(log)
        db.commit()
        return True
    except Exception as e:
        log = models.EmailLog(
            user_id=user.id, email_type="weekly_progress",
            email_subject=subject, status="failed",
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

def send_welcome_email(user: models.User, db: Session):
    subject = "Welcome to Voice Control AI 🎙️"
    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0A0E1A;font-family:'Inter',Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;padding:32px 16px;">
    <div style="text-align:center;margin-bottom:32px;">
      <p style="font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;">Voice Control AI</p>
      <h1 style="font-family:Georgia,serif;font-size:28px;color:#FFFFFF;margin:8px 0;">Welcome, {user.name.split()[0]}.</h1>
      <p style="font-size:15px;color:rgba(255,255,255,0.6);">Your voice coaching journey starts now.</p>
    </div>
    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:15px;color:rgba(255,255,255,0.8);line-height:1.7;margin:0;">
        Voice Control AI analyzes your voice using acoustic analysis and gives you a personalized Authority Score — then recommends daily exercises to help you sound more confident, credible, and unignorable.
      </p>
    </div>
    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:24px;border:1px solid rgba(201,168,76,0.28);">
      <p style="font-size:12px;color:#C9A84C;text-transform:uppercase;letter-spacing:0.15em;margin:0 0 16px;font-weight:600;">How it works</p>
      <p style="color:rgba(255,255,255,0.7);font-size:14px;line-height:1.8;margin:0;">
        1. Record 60 seconds of speaking<br>
        2. Get your Authority Score + full analysis<br>
        3. Complete daily exercises<br>
        4. Record again weekly to track improvement
      </p>
    </div>
    <div style="text-align:center;margin-bottom:32px;">
      <a href="{os.getenv('FRONTEND_URL', 'https://voicecontrol.tech')}/record"
         style="display:inline-block;background:#C9A84C;color:#0A0E1A;padding:13px 32px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">
        Start Your First Assessment
      </a>
    </div>
    <p style="text-align:center;font-size:12px;color:rgba(255,255,255,0.3);">Voice Control AI · voicecontrol.tech</p>
  </div>
</body>
</html>"""

    try:
        response = resend.Emails.send({
            "from": FROM_EMAIL, "to": user.email,
            "subject": subject, "html": html,
        })
        log = models.EmailLog(user_id=user.id, email_type="welcome", email_subject=subject, status="sent", resend_id=response.get("id", ""))
        db.add(log); db.commit()
        return True
    except Exception as e:
        log = models.EmailLog(user_id=user.id, email_type="welcome", email_subject=subject, status="failed")
        db.add(log); db.commit()
        print(f"Welcome email error: {e}")
        return False


def send_assessment_complete_email(user: models.User, report: models.Report, db: Session):
    """Check preference before sending"""
    pref = db.query(models.EmailPreference).filter(
        models.EmailPreference.user_id == user.id
    ).first()
    if pref and not pref.assessment_complete:
        return False

    feedback = json.loads(report.feedback) if report.feedback else {}
    weaknesses = feedback.get("weaknesses", [])
    strengths = feedback.get("strengths", [])
    subject = f"Your Voice Assessment Results — Authority Score: {round(report.authority_score)}"

    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0A0E1A;font-family:'Inter',Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;padding:32px 16px;">
    <div style="text-align:center;margin-bottom:24px;">
      <p style="font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;">Voice Control AI</p>
      <h1 style="font-family:Georgia,serif;font-size:26px;color:#FFFFFF;margin:8px 0;">Your Assessment Results</h1>
    </div>
    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(201,168,76,0.28);text-align:center;">
      <p style="font-size:11px;color:#C9A84C;text-transform:uppercase;letter-spacing:0.15em;margin:0 0 8px;">Authority Score</p>
      <p style="font-family:Georgia,serif;font-size:52px;font-weight:700;color:#C9A84C;margin:0;">{round(report.authority_score)}</p>
      <p style="font-size:14px;color:rgba(255,255,255,0.5);margin:4px 0 0;">out of 100 · {feedback.get('user_level', 'Developing Presence')}</p>
    </div>
    <div style="background:#111827;border-radius:12px;padding:20px 24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:12px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.12em;margin:0 0 12px;">Score Breakdown</p>
      {_score_row("Confidence",  round(report.confidence_score))}
      {_score_row("Presence",    round(report.presence_score))}
      {_score_row("Leadership",  round(report.leadership_score))}
    </div>
    {'<div style="background:#111827;border-radius:12px;padding:20px 24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);"><p style="font-size:12px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.12em;margin:0 0 12px;">Areas to Improve</p>' + ''.join([f'<p style="color:#F87171;font-size:14px;margin:4px 0;">⚠️ {w}</p>' for w in weaknesses]) + '</div>' if weaknesses else ''}
    {'<div style="background:#111827;border-radius:12px;padding:20px 24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);"><p style="font-size:12px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.12em;margin:0 0 12px;">Your Strengths</p>' + ''.join([f'<p style="color:#4ADE80;font-size:14px;margin:4px 0;">✅ {s}</p>' for s in strengths]) + '</div>' if strengths else ''}
    <div style="text-align:center;margin-bottom:32px;">
      <a href="{os.getenv('FRONTEND_URL', 'https://voicecontrol.tech')}/exercises"
         style="display:inline-block;background:#C9A84C;color:#0A0E1A;padding:13px 32px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">
        Continue Training
      </a>
    </div>
    <p style="text-align:center;font-size:12px;color:rgba(255,255,255,0.3);">Voice Control AI · voicecontrol.tech</p>
  </div>
</body>
</html>"""

    try:
        response = resend.Emails.send({
            "from": FROM_EMAIL, "to": user.email,
            "subject": subject, "html": html,
        })
        log = models.EmailLog(user_id=user.id, email_type="assessment_complete", email_subject=subject, status="sent", resend_id=response.get("id", ""))
        db.add(log); db.commit()
        return True
    except Exception as e:
        log = models.EmailLog(user_id=user.id, email_type="assessment_complete", email_subject=subject, status="failed")
        db.add(log); db.commit()
        print(f"Assessment email error: {e}")
        return False


def send_missed_practice_email(user: models.User, days_missed: int, db: Session):
    """Check preference before sending"""
    pref = db.query(models.EmailPreference).filter(
        models.EmailPreference.user_id == user.id
    ).first()
    if pref and not pref.practice_reminders:
        return False

    subject = "Your voice misses you 🎙️"
    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0A0E1A;font-family:'Inter',Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;padding:32px 16px;">
    <div style="text-align:center;margin-bottom:32px;">
      <p style="font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;">Voice Control AI</p>
      <h1 style="font-family:Georgia,serif;font-size:26px;color:#FFFFFF;margin:8px 0;">You haven't practiced in {days_missed} days.</h1>
    </div>
    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:15px;color:rgba(255,255,255,0.7);line-height:1.7;margin:0;">
        Your voice improves with consistent practice. Today's challenge takes less than 60 seconds — and it keeps your streak alive.
      </p>
    </div>
    <div style="text-align:center;margin-bottom:32px;">
      <a href="{os.getenv('FRONTEND_URL', 'https://voicecontrol.tech')}/record"
         style="display:inline-block;background:#C9A84C;color:#0A0E1A;padding:13px 32px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">
        Start Today's Challenge
      </a>
    </div>
    <p style="text-align:center;font-size:12px;color:rgba(255,255,255,0.3);">Voice Control AI · <a href="{os.getenv('FRONTEND_URL')}/dashboard" style="color:rgba(201,168,76,0.6);text-decoration:none;">View Dashboard</a></p>
  </div>
</body>
</html>"""

    try:
        response = resend.Emails.send({
            "from": FROM_EMAIL, "to": user.email,
            "subject": subject, "html": html,
        })
        log = models.EmailLog(user_id=user.id, email_type="missed_practice", email_subject=subject, status="sent", resend_id=response.get("id", ""))
        db.add(log); db.commit()
        return True
    except Exception as e:
        log = models.EmailLog(user_id=user.id, email_type="missed_practice", email_subject=subject, status="failed")
        db.add(log); db.commit()
        print(f"Missed practice email error: {e}")
        return False


def send_personal_best_email(user: models.User, personal_bests: list, db: Session):
    """Check preference before sending"""
    pref = db.query(models.EmailPreference).filter(
        models.EmailPreference.user_id == user.id
    ).first()
    if pref and not pref.achievement_emails:
        return False

    subject = "🏆 New Personal Best — Voice Control AI"
    bests_html = ""
    for pb in personal_bests:
        improvement = f"+{pb['improvement']}" if pb.get('improvement') else "First score!"
        bests_html += f"""
        <div style="background:rgba(201,168,76,0.08);border:1px solid rgba(201,168,76,0.28);border-radius:8px;padding:16px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;">
          <div>
            <p style="font-size:12px;color:rgba(255,255,255,0.5);margin:0 0 4px;text-transform:uppercase;letter-spacing:0.1em;">{pb['metric'].title()} Score</p>
            <p style="font-family:Georgia,serif;font-size:28px;color:#C9A84C;margin:0;font-weight:700;">{pb['new_score']}</p>
          </div>
          <p style="font-size:16px;color:#4ADE80;font-weight:700;margin:0;">{improvement}</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0A0E1A;font-family:'Inter',Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;padding:32px 16px;">
    <div style="text-align:center;margin-bottom:24px;">
      <p style="font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;">Voice Control AI</p>
      <h1 style="font-family:Georgia,serif;font-size:26px;color:#FFFFFF;margin:8px 0;">New Personal Best!</h1>
      <p style="color:rgba(255,255,255,0.5);font-size:14px;">You just set a new record, {user.name.split()[0]}.</p>
    </div>
    <div style="margin-bottom:16px;">{bests_html}</div>
    <div style="background:#111827;border-radius:12px;padding:20px 24px;margin-bottom:24px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:14px;color:rgba(255,255,255,0.7);line-height:1.7;margin:0;">
        Keep building your executive voice. Every practice session moves you closer to the top.
      </p>
    </div>
    <div style="text-align:center;margin-bottom:32px;">
      <a href="{os.getenv('FRONTEND_URL', 'https://voicecontrol.tech')}/dashboard"
         style="display:inline-block;background:#C9A84C;color:#0A0E1A;padding:13px 32px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">
        View Dashboard
      </a>
    </div>
    <p style="text-align:center;font-size:12px;color:rgba(255,255,255,0.3);">Voice Control AI · voicecontrol.tech</p>
  </div>
</body>
</html>"""

    try:
        response = resend.Emails.send({
            "from": FROM_EMAIL, "to": user.email,
            "subject": subject, "html": html,
        })
        log = models.EmailLog(user_id=user.id, email_type="personal_best", email_subject=subject, status="sent", resend_id=response.get("id", ""))
        db.add(log); db.commit()
        return True
    except Exception as e:
        log = models.EmailLog(user_id=user.id, email_type="personal_best", email_subject=subject, status="failed")
        db.add(log); db.commit()
        print(f"Personal best email error: {e}")
        return False

def send_monthly_report_email(user: models.User, db: Session):
    from datetime import datetime, timedelta

    # Last 30 days ka data
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    reports = db.query(models.Report).filter(
        models.Report.user_id == user.id,
        models.Report.created_at >= thirty_days_ago
    ).order_by(models.Report.created_at.asc()).all()

    all_reports = db.query(models.Report).filter(
        models.Report.user_id == user.id
    ).order_by(models.Report.created_at.asc()).all()

    if not reports:
        return False

    total_recordings = len(reports)
    highest_score = round(max(r.authority_score for r in reports))
    avg_score = round(sum(r.authority_score for r in reports) / len(reports))
    latest = reports[-1]
    first_this_month = reports[0]
    improvement = round(latest.authority_score - first_this_month.authority_score)
    improvement_text = f"+{improvement}" if improvement >= 0 else str(improvement)
    improvement_color = "#4ADE80" if improvement >= 0 else "#F87171"

    latest_feedback = json.loads(latest.feedback) if latest.feedback else {}
    weaknesses = latest_feedback.get("weaknesses", [])

    # Best metric improvement
    score_improvements = {
        "Confidence": round(latest.confidence_score - first_this_month.confidence_score),
        "Presence":   round(latest.presence_score   - first_this_month.presence_score),
        "Leadership": round(latest.leadership_score  - first_this_month.leadership_score),
    }
    best_metric = max(score_improvements, key=score_improvements.get)
    best_metric_val = score_improvements[best_metric]

    subject = f"Your Monthly Voice Report — {datetime.utcnow().strftime('%B %Y')}"

    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0A0E1A;font-family:'Inter',Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;padding:32px 16px;">

    <div style="text-align:center;margin-bottom:32px;">
      <p style="font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 8px;">Voice Control AI</p>
      <h1 style="font-family:Georgia,serif;font-size:26px;color:#FFFFFF;margin:0;">Your Monthly Voice Report</h1>
      <p style="font-size:13px;color:rgba(255,255,255,0.4);margin:6px 0 0;">{datetime.utcnow().strftime('%B %Y')}</p>
    </div>

    <div style="background:#111827;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid rgba(201,168,76,0.28);">
      <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 16px;">This Month's Authority Score</p>
      <div style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;">
        <div style="text-align:center;">
          <p style="font-size:11px;color:rgba(255,255,255,0.4);margin:0 0 4px;">Start of Month</p>
          <p style="font-family:Georgia,serif;font-size:40px;color:rgba(255,255,255,0.5);margin:0;font-weight:700;">{round(first_this_month.authority_score)}</p>
        </div>
        <div style="font-size:20px;color:#4ADE80;">→</div>
        <div style="text-align:center;">
          <p style="font-size:11px;color:rgba(255,255,255,0.4);margin:0 0 4px;">End of Month</p>
          <p style="font-family:Georgia,serif;font-size:40px;color:#C9A84C;margin:0;font-weight:700;">{round(latest.authority_score)}</p>
        </div>
        <div style="margin-left:auto;text-align:center;">
          <p style="font-family:Georgia,serif;font-size:28px;color:{improvement_color};margin:0;font-weight:700;">{improvement_text}</p>
          <p style="font-size:11px;color:{improvement_color};margin:4px 0 0;">this month</p>
        </div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">
      <div style="background:#111827;border-radius:12px;padding:20px;border:1px solid rgba(255,255,255,0.08);text-align:center;">
        <p style="font-size:11px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.12em;margin:0 0 8px;">Total Recordings</p>
        <p style="font-family:Georgia,serif;font-size:36px;color:#FFFFFF;margin:0;font-weight:700;">{total_recordings}</p>
      </div>
      <div style="background:#111827;border-radius:12px;padding:20px;border:1px solid rgba(255,255,255,0.08);text-align:center;">
        <p style="font-size:11px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.12em;margin:0 0 8px;">Highest Score</p>
        <p style="font-family:Georgia,serif;font-size:36px;color:#C9A84C;margin:0;font-weight:700;">{highest_score}</p>
      </div>
      <div style="background:#111827;border-radius:12px;padding:20px;border:1px solid rgba(255,255,255,0.08);text-align:center;">
        <p style="font-size:11px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.12em;margin:0 0 8px;">Average Score</p>
        <p style="font-family:Georgia,serif;font-size:36px;color:#FFFFFF;margin:0;font-weight:700;">{avg_score}</p>
      </div>
      <div style="background:#111827;border-radius:12px;padding:20px;border:1px solid rgba(74,222,128,0.15);text-align:center;">
        <p style="font-size:11px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.12em;margin:0 0 8px;">Best Improvement</p>
        <p style="font-family:Georgia,serif;font-size:22px;color:#4ADE80;margin:0;font-weight:700;">{best_metric}</p>
        <p style="font-size:13px;color:#4ADE80;margin:4px 0 0;">+{best_metric_val} points</p>
      </div>
    </div>

    {'<div style="background:#111827;border-radius:12px;padding:20px 24px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.08);"><p style="font-size:11px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.12em;margin:0 0 12px;">Focus For Next Month</p>' + ''.join([f'<p style="color:#F87171;font-size:14px;margin:4px 0;">⚠️ {w}</p>' for w in weaknesses[:2]]) + '</div>' if weaknesses else ''}

    <div style="text-align:center;margin:24px 0;">
      <a href="{os.getenv('FRONTEND_URL', 'https://voicecontrol.tech')}/record"
         style="display:inline-block;background:#C9A84C;color:#0A0E1A;padding:13px 32px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">
        Start Next Month Strong
      </a>
    </div>

    <p style="text-align:center;font-size:12px;color:rgba(255,255,255,0.3);">
      Voice Control AI · Monthly Report<br>
      <a href="{os.getenv('FRONTEND_URL')}/dashboard" style="color:rgba(201,168,76,0.6);text-decoration:none;">View Dashboard</a>
    </p>
  </div>
</body>
</html>"""

    try:
        response = resend.Emails.send({
            "from": FROM_EMAIL, "to": user.email,
            "subject": subject, "html": html,
        })
        log = models.EmailLog(
            user_id=user.id,
            email_type="monthly_report",
            email_subject=subject,
            status="sent",
            resend_id=response.get("id", "")
        )
        db.add(log); db.commit()
        return True
    except Exception as e:
        log = models.EmailLog(
            user_id=user.id,
            email_type="monthly_report",
            email_subject=subject,
            status="failed"
        )
        db.add(log); db.commit()
        print(f"Monthly report email error: {e}")
        return False

def send_exercise_recommendation_email(user: models.User, db: Session):
    """
    Exercise recommendation email — based on latest report weakest score.
    Sent 3 times/day: 8 AM, 12 PM, 6 PM scheduler se.
    """
    pref = db.query(models.EmailPreference).filter(
        models.EmailPreference.user_id == user.id
    ).first()
    if pref and not pref.assessment_complete:
        return False

    latest_report = db.query(models.Report).filter(
        models.Report.user_id == user.id
    ).order_by(models.Report.created_at.desc()).first()

    if not latest_report:
        return False

    scores = {
        "pause_control":  latest_report.pause_score,
        "strong_endings": latest_report.ending_score,
        "pitch_movement": latest_report.pitch_score,
        "pace_control":   latest_report.pace_score,
    }
    weakest_category = min(scores, key=scores.get)
    weakest_score = round(scores[weakest_category])
    all_scores = {k: round(v) for k, v in scores.items()}

    exercise = db.query(models.Exercise).filter(
        models.Exercise.category == weakest_category
    ).first()

    if not exercise:
        return False

    category_label = CATEGORY_LABELS.get(weakest_category, weakest_category)
    authority_score = round(latest_report.authority_score)
    frontend_url = os.getenv("FRONTEND_URL", "https://voicecontrol.tech")
    exercises_url = f"{frontend_url}/exercises?category={weakest_category}"

    # Detailed why + how per category
    CATEGORY_DETAIL = {
        "pause_control": {
            "why": f"Your Pause Control score is {weakest_score}/100. This means you are not pausing long enough between ideas — making your speech sound rushed and less authoritative.",
            "how": "Before your most important point, stop completely. Count silently: one... two... then continue. This pause signals confidence to your listener.",
            "steps": [
                "Read your practice sentence once at your normal pace.",
                "Read it again — pause 2 full seconds before the key word.",
                "Record yourself on the third attempt.",
                "Listen back and check: did you actually pause?",
            ],
            "tip": "Professional speakers use silence as a tool. The pause is not empty — it creates anticipation."
        },
        "strong_endings": {
            "why": f"Your Strong Endings score is {weakest_score}/100. Your sentences are ending with a rising pitch — this sounds uncertain and undermines your authority.",
            "how": "At the end of every statement, consciously drop your pitch downward. Think of it as placing a full stop with your voice.",
            "steps": [
                "Say a sentence and notice if your voice rises at the end.",
                "Repeat the same sentence and deliberately lower your pitch on the last word.",
                "Record yourself saying 3 statements with strong downward endings.",
                "Listen back — does each sentence end with confidence?",
            ],
            "tip": "A rising ending turns a statement into a question. Drop your pitch and own your words."
        },
        "pitch_movement": {
            "why": f"Your Pitch Movement score is {weakest_score}/100. Your voice is staying at one level — this sounds flat and monotone, making it harder for listeners to stay engaged.",
            "how": "Identify the most important word in each sentence and raise your pitch on that word only. Let everything else stay lower.",
            "steps": [
                "Read your practice sentence in a completely flat tone.",
                "Now identify the ONE most important word.",
                "Read it again — raise your pitch on that word only.",
                "Record yourself and compare both attempts.",
            ],
            "tip": "Pitch variation is not about being dramatic. One intentional raise per sentence is enough."
        },
        "pace_control": {
            "why": f"Your Pace Control score is {weakest_score}/100. You are speaking outside the 130-160 WPM range — either too fast (losing the listener) or too slow (losing their attention).",
            "how": "Record 60 seconds of natural speech and count the words. Aim for 130-160 words. If you are over, slow down by pausing between sentences.",
            "steps": [
                "Read your practice sentence at your normal pace.",
                "Count the words and estimate your speed.",
                "Adjust: if too fast, add a breath after each sentence.",
                "Record the final attempt at your target pace.",
            ],
            "tip": "Slow is not the same as boring. A controlled pace gives your words weight."
        },
    }

    detail = CATEGORY_DETAIL.get(weakest_category, {
        "why": f"Your {category_label} score is {weakest_score}/100 — this is your current development area.",
        "how": exercise.instruction,
        "steps": ["Practice the exercise", "Record yourself", "Listen back", "Repeat"],
        "tip": "Consistent practice is the only path to improvement."
    })

    steps_html = "".join([
        f'<div style="display:flex;gap:12px;margin-bottom:10px;align-items:flex-start;">'
        f'<span style="background:rgba(201,168,76,0.15);border:1px solid rgba(201,168,76,0.3);color:#C9A84C;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;margin-top:1px;">{i+1}</span>'
        f'<p style="font-size:13px;color:rgba(255,255,255,0.75);line-height:1.6;margin:0;">{step}</p>'
        f'</div>'
        for i, step in enumerate(detail["steps"])
    ])

    scores_html = "".join([
        f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">'
        f'<span style="font-size:13px;color:rgba(255,255,255,0.6);">{CATEGORY_LABELS.get(k, k)}</span>'
        f'<span style="font-size:14px;font-weight:700;color:{"#F87171" if k == weakest_category else "#4ADE80" if v >= 70 else "#C9A84C"};">{v}/100{" ← Focus here" if k == weakest_category else ""}</span>'
        f'</div>'
        for k, v in all_scores.items()
    ])

    subject = f"AI Voice Coach — Your {category_label} needs work ({weakest_score}/100)"

    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0A0E1A;font-family:'Inter',Arial,sans-serif;">
  <div style="max-width:580px;margin:0 auto;padding:32px 16px;">

    <div style="text-align:center;margin-bottom:28px;">
      <p style="font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 6px;">Voice Control AI</p>
      <h1 style="font-family:Georgia,serif;font-size:24px;color:#FFFFFF;margin:0 0 6px;">Your AI Voice Coach</h1>
      <p style="font-size:13px;color:rgba(255,255,255,0.4);margin:0;">Personalized training based on your voice data</p>
    </div>

    <!-- GREETING + AUTHORITY SCORE -->
    <div style="background:#111827;border-radius:12px;padding:20px 24px;margin-bottom:14px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:14px;color:rgba(255,255,255,0.8);margin:0 0 10px;">
        Hi <strong style="color:#FFFFFF;">{user.name.split()[0]}</strong> — your current Authority Score is <strong style="color:#C9A84C;font-size:16px;">{authority_score}/100</strong>.
        Your AI Voice Coach has identified your biggest area to work on today.
      </p>
    </div>

    <!-- SCORE BREAKDOWN -->
    <div style="background:#111827;border-radius:12px;padding:20px 24px;margin-bottom:14px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.4);font-weight:600;margin:0 0 12px;">Your Current Scores</p>
      {scores_html}
    </div>

    <!-- WHY THIS MATTERS -->
    <div style="background:rgba(248,113,113,0.07);border:1px solid rgba(248,113,113,0.2);border-radius:12px;padding:20px 24px;margin-bottom:14px;">
      <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#F87171;font-weight:600;margin:0 0 10px;">⚠️ Why This Needs Attention</p>
      <p style="font-size:14px;color:rgba(255,255,255,0.8);line-height:1.7;margin:0;">{detail["why"]}</p>
    </div>

    <!-- TODAY'S EXERCISE -->
    <div style="background:#111827;border-radius:12px;padding:20px 24px;margin-bottom:14px;border:1px solid rgba(201,168,76,0.28);">
      <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#C9A84C;font-weight:600;margin:0 0 6px;">Today's Exercise · {category_label}</p>
      <h2 style="font-family:Georgia,serif;font-size:20px;color:#FFFFFF;margin:0 0 12px;">{exercise.title}</h2>
      <p style="font-size:14px;color:rgba(255,255,255,0.75);line-height:1.7;margin:0 0 14px;">{detail["how"]}</p>
      <div style="background:rgba(201,168,76,0.06);border-radius:8px;padding:14px 16px;">
        <p style="font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:#C9A84C;font-weight:600;margin:0 0 8px;">Practice Sentence</p>
        <p style="font-family:Georgia,serif;font-size:15px;color:#E8C97A;font-style:italic;margin:0;">"{exercise.practice_template}"</p>
      </div>
    </div>

    <!-- STEP BY STEP -->
    <div style="background:#111827;border-radius:12px;padding:20px 24px;margin-bottom:14px;border:1px solid rgba(255,255,255,0.08);">
      <p style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.4);font-weight:600;margin:0 0 14px;">How To Practice — Step by Step</p>
      {steps_html}
    </div>

    <!-- AI VOICE COACH TIP -->
    <div style="background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.18);border-radius:12px;padding:16px 20px;margin-bottom:20px;display:flex;gap:12px;align-items:flex-start;">
      <span style="font-size:20px;flex-shrink:0;">🎓</span>
      <p style="font-size:13px;color:rgba(255,255,255,0.8);line-height:1.6;margin:0;">
        <strong style="color:#C9A84C;">AI Voice Coach tip:</strong> {detail["tip"]}
      </p>
    </div>

    <!-- CTA -->
    <div style="text-align:center;margin-bottom:28px;">
      <a href="{exercises_url}"
         style="display:inline-block;background:#C9A84C;color:#0A0E1A;padding:13px 32px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;margin-bottom:10px;display:block;">
        Practice This Exercise Now →
      </a>
      <a href="{frontend_url}/record"
         style="display:inline-block;background:transparent;color:#C9A84C;padding:11px 28px;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;border:1px solid rgba(201,168,76,0.35);margin-top:8px;">
        Record a New Assessment
      </a>
    </div>

    <p style="text-align:center;font-size:12px;color:rgba(255,255,255,0.25);">
      Voice Control AI · AI Voice Coach<br>
      <a href="{frontend_url}/dashboard" style="color:rgba(201,168,76,0.5);text-decoration:none;">Dashboard</a> ·
      <a href="{frontend_url}/settings" style="color:rgba(201,168,76,0.5);text-decoration:none;">Email Settings</a>
    </p>
  </div>
</body>
</html>"""

    try:
        response = resend.Emails.send({
            "from": FROM_EMAIL, "to": user.email,
            "subject": subject, "html": html,
        })
        log = models.EmailLog(
            user_id=user.id, email_type="exercise_recommendation",
            email_subject=subject, status="sent",
            resend_id=response.get("id", "")
        )
        db.add(log); db.commit()
        return True
    except Exception as e:
        log = models.EmailLog(
            user_id=user.id, email_type="exercise_recommendation",
            email_subject=subject, status="failed"
        )
        db.add(log); db.commit()
        print(f"Exercise recommendation email error: {e}")
        return False


# ════════════════════════════════════════════════════════════
# DAILY COACH EMAIL — Single email per day
# ════════════════════════════════════════════════════════════

FOCUS_ROTATION = [
    "confidence", "pace", "pausing", "emphasis", "articulation",
    "clarity", "sentence_endings", "pressure", "presentations",
    "interviews", "leadership", "storytelling", "persuasion",
    "difficult_conversations", "networking", "disagreement",
]

FOCUS_LABELS = {
    "confidence": "Confidence",
    "pace": "Pace Control",
    "pausing": "Intentional Pausing",
    "emphasis": "Emphasis & Stress",
    "articulation": "Articulation",
    "clarity": "Clarity",
    "sentence_endings": "Sentence Endings",
    "pressure": "Speaking Under Pressure",
    "presentations": "Presentations",
    "interviews": "Interview Skills",
    "leadership": "Leadership Voice",
    "storytelling": "Storytelling",
    "persuasion": "Persuasion",
    "difficult_conversations": "Difficult Conversations",
    "networking": "Networking",
    "disagreement": "Expressing Disagreement",
}


def _get_today_focus(user_id: int, db: Session) -> str:
    """Rotate focus areas — avoid repeating recent ones"""
    recent_logs = db.query(models.EmailLog).filter(
        models.EmailLog.user_id == user_id,
        models.EmailLog.email_type == "daily_coach"
    ).order_by(models.EmailLog.sent_at.desc()).limit(16).all()

    used = []
    for log in recent_logs:
        try:
            subj = log.email_subject or ""
            for focus in FOCUS_ROTATION:
                if FOCUS_LABELS[focus].lower() in subj.lower():
                    used.append(focus)
                    break
        except:
            pass

    for focus in FOCUS_ROTATION:
        if focus not in used:
            return focus
    return FOCUS_ROTATION[len(recent_logs) % len(FOCUS_ROTATION)]


def _generate_daily_content(user_context: dict, focus: str) -> dict:
    """Generate fresh daily coaching content via OpenAI"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        focus_label = FOCUS_LABELS.get(focus, focus)
        days_inactive = user_context.get("days_inactive", 0)
        has_recent = days_inactive < 3

        inactive_note = ""
        if days_inactive >= 3:
            inactive_note = f"The user has been inactive for {days_inactive} days. Be warm and welcoming, not pressuring. Make it feel easy to return."

        prev_note = ""
        if has_recent and user_context.get("feedback"):
            prev_note = f"Recent coach observation: {user_context['feedback']}"

        prompt = f"""You are Rina, a warm and intelligent AI voice coach sending a personal daily coaching email.

Today's training focus: {focus_label}
User name: {user_context["name"]}
User goal: {user_context["goal"]}
{prev_note}
{inactive_note}

Generate a fresh, personal daily coaching email. Return ONLY valid JSON:
{{
  "opening": "2-3 sentences max. Natural, warm, personal. If there is recent session data, reference something real. Never invent progress. Sound like a real coach, not a system.",
  "sentence": "One powerful, natural English sentence for a real situation (meeting, interview, presentation, leadership, networking, etc). It must demonstrate today's focus: {focus_label}. Max 15 words.",
  "listen_instruction": "One sentence. Tell them what to notice when they listen. Focus on {focus_label}.",
  "shadow_instruction": "One sentence. How to shadow this sentence.",
  "speak_instruction": "One sentence. Encourage them to say it naturally, make it theirs.",
  "closing": "One warm short sentence. Something like 'Take this into one real conversation today.' No clichés.",
  "sign_off": "See you tomorrow — [something brief and specific about tomorrow's direction]."
}}

Rules:
- The sentence must be something a real professional would say naturally
- Never use the word 'boundaries', 'journey', 'empower' or 'transform'
- Sound personal and human, not like a marketing email
- Keep opening under 40 words
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=500,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    except Exception as e:
        print(f"Daily content generation error: {e}")
        focus_label = FOCUS_LABELS.get(focus, focus)
        return {
            "opening": f"Hi {user_context['name'].split()[0]}, today we focus on {focus_label}. One sentence. One practice. That is all.",
            "sentence": "There is one point I would like you to remember.",
            "listen_instruction": f"Notice the calm pace and the pause — that is {focus_label} in action.",
            "shadow_instruction": "Speak along with the model. Match the rhythm exactly.",
            "speak_instruction": "Now say it yourself. Make the sentence yours.",
            "closing": "Take this into one real conversation today.",
            "sign_off": "See you tomorrow — we will build something new.",
        }


def _generate_audio_url(sentence: str, user_id: int) -> str:
    """Generate model audio via ElevenLabs and upload to S3"""
    try:
        import boto3, uuid, requests

        eleven_key = os.getenv("ELEVENLABS_API_KEY")
        if not eleven_key:
            return None

        # ElevenLabs TTS — Rachel voice (calm, professional)
        response = requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
            headers={
                "xi-api-key": eleven_key,
                "Content-Type": "application/json",
            },
            json={
                "text": sentence,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.85,
                    "style": 0.0,
                    "use_speaker_boost": True,
                }
            },
            timeout=30,
        )

        if response.status_code != 200:
            print(f"ElevenLabs error: {response.text}")
            return None

        audio_bytes = response.content

        # Upload to S3
        s3 = boto3.client("s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name="eu-north-1",
        )
        bucket = os.getenv("AWS_BUCKET_NAME")
        key = f"daily-audio/{uuid.uuid4()}.mp3"
        s3.put_object(Bucket=bucket, Key=key, Body=audio_bytes, ContentType="audio/mpeg")

        return f"https://{bucket}.s3.eu-north-1.amazonaws.com/{key}"

    except Exception as e:
        print(f"Audio generation error: {e}")
        return None


def _build_user_context(user: models.User, db: Session) -> dict:
    """Build user context for AI"""
    latest = db.query(models.Report).filter(
        models.Report.user_id == user.id
    ).order_by(models.Report.created_at.desc()).first()

    from datetime import date
    last_log = db.query(models.StreakLog).filter(
        models.StreakLog.user_id == user.id
    ).order_by(models.StreakLog.activity_date.desc()).first()

    days_inactive = 0
    if last_log:
        last_date = date.fromisoformat(last_log.activity_date)
        days_inactive = (date.today() - last_date).days

    profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == user.id
    ).first()

    goal = "improving speaking confidence"
    if profile and profile.goals:
        try:
            goals = json.loads(profile.goals)
            if goals:
                goal = goals[0]
        except:
            goal = str(profile.goals)[:50]

    feedback = ""
    if latest and latest.feedback:
        try:
            fb = json.loads(latest.feedback)
            feedback = fb.get("summary", "")[:120]
        except:
            feedback = str(latest.feedback)[:120]

    return {
        "name": user.name,
        "goal": goal,
        "days_inactive": days_inactive,
        "feedback": feedback,
    }


def _generate_secure_token(user_id: int) -> str:
    try:
        import jwt as pyjwt
        from datetime import datetime, timedelta
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=7),
        }
        return pyjwt.encode(payload, os.getenv("SECRET_KEY", "secret"), algorithm="HS256")
    except:
        return str(user_id)


def send_daily_coach_email(user: models.User, db: Session) -> bool:
    """
    Single daily coaching email — premium, personal, clean.
    Replaces morning/afternoon/evening system.
    """
    pref = db.query(models.EmailPreference).filter(
        models.EmailPreference.user_id == user.id
    ).first()
    if pref and not pref.assessment_complete:
        return False

    ctx = _build_user_context(user, db)
    focus = _get_today_focus(user.id, db)
    focus_label = FOCUS_LABELS.get(focus, focus)

    # Generate content
    content = _generate_daily_content(ctx, focus)
    sentence = content.get("sentence", "There is one point I would like you to remember.")

    # Generate audio
    audio_url = _generate_audio_url(sentence, user.id)

    # Deep links
    token = _generate_secure_token(user.id)
    frontend_url = os.getenv("FRONTEND_URL", "https://voicecontrol.tech")
    coach_url = f"{frontend_url}/coach?mode=practice&token={token}&focus={focus}"
    listen_url = audio_url or f"{frontend_url}/coach?mode=listen&token={token}&focus={focus}"

    first_name = user.name.split()[0]
    subject = f"Your voice practice for today — {focus_label}"
    if ctx["days_inactive"] >= 3:
        subject = f"Ready when you are, {first_name}"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Voice Control AI</title>
</head>
<body style="margin:0;padding:0;background:#F9F8F6;font-family:'Georgia',serif;">
<div style="max-width:560px;margin:0 auto;padding:20px 16px;">

  <!-- HEADER -->
  <div style="padding:40px 0 32px;text-align:left;">
    <p style="font-size:11px;letter-spacing:0.22em;text-transform:uppercase;color:#9A9890;font-weight:600;margin:0 0 32px;font-family:'Inter',Arial,sans-serif;">
      VOICE CONTROL AI
    </p>
    <p style="font-size:28px;color:#1A1A1B;line-height:1.4;margin:0 0 16px;font-weight:400;">
      Hi {first_name},
    </p>
    <p style="font-size:17px;color:#4A4840;line-height:1.75;margin:0;font-weight:400;">
      {content.get("opening", "")}
    </p>
  </div>

  <!-- DIVIDER -->
  <div style="height:1px;background:#E8E4DC;margin:0 0 40px;"></div>

  <!-- SENTENCE LABEL -->
  <p style="font-size:10px;letter-spacing:0.22em;text-transform:uppercase;color:#9A9890;font-weight:600;margin:0 0 20px;font-family:'Inter',Arial,sans-serif;">
    YOUR SENTENCE TO PRACTICE FOR TODAY
  </p>

  <!-- THE SENTENCE — centerpiece -->
  <div style="padding:0 0 40px;">
    <p style="font-size:26px;color:#1A1A1B;line-height:1.45;margin:0;font-weight:400;font-style:italic;">
      &ldquo;{sentence}&rdquo;
    </p>
  </div>

  <!-- DIVIDER -->
  <div style="height:1px;background:#E8E4DC;margin:0 0 40px;"></div>

  <!-- LISTEN -->
  <div style="margin-bottom:36px;">
    <p style="font-size:13px;letter-spacing:0.1em;color:#1A1A1B;font-weight:700;margin:0 0 8px;font-family:'Inter',Arial,sans-serif;">
      🎧 LISTEN
    </p>
    <p style="font-size:15px;color:#6A6860;line-height:1.65;margin:0 0 16px;font-weight:400;">
      {content.get("listen_instruction", "")}
    </p>
    <a href="{listen_url}"
       style="display:inline-block;border:1.5px solid #1A1A1B;color:#1A1A1B;padding:10px 24px;border-radius:30px;font-size:12px;font-weight:700;letter-spacing:0.1em;text-decoration:none;font-family:'Inter',Arial,sans-serif;">
      LISTEN
    </a>
  </div>

  <!-- SHADOW -->
  <div style="margin-bottom:36px;">
    <p style="font-size:13px;letter-spacing:0.1em;color:#1A1A1B;font-weight:700;margin:0 0 8px;font-family:'Inter',Arial,sans-serif;">
      🗣️ SHADOW
    </p>
    <p style="font-size:15px;color:#6A6860;line-height:1.65;margin:0;font-weight:400;">
      {content.get("shadow_instruction", "")}
    </p>
  </div>

  <!-- SPEAK -->
  <div style="margin-bottom:48px;">
    <p style="font-size:13px;letter-spacing:0.1em;color:#1A1A1B;font-weight:700;margin:0 0 8px;font-family:'Inter',Arial,sans-serif;">
      🎙️ SPEAK
    </p>
    <p style="font-size:15px;color:#6A6860;line-height:1.65;margin:0;font-weight:400;">
      {content.get("speak_instruction", "")}
    </p>
  </div>

  <!-- MAIN CTA -->
  <div style="margin-bottom:48px;">
    <a href="{coach_url}"
       style="display:block;background:#1A1A1B;color:#FFFFFF;padding:18px 32px;border-radius:6px;font-size:13px;font-weight:700;letter-spacing:0.12em;text-decoration:none;text-align:center;font-family:'Inter',Arial,sans-serif;">
      PRACTISE WITH YOUR VOICE CONTROL AI COACH &rarr;
    </a>
  </div>

  <!-- DIVIDER -->
  <div style="height:1px;background:#E8E4DC;margin:0 0 36px;"></div>

  <!-- CLOSING -->
  <div style="padding-bottom:48px;">
    <p style="font-size:16px;color:#4A4840;line-height:1.7;margin:0 0 28px;font-weight:400;">
      {content.get("closing", "Take this into one real conversation today.")}
    </p>
    <p style="font-size:15px;color:#9A9890;line-height:1.6;margin:0 0 6px;font-weight:400;">
      {content.get("sign_off", "See you tomorrow.")}
    </p>
    <p style="font-size:15px;color:#1A1A1B;font-weight:600;margin:0;font-family:'Inter',Arial,sans-serif;">Rina</p>
    <p style="font-size:13px;color:#9A9890;margin:4px 0 0;font-family:'Inter',Arial,sans-serif;">Your Voice Control AI Coach</p>
  </div>

  <!-- FOOTER -->
  <div style="border-top:1px solid #E8E4DC;padding-top:24px;text-align:center;">
    <p style="font-size:11px;color:#BBBAB6;margin:0 0 6px;font-family:'Inter',Arial,sans-serif;">
      Voice Control AI &nbsp;·&nbsp;
      <a href="{frontend_url}/dashboard" style="color:#BBBAB6;text-decoration:none;">Dashboard</a>
      &nbsp;·&nbsp;
      <a href="{frontend_url}/settings" style="color:#BBBAB6;text-decoration:none;">Email Settings</a>
    </p>
    <p style="font-size:11px;color:#BBBAB6;margin:0;font-family:'Inter',Arial,sans-serif;">
      <a href="{frontend_url}/settings?unsubscribe=1" style="color:#BBBAB6;text-decoration:underline;">Unsubscribe</a>
    </p>
  </div>

</div>
</body>
</html>"""

    try:
        response = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": user.email,
            "subject": subject,
            "html": html,
        })
        db.add(models.EmailLog(
            user_id=user.id,
            email_type="daily_coach",
            email_subject=subject,
            status="sent",
            resend_id=response.get("id", "")
        ))
        db.commit()
        return True
    except Exception as e:
        db.add(models.EmailLog(
            user_id=user.id,
            email_type="daily_coach",
            email_subject=subject,
            status="failed"
        ))
        db.commit()
        print(f"Daily coach email error: {e}")
        return Fals

# ════════════════════════════════════════════════════════════
# DAILY COACH EMAIL — Single email per day
# ════════════════════════════════════════════════════════════

FOCUS_ROTATION = [
    "confidence", "pace", "pausing", "emphasis", "articulation",
    "clarity", "sentence_endings", "pressure", "presentations",
    "interviews", "leadership", "storytelling", "persuasion",
    "difficult_conversations", "networking", "disagreement",
]

FOCUS_LABELS = {
    "confidence": "Confidence",
    "pace": "Pace Control",
    "pausing": "Intentional Pausing",
    "emphasis": "Emphasis & Stress",
    "articulation": "Articulation",
    "clarity": "Clarity",
    "sentence_endings": "Sentence Endings",
    "pressure": "Speaking Under Pressure",
    "presentations": "Presentations",
    "interviews": "Interview Skills",
    "leadership": "Leadership Voice",
    "storytelling": "Storytelling",
    "persuasion": "Persuasion",
    "difficult_conversations": "Difficult Conversations",
    "networking": "Networking",
    "disagreement": "Expressing Disagreement",
}


def _get_today_focus(user_id: int, db: Session) -> str:
    """Rotate focus areas — check StudentMemory for next_focus first"""
    # Check if Rina has a recommendation
    memory = db.query(models.StudentMemory).filter(
        models.StudentMemory.user_id == user_id
    ).first()
    if memory and memory.next_focus:
        for key, label in FOCUS_LABELS.items():
            if key in memory.next_focus.lower() or label.lower() in memory.next_focus.lower():
                return key

    # Fallback: rotate
    recent_logs = db.query(models.EmailLog).filter(
        models.EmailLog.user_id == user_id,
        models.EmailLog.email_type == "daily_coach"
    ).order_by(models.EmailLog.sent_at.desc()).limit(16).all()

    used = []
    for log in recent_logs:
        try:
            subj = log.email_subject or ""
            for focus in FOCUS_ROTATION:
                if FOCUS_LABELS[focus].lower() in subj.lower():
                    used.append(focus)
                    break
        except:
            pass

    for focus in FOCUS_ROTATION:
        if focus not in used:
            return focus
    return FOCUS_ROTATION[len(recent_logs) % len(FOCUS_ROTATION)]


def _get_session_memory(user_id: int, db: Session) -> dict:
    """Get recent session summaries and memory for email context"""
    memory = db.query(models.StudentMemory).filter(
        models.StudentMemory.user_id == user_id
    ).first()

    recent = db.query(models.SessionSummary).filter(
        models.SessionSummary.user_id == user_id
    ).order_by(models.SessionSummary.created_at.desc()).limit(3).all()

    return {
        "current_focus": memory.current_focus if memory else None,
        "next_focus": memory.next_focus if memory else None,
        "rina_observation": memory.rina_observation if memory else None,
        "strongest_improvement": memory.strongest_improvement if memory else None,
        "recent_sessions": [
            {
                "date": s.session_date,
                "focus": s.focus,
                "improvement": s.improvement,
                "problem": s.problem,
                "next": s.next_session,
            }
            for s in recent
        ] if recent else [],
    }


def _generate_ai_subject(user_context: dict, session_memory: dict, focus: str) -> str:
    """Generate AI subject line based on student memory — like Rina wrote it"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        focus_label = FOCUS_LABELS.get(focus, focus)
        recent = session_memory.get("recent_sessions", [])
        last_session = recent[0] if recent else None

        memory_context = ""
        if last_session:
            memory_context = f"Last session: focused on {last_session.get('focus', '')}, improvement: {last_session.get('improvement', 'None')}. Next recommended: {last_session.get('next', '')}."
        if session_memory.get("rina_observation"):
            memory_context += f" Rina noticed: {session_memory['rina_observation']}."

        prompt = f"""You are Rina, the student's personal Voice Control AI Coach.

Write ONE compelling email subject line based on the student's coaching data.

Student: {user_context["name"]}
Today's focus: {focus_label}
Goal: {user_context["goal"]}
{memory_context}

Rules:
- Maximum 12 words
- Sound like a personal coach, not marketing software
- Always include the student's first name — it must feel personal and direct
- Do not write "Your daily practice"
- Do not include "Voice Control AI" in the subject
- Vary style: progress / curiosity / challenge / encouragement / real-life relevance
- Only reference previous progress if the data confirms it
- Never invent improvement
- Connect yesterday's work to today's next step
- No clickbait, no excessive exclamation marks

Return ONLY the subject line. No quotes, no explanation."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=50,
        )
        subject = response.choices[0].message.content.strip().strip('"').strip("'")
        return subject

    except Exception as e:
        print(f"Subject generation error: {e}")
        focus_label = FOCUS_LABELS.get(focus, focus)
        return f"Your voice practice for today — {focus_label}"


def _generate_daily_content(user_context: dict, focus: str, session_memory: dict) -> dict:
    """Generate fresh daily coaching content via OpenAI with memory"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        focus_label = FOCUS_LABELS.get(focus, focus)
        days_inactive = user_context.get("days_inactive", 0)
        recent = session_memory.get("recent_sessions", [])
        last_session = recent[0] if recent else None

        inactive_note = ""
        if days_inactive >= 3:
            inactive_note = f"The user has been inactive for {days_inactive} days. Be warm and welcoming, not pressuring."

        memory_note = ""
        if last_session:
            memory_note = f"Last session: {last_session.get('focus', '')} — improvement: {last_session.get('improvement', 'None')}. Recommended next: {last_session.get('next', '')}."
        if session_memory.get("rina_observation"):
            memory_note += f" Rina noticed: {session_memory['rina_observation']}."

        prompt = f"""You are Rina, a warm and intelligent AI voice coach sending a personal daily coaching email.

Today's training focus: {focus_label}
User name: {user_context["name"]}
User goal: {user_context["goal"]}
{memory_note}
{inactive_note}

Generate a fresh, personal daily coaching email. Return ONLY valid JSON:
{{
  "opening": "2-3 sentences max. Natural, warm, personal. If there is session memory, reference something real naturally — like a real coach would. Never say 'I remember everything'. Say things like 'Last time we worked on...' Never invent progress.",
  "sentence": "One powerful natural English sentence for a real situation. Must demonstrate today's focus: {focus_label}. Max 15 words.",
  "listen_instruction": "One sentence. Tell them what to notice. Focus on {focus_label}.",
  "shadow_instruction": "One sentence. How to shadow this sentence.",
  "speak_instruction": "One sentence. Encourage them to make it theirs.",
  "closing": "One warm short sentence. Real, not generic.",
  "sign_off": "See you tomorrow — [something brief and specific about tomorrow based on coaching plan]."
}}

Rules:
- Sound personal and human, not automated
- Never use 'boundaries', 'journey', 'empower', 'transform'
- Keep opening under 50 words
- The sentence must be something a real professional would say naturally"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=500,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    except Exception as e:
        print(f"Daily content generation error: {e}")
        return {
            "opening": f"Hi {user_context['name'].split()[0]}, today we focus on {FOCUS_LABELS.get(focus, focus)}. One sentence. One practice.",
            "sentence": "There is one point I would like you to remember.",
            "listen_instruction": "Notice the calm pace and the intentional pause.",
            "shadow_instruction": "Speak along with the model. Match the rhythm exactly.",
            "speak_instruction": "Now say it yourself. Make the sentence yours.",
            "closing": "Take this into one real conversation today.",
            "sign_off": "See you tomorrow — we will build something new.",
        }


def _generate_audio_url(sentence: str, user_id: int) -> str:
    """Generate model audio via OpenAI TTS and upload to S3"""
    try:
        import boto3, uuid
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=sentence,
            speed=0.92,
        )

        audio_bytes = response.content
        s3 = boto3.client("s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name="eu-north-1",
        )
        bucket = os.getenv("AWS_BUCKET_NAME")
        key = f"daily-audio/{uuid.uuid4()}.mp3"
        s3.put_object(Bucket=bucket, Key=key, Body=audio_bytes, ContentType="audio/mpeg")
        return f"https://{bucket}.s3.eu-north-1.amazonaws.com/{key}"

    except Exception as e:
        print(f"Audio generation error: {e}")
        return None


def _build_user_context(user: models.User, db: Session) -> dict:
    latest = db.query(models.Report).filter(
        models.Report.user_id == user.id
    ).order_by(models.Report.created_at.desc()).first()

    from datetime import date
    last_log = db.query(models.StreakLog).filter(
        models.StreakLog.user_id == user.id
    ).order_by(models.StreakLog.activity_date.desc()).first()

    days_inactive = 0
    if last_log:
        last_date = date.fromisoformat(last_log.activity_date)
        days_inactive = (date.today() - last_date).days

    profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == user.id
    ).first()

    goal = "improving speaking confidence"
    if profile and profile.goals:
        try:
            goals = json.loads(profile.goals)
            if goals:
                goal = goals[0]
        except:
            goal = str(profile.goals)[:50]

    return {
        "name": user.name,
        "goal": goal,
        "days_inactive": days_inactive,
    }


def _generate_secure_token(user_id: int) -> str:
    try:
        import jwt as pyjwt
        from datetime import datetime, timedelta
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=7),
        }
        return pyjwt.encode(payload, os.getenv("SECRET_KEY", "secret"), algorithm="HS256")
    except:
        return str(user_id)


def send_daily_coach_email(user: models.User, db: Session) -> bool:
    """Single daily coaching email — premium, personal, clean."""
    pref = db.query(models.EmailPreference).filter(
        models.EmailPreference.user_id == user.id
    ).first()
    if pref and not pref.assessment_complete:
        return False

    latest = db.query(models.Report).filter(
        models.Report.user_id == user.id
    ).order_by(models.Report.created_at.desc()).first()
    if not latest:
        return False

    ctx = _build_user_context(user, db)
    session_memory = _get_session_memory(user.id, db)
    focus = _get_today_focus(user.id, db)

    # Generate content with memory
    content_data = _generate_daily_content(ctx, focus, session_memory)
    sentence = content_data.get("sentence", "There is one point I would like you to remember.")

    # AI generated subject line
    subject = _generate_ai_subject(ctx, session_memory, focus)

    # Generate audio
    audio_url = _generate_audio_url(sentence, user.id)

    # Deep links
    token = _generate_secure_token(user.id)
    frontend_url = os.getenv("FRONTEND_URL", "https://voicecontrol.tech")
    coach_url = f"{frontend_url}/coach?mode=practice&token={token}&focus={focus}"
    listen_url = audio_url or f"{frontend_url}/coach?mode=listen&token={token}&focus={focus}"

    first_name = user.name.split()[0]

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#F9F8F6;font-family:'Georgia',serif;">
<div style="max-width:560px;margin:0 auto;padding:20px 16px;">

  <div style="padding:40px 0 32px;text-align:left;">
    <p style="font-size:11px;letter-spacing:0.22em;text-transform:uppercase;color:#9A9890;font-weight:600;margin:0 0 32px;font-family:'Inter',Arial,sans-serif;">VOICE CONTROL AI</p>
    <p style="font-size:28px;color:#1A1A1B;line-height:1.4;margin:0 0 16px;font-weight:400;">Hi {first_name},</p>
    <p style="font-size:17px;color:#4A4840;line-height:1.75;margin:0;font-weight:400;">{content_data.get("opening", "")}</p>
  </div>

  <div style="height:1px;background:#E8E4DC;margin:0 0 40px;"></div>

  <p style="font-size:10px;letter-spacing:0.22em;text-transform:uppercase;color:#9A9890;font-weight:600;margin:0 0 20px;font-family:'Inter',Arial,sans-serif;">YOUR SENTENCE TO PRACTICE FOR TODAY</p>

  <div style="padding:0 0 40px;">
    <p style="font-size:26px;color:#1A1A1B;line-height:1.45;margin:0;font-weight:400;font-style:italic;">&ldquo;{sentence}&rdquo;</p>
  </div>

  <div style="height:1px;background:#E8E4DC;margin:0 0 40px;"></div>

  <div style="margin-bottom:36px;">
    <p style="font-size:13px;letter-spacing:0.1em;color:#1A1A1B;font-weight:700;margin:0 0 8px;font-family:'Inter',Arial,sans-serif;">🎧 LISTEN</p>
    <p style="font-size:15px;color:#6A6860;line-height:1.65;margin:0 0 16px;font-weight:400;">{content_data.get("listen_instruction", "")}</p>
    <a href="{listen_url}" style="display:inline-block;border:1.5px solid #1A1A1B;color:#1A1A1B;padding:10px 24px;border-radius:30px;font-size:12px;font-weight:700;letter-spacing:0.1em;text-decoration:none;font-family:'Inter',Arial,sans-serif;">LISTEN</a>
  </div>

  <div style="margin-bottom:36px;">
    <p style="font-size:13px;letter-spacing:0.1em;color:#1A1A1B;font-weight:700;margin:0 0 8px;font-family:'Inter',Arial,sans-serif;">🗣️ SHADOW</p>
    <p style="font-size:15px;color:#6A6860;line-height:1.65;margin:0;font-weight:400;">{content_data.get("shadow_instruction", "")}</p>
  </div>

  <div style="margin-bottom:48px;">
    <p style="font-size:13px;letter-spacing:0.1em;color:#1A1A1B;font-weight:700;margin:0 0 8px;font-family:'Inter',Arial,sans-serif;">🎙️ SPEAK</p>
    <p style="font-size:15px;color:#6A6860;line-height:1.65;margin:0;font-weight:400;">{content_data.get("speak_instruction", "")}</p>
  </div>

  <div style="margin-bottom:48px;">
    <a href="{coach_url}" style="display:block;background:#1A1A1B;color:#FFFFFF;padding:18px 32px;border-radius:6px;font-size:13px;font-weight:700;letter-spacing:0.12em;text-decoration:none;text-align:center;font-family:'Inter',Arial,sans-serif;">PRACTISE WITH YOUR VOICE CONTROL AI COACH &rarr;</a>
  </div>

  <div style="height:1px;background:#E8E4DC;margin:0 0 36px;"></div>

  <div style="padding-bottom:48px;">
    <p style="font-size:16px;color:#4A4840;line-height:1.7;margin:0 0 28px;font-weight:400;">{content_data.get("closing", "Take this into one real conversation today.")}</p>
    <p style="font-size:15px;color:#9A9890;line-height:1.6;margin:0 0 6px;font-weight:400;">{content_data.get("sign_off", "See you tomorrow.")}</p>
    <p style="font-size:15px;color:#1A1A1B;font-weight:600;margin:0;font-family:'Inter',Arial,sans-serif;">Rina</p>
    <p style="font-size:13px;color:#9A9890;margin:4px 0 0;font-family:'Inter',Arial,sans-serif;">Your Voice Control AI Coach</p>
  </div>

  <div style="border-top:1px solid #E8E4DC;padding-top:24px;text-align:center;">
    <p style="font-size:11px;color:#BBBAB6;margin:0 0 6px;font-family:'Inter',Arial,sans-serif;">
      Voice Control AI &nbsp;·&nbsp;
      <a href="{frontend_url}/dashboard" style="color:#BBBAB6;text-decoration:none;">Dashboard</a>
      &nbsp;·&nbsp;
      <a href="{frontend_url}/settings" style="color:#BBBAB6;text-decoration:none;">Email Settings</a>
    </p>
    <p style="font-size:11px;color:#BBBAB6;margin:0;font-family:'Inter',Arial,sans-serif;">
      <a href="{frontend_url}/settings?unsubscribe=1" style="color:#BBBAB6;text-decoration:underline;">Unsubscribe</a>
    </p>
  </div>

</div>
</body>
</html>"""

    try:
        response = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": user.email,
            "subject": subject,
            "html": html,
        })
        db.add(models.EmailLog(
            user_id=user.id,
            email_type="daily_coach",
            email_subject=subject,
            status="sent",
            resend_id=response.get("id", "")
        ))
        db.commit()
        return True
    except Exception as e:
        db.add(models.EmailLog(
            user_id=user.id,
            email_type="daily_coach",
            email_subject=subject,
            status="failed"
        ))
        db.commit()
        print(f"Daily coach email error: {e}")
        return False