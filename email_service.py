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

# ═══ GRAPHIC GENERATOR — S3 hosted ═══

def _generate_graphic_b64(
    authority_score=87,
    center_label="AUTHORITY",
    label_top="Clarity",
    label_bottom="Resonance",
    coaching_title="Real-time Coaching",
    coaching_sub="★ Optimal steady flow",
    pace_label="Pace",
    score_left_label="Authority",
    score_left_val="87/100",
    score_right_label="Confidence",
    score_right_val="80/100",
    score_confidence="80/100",
    score_presence="75/100",
    score_leadership="72/100",
    prev_score=None,
    email_type="afternoon"
) -> str:
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        import numpy as np
        import io, base64, boto3, uuid

        fig = plt.figure(figsize=(7.5, 3.5), facecolor='#FDFCF8')
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_facecolor('#FDFCF8')
        ax.set_xlim(0, 7.5)
        ax.set_ylim(0, 3.5)
        ax.axis('off')

        cx, cy, r = 1.9, 1.75, 1.38

        if email_type == "evening" and prev_score is not None:
            theta_prev = np.linspace(np.radians(-225 + 270*(prev_score/100)), np.radians(-225), 300)
            ax.plot(cx + r*np.cos(theta_prev), cy + r*np.sin(theta_prev), color='#DEDAD2', linewidth=4, solid_capstyle='round')

        theta = np.linspace(np.radians(-225 + 270*(authority_score/100)), np.radians(-225), 300)
        ax.plot(cx + r*np.cos(theta), cy + r*np.sin(theta), color='#1A1A1B', linewidth=5, solid_capstyle='round')

        ax.add_patch(plt.Circle((cx, cy), 0.46, color='#F5F3EF', zorder=3))
        ax.add_patch(plt.Circle((cx, cy), 0.46, fill=False, edgecolor='#DEDAD2', linewidth=1.2, zorder=4))
        ax.text(cx, cy+0.22, center_label, ha='center', va='center', fontsize=6, color='#9A9890', zorder=5)
        ax.text(cx, cy-0.08, str(authority_score), ha='center', va='center', fontsize=28, color='#1A1A1B', zorder=5)
        ax.text(cx, cy+r+0.18, label_top, ha='center', fontsize=9, color='#4A4840')
        # bottom label removed

        ax.add_patch(patches.FancyBboxPatch((3.4, 2.62), 3.8, 0.62, boxstyle="round,pad=0.08", facecolor='#F0EDE6', edgecolor='none'))
        ax.text(3.58, 2.98, coaching_title, fontsize=8, color='#4A4840', fontweight='semibold')
        ax.text(3.58, 2.74, coaching_sub, fontsize=8, color='#8A7A60')
        ax.text(3.4, 2.28, pace_label, fontsize=9, color='#4A4840')

        wx = np.linspace(3.4, 7.2, 80)
        wy1 = 1.82 + 0.12*np.sin(wx*3.8) + 0.05*np.sin(wx*7.5)
        wy2 = 1.75 + 0.14*np.sin(wx*3.8+0.5) + 0.06*np.sin(wx*7.5+0.4)
        ax.plot(wx, wy1, color='#DEDAD2', linewidth=1.8, solid_capstyle='round')
        ax.plot(wx, wy2, color='#1A1A1B', linewidth=2.5, solid_capstyle='round')
        ax.plot(wx[45], wy2[45], 'o', color='#1A1A1B', markersize=6, zorder=5)

        ax.text(3.4, 1.55, "Authority", fontsize=7.5, color='#9A9890')
        ax.text(3.4, 1.36, score_left_val, fontsize=9, color='#1A1A1B', fontweight='semibold')
        ax.text(4.85, 1.55, "Confidence", fontsize=7.5, color='#9A9890')
        ax.text(4.85, 1.36, score_confidence, fontsize=9, color='#1A1A1B', fontweight='semibold')
        ax.text(3.4, 1.00, "Presence", fontsize=7.5, color='#9A9890')
        ax.text(3.4, 0.81, score_presence, fontsize=9, color='#1A1A1B', fontweight='semibold')
        ax.text(4.85, 1.00, "Leadership", fontsize=7.5, color='#9A9890')
        ax.text(4.85, 0.81, score_leadership, fontsize=9, color='#1A1A1B', fontweight='semibold')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#FDFCF8')
        buf.seek(0)
        img_bytes = buf.read()
        plt.close()

        # Upload to S3
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        bucket = os.getenv("AWS_BUCKET_NAME")
        key = f"email-graphics/{uuid.uuid4()}.png"
        s3.put_object(Bucket=bucket, Key=key, Body=img_bytes, ContentType='image/png', ACL='public-read')
        url = f"https://{bucket}.s3.{os.getenv('AWS_REGION', 'us-east-1')}.amazonaws.com/{key}"
        return url

    except Exception as e:
        print(f"Graphic generation error: {e}")
        return None


