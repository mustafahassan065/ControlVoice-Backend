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