def _graphic_img_tag(url: str) -> str:
    if not url:
        return ""
    return f'<img src="{url}" alt="Voice Score Graphic" style="width:100%;max-width:520px;display:block;margin:0 auto;" width="520"/>'


def _get_weakest(latest_report) -> tuple:
    scores = {
        "pause_control":  latest_report.pause_score  or 0,
        "strong_endings": latest_report.ending_score or 0,
        "pitch_movement": latest_report.pitch_score  or 0,
        "pace_control":   latest_report.pace_score   or 0,
    }
    weakest_key = min(scores, key=scores.get)
    labels = {
        "pause_control":  "Pause Control",
        "strong_endings": "Strong Endings",
        "pitch_movement": "Pitch Movement",
        "pace_control":   "Pace Control",
    }
    scripts = {
        "pause_control":  "The most important thing [PAUSE] about clear communication [DOWN] is not what you say — but how deliberately you say it.",
        "strong_endings": "I am confident in this decision [DOWN]. The plan is clear [DOWN]. We move forward today [DOWN].",
        "pitch_movement": "This idea WILL work. The results SPEAK for themselves. Let me show you WHY.",
        "pace_control":   "Take your time. Speak clearly. Make every word count. Pause between your thoughts.",
    }
    return weakest_key, round(scores[weakest_key]), labels[weakest_key], scripts.get(weakest_key, "")


def send_morning_email(user: models.User, db: Session):
    pref = db.query(models.EmailPreference).filter(models.EmailPreference.user_id == user.id).first()
    if pref and not pref.assessment_complete:
        return False
    latest_report = db.query(models.Report).filter(models.Report.user_id == user.id).order_by(models.Report.created_at.desc()).first()
    if not latest_report:
        return False

    weakest_key, weakest_score, weakest_label, script = _get_weakest(latest_report)
    authority = round(latest_report.authority_score)
    pace = round(latest_report.pace_score or 0)
    frontend_url = os.getenv("FRONTEND_URL", "https://voicecontrol.tech")

    img_url = _generate_graphic_b64(
        authority_score=weakest_score, center_label=weakest_label.upper()[:9],
        label_top="Today's Focus", label_bottom="Weakest Area",
        coaching_title="Morning Blueprint", coaching_sub=f"★ {weakest_label} drill",
        pace_label="Speaking Rate",
        score_left_val=f"{authority}/100",
        score_confidence=f"{confidence}/100",
        score_presence=f"{presence}/100",
        score_leadership=f"{leadership}/100",
        email_type="morning",
    )

    script_html = script.replace("[PAUSE]",
        '<span style="border-bottom:1.5px solid #1A1A1B;padding:0 5px;font-size:11px;font-weight:600;">PAUSE</span>'
    ).replace("[DOWN]", '<span style="font-weight:700;"> ↓ </span>')

    subject = f"Voice Control AI — Morning Blueprint · {weakest_label}"
    html = f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#FDFCF8;font-family:'Inter',Arial,sans-serif;">
<div style="max-width:560px;margin:0 auto;background:#FDFCF8;">
  <div style="padding:22px 28px 18px;border-bottom:0.5px solid #ECEAE4;">
    <div style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#8A7A60;font-weight:600;margin-bottom:5px;">Voice Control AI · Morning Blueprint</div>
    <div style="font-size:20px;color:#1A1A1B;font-weight:500;">Good morning, {user.name.split()[0]}.</div>
    <div style="font-size:13px;color:#9A9890;margin-top:3px;">Your strategy script for today is ready.</div>
  </div>
  <div style="padding:24px 20px 16px;">{_graphic_img_tag(img_url)}</div>
  <div style="padding:0 28px 28px;">
    <div style="border:0.5px solid #ECEAE4;border-radius:12px;padding:16px 18px;margin-bottom:16px;background:#fff;">
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:#8A7A60;font-weight:600;margin-bottom:10px;">Today's Script · {weakest_label}</div>
      <div style="font-size:15px;color:#1A1A1B;font-family:Georgia,serif;line-height:1.9;margin-bottom:10px;">{script_html}</div>
      <div style="font-size:12px;color:#9A9890;">⏱ 2 min &nbsp;·&nbsp; {weakest_label} &nbsp;·&nbsp; Beginner</div>
    </div>
    <div style="text-align:center;"><a href="{frontend_url}/record" style="display:inline-block;background:#1A1A1B;color:#fff;padding:12px 32px;border-radius:30px;font-size:13px;font-weight:500;text-decoration:none;">Open Today's Blueprint</a></div>
    <p style="text-align:center;font-size:12px;color:#BBBAB6;margin-top:20px;">Voice Control AI &nbsp;·&nbsp; <a href="{frontend_url}/settings" style="color:#BBBAB6;">Email Settings</a></p>
  </div>
</div></body></html>"""

    try:
        response = resend.Emails.send({"from": FROM_EMAIL, "to": user.email, "subject": subject, "html": html})
        db.add(models.EmailLog(user_id=user.id, email_type="morning_blueprint", email_subject=subject, status="sent", resend_id=response.get("id", "")))
        db.commit()
        return True
    except Exception as e:
        db.add(models.EmailLog(user_id=user.id, email_type="morning_blueprint", email_subject=subject, status="failed"))
        db.commit()
        print(f"Morning email error: {e}")
        return False


def send_afternoon_email(user: models.User, db: Session):
    pref = db.query(models.EmailPreference).filter(models.EmailPreference.user_id == user.id).first()
    if pref and not pref.assessment_complete:
        return False
    latest_report = db.query(models.Report).filter(models.Report.user_id == user.id).order_by(models.Report.created_at.desc()).first()
    if not latest_report:
        return False

    weakest_key, weakest_score, weakest_label, _ = _get_weakest(latest_report)
    authority = round(latest_report.authority_score)
    pause = round(latest_report.pause_score or 0)
    endings = round(latest_report.ending_score or 0)
    frontend_url = os.getenv("FRONTEND_URL", "https://voicecontrol.tech")
    exercises_url = f"{frontend_url}/exercises?category={weakest_key}"

    exercise = db.query(models.Exercise).filter(models.Exercise.category == weakest_key).first()
    exercise_title = exercise.title if exercise else f"{weakest_label} Exercise"
    exercise_desc = (exercise.instruction[:120] + "...") if exercise and len(exercise.instruction) > 120 else (exercise.instruction if exercise else "")

    img_url = _generate_graphic_b64(
        authority_score=authority, center_label="AUTHORITY",
        label_top="Clarity", label_bottom="Resonance",
        coaching_title="Real-time Coaching", coaching_sub="★ Optimal steady flow",
        pace_label="Pace",
        score_left_val=f"{authority}/100",
        score_confidence=f"{confidence}/100",
        score_presence=f"{presence}/100",
        score_leadership=f"{leadership}/100",
        email_type="afternoon",
    )

    subject = f"Voice Control AI — Score Report · Authority {authority}/100"
    html = f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#FDFCF8;font-family:'Inter',Arial,sans-serif;">
<div style="max-width:560px;margin:0 auto;background:#FDFCF8;">
  <div style="padding:22px 28px 18px;border-bottom:0.5px solid #ECEAE4;">
    <div style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#8A7A60;font-weight:600;margin-bottom:5px;">Voice Control AI · Score Report</div>
    <div style="font-size:20px;color:#1A1A1B;font-weight:500;">Your voice report, {user.name.split()[0]}.</div>
    <div style="font-size:13px;color:#9A9890;margin-top:3px;">Based on your latest recording.</div>
  </div>
  <div style="padding:24px 20px 16px;">{_graphic_img_tag(img_url)}</div>
  <div style="padding:0 28px 28px;">
    <div style="border:0.5px solid #ECEAE4;border-radius:12px;padding:16px 18px;margin-bottom:16px;background:#fff;">
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:#8A7A60;font-weight:600;margin-bottom:6px;">AI Voice Coach · {weakest_label}</div>
      <div style="font-size:14px;color:#1A1A1B;font-weight:500;margin-bottom:4px;">{exercise_title}</div>
      <div style="font-size:13px;color:#6A6860;line-height:1.6;">{exercise_desc} Your {weakest_label} score is {weakest_score}/100 — this is your biggest area to fix today.</div>
    </div>
    <div style="text-align:center;"><a href="{exercises_url}" style="display:inline-block;background:#1A1A1B;color:#fff;padding:12px 32px;border-radius:30px;font-size:13px;font-weight:500;text-decoration:none;">Practice Today's Exercise</a></div>
    <p style="text-align:center;font-size:12px;color:#BBBAB6;margin-top:20px;">Voice Control AI &nbsp;·&nbsp; <a href="{frontend_url}/settings" style="color:#BBBAB6;">Email Settings</a></p>
  </div>
</div></body></html>"""

    try:
        response = resend.Emails.send({"from": FROM_EMAIL, "to": user.email, "subject": subject, "html": html})
        db.add(models.EmailLog(user_id=user.id, email_type="afternoon_report", email_subject=subject, status="sent", resend_id=response.get("id", "")))
        db.commit()
        return True
    except Exception as e:
        db.add(models.EmailLog(user_id=user.id, email_type="afternoon_report", email_subject=subject, status="failed"))
        db.commit()
        print(f"Afternoon email error: {e}")
        return False


def send_evening_email(user: models.User, db: Session):
    pref = db.query(models.EmailPreference).filter(models.EmailPreference.user_id == user.id).first()
    if pref and not pref.assessment_complete:
        return False
    reports = db.query(models.Report).filter(models.Report.user_id == user.id).order_by(models.Report.created_at.desc()).all()
    if not reports:
        return False

    latest = reports[0]
    prev = reports[1] if len(reports) > 1 else None
    authority_now = round(latest.authority_score)
    authority_prev = round(prev.authority_score) if prev else max(0, authority_now - 5)
    improvement = authority_now - authority_prev
    improvement_text = f"+{improvement}" if improvement >= 0 else str(improvement)
    pause_now = round(latest.pause_score or 0)
    pause_prev = round(prev.pause_score or 0) if prev else max(0, pause_now - 8)
    weakest_key, weakest_score, weakest_label, _ = _get_weakest(latest)
    frontend_url = os.getenv("FRONTEND_URL", "https://voicecontrol.tech")

    img_url = _generate_graphic_b64(
        authority_score=authority_now, center_label="TODAY",
        label_top="Improvement", label_bottom="Progress",
        coaching_title="Daily Progress Review",
        coaching_sub=f"★ {'Strong improvement' if improvement > 0 else 'Keep going'} today",
        pace_label="Pace",
        score_left_val=f"{authority_prev} → {authority_now}",
        score_confidence=f"{confidence_prev} → {confidence_now}",
        score_presence=f"{presence_prev} → {presence_now}",
        score_leadership=f"{leadership_prev} → {leadership_now}",
        email_type="evening", prev_score=authority_prev,
    )

    subject = f"Voice Control AI — Evening Review · {improvement_text} points today"
    html = f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#FDFCF8;font-family:'Inter',Arial,sans-serif;">
<div style="max-width:560px;margin:0 auto;background:#FDFCF8;">
  <div style="padding:22px 28px 18px;border-bottom:0.5px solid #ECEAE4;">
    <div style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#8A7A60;font-weight:600;margin-bottom:5px;">Voice Control AI · Evening Review</div>
    <div style="font-size:20px;color:#1A1A1B;font-weight:500;">See how far you came today, {user.name.split()[0]}.</div>
    <div style="font-size:13px;color:#9A9890;margin-top:3px;">Your progress compared to your previous recording.</div>
  </div>
  <div style="padding:24px 20px 16px;">{_graphic_img_tag(img_url)}</div>
  <div style="padding:0 28px 28px;">
    <div style="border-left:1.5px solid #1A1A1B;padding:10px 14px;margin-bottom:16px;font-size:13px;color:#4A4840;line-height:1.6;background:#fff;border-radius:0 8px 8px 0;">
      <strong>AI Voice Coach:</strong> {"Your Authority Score improved by " + str(improvement) + " points today. " if improvement > 0 else "Keep practicing — consistency is key. "}Tomorrow we shift focus to your {weakest_label} — target 80/100.
    </div>
    <div style="text-align:center;"><a href="{frontend_url}/record" style="display:inline-block;background:#1A1A1B;color:#fff;padding:12px 32px;border-radius:30px;font-size:13px;font-weight:500;text-decoration:none;">Record Tomorrow's Session</a></div>
    <p style="text-align:center;font-size:12px;color:#BBBAB6;margin-top:20px;">Voice Control AI &nbsp;·&nbsp; <a href="{frontend_url}/settings" style="color:#BBBAB6;">Email Settings</a></p>
  </div>
</div></body></html>"""

    try:
        response = resend.Emails.send({"from": FROM_EMAIL, "to": user.email, "subject": subject, "html": html})
        db.add(models.EmailLog(user_id=user.id, email_type="evening_review", email_subject=subject, status="sent", resend_id=response.get("id", "")))
        db.commit()
        return True
    except Exception as e:
        db.add(models.EmailLog(user_id=user.id, email_type="evening_review", email_subject=subject, status="failed"))
        db.commit()
        print(f"Evening email error: {e}")
        return False