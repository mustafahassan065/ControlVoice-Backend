from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models
import json
import os
import httpx

router = APIRouter(prefix="/live-coach", tags=["live-coach"])

TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")
TAVUS_REPLICA_ID = os.getenv("TAVUS_REPLICA_ID")
TAVUS_API_URL = "https://tavusapi.com/v2/conversations"


def build_user_context(user: models.User, db: Session) -> str:
    """Build full user context to pass to Tavus avatar"""

    # Latest report
    latest_report = db.query(models.Report).filter(
        models.Report.user_id == user.id
    ).order_by(models.Report.created_at.desc()).first()

    # All reports for history
    all_reports = db.query(models.Report).filter(
        models.Report.user_id == user.id
    ).order_by(models.Report.created_at.asc()).all()

    # XP and level
    user_xp = db.query(models.UserXP).filter(
        models.UserXP.user_id == user.id
    ).first()

    # Personal bests
    bests = db.query(models.PersonalBest).filter(
        models.PersonalBest.user_id == user.id
    ).all()

    # Streak
    logs = db.query(models.StreakLog).filter(
        models.StreakLog.user_id == user.id
    ).all()
    activity_dates = list({log.activity_date for log in logs})

    # Active program
    active_program = db.query(models.UserProgram).filter(
        models.UserProgram.user_id == user.id,
        models.UserProgram.status == "active"
    ).first()

    context = f"You are a professional AI voice coach on Voice Control AI platform. The user's name is {user.name}. "
    context += f"Address them by their first name: {user.name.split()[0]}. "
    context += "You have full access to their voice data and should give specific, personalized coaching. "
    context += "Never mention GPT, OpenAI, or any third-party tools. You are Voice Control AI Coach. "
    context += "Be encouraging, specific, and always end with one actionable exercise. "
    context += "\n\n=== USER VOICE DATA ===\n"

    if latest_report:
        feedback = json.loads(latest_report.feedback) if latest_report.feedback else {}
        acoustic = {}
        if latest_report.recording_id:
            rec = db.query(models.Recording).filter(
                models.Recording.id == latest_report.recording_id
            ).first()
            if rec and rec.acoustic_data:
                acoustic = json.loads(rec.acoustic_data)

        # Find weakest area
        scores = {
            "Pause Control":   round(latest_report.pause_score or 0),
            "Strong Endings":  round(latest_report.ending_score or 0),
            "Pitch Movement":  round(latest_report.pitch_score or 0),
            "Pace Control":    round(latest_report.pace_score or 0),
        }
        weakest = min(scores, key=scores.get)
        strongest = max(scores, key=scores.get)

        context += f"Latest Assessment Date: {latest_report.created_at.strftime('%B %d, %Y')}\n"
        context += f"Authority Score: {round(latest_report.authority_score)}/100\n"
        context += f"Confidence Score: {round(latest_report.confidence_score)}/100\n"
        context += f"Presence Score: {round(latest_report.presence_score)}/100\n"
        context += f"Leadership Score: {round(latest_report.leadership_score)}/100\n"
        context += f"\nDetailed Scores:\n"
        for name, score in scores.items():
            context += f"- {name}: {score}/100\n"
        context += f"\nBIGGEST WEAKNESS: {weakest} ({scores[weakest]}/100) — focus coaching here\n"
        context += f"STRONGEST AREA: {strongest} ({scores[strongest]}/100)\n"

        if feedback.get('weaknesses'):
            context += f"\nSpecific weaknesses identified: {', '.join(feedback['weaknesses'])}\n"
        if feedback.get('strengths'):
            context += f"Specific strengths: {', '.join(feedback['strengths'])}\n"
        if feedback.get('user_level'):
            context += f"Current level: {feedback['user_level']}\n"
        if feedback.get('target_score'):
            context += f"Target score: {feedback['target_score']}/100\n"

        if acoustic:
            context += f"\nAcoustic Analysis:\n"
            context += f"- Speaking rate: {acoustic.get('speaking_rate_wpm', 'N/A')} WPM (target: 130-160)\n"
            context += f"- Pace status: {acoustic.get('wpm_status', 'N/A')}\n"
            context += f"- Pause count: {acoustic.get('pause_count', 'N/A')} pauses\n"
            context += f"- Average pause duration: {acoustic.get('avg_pause_duration', 'N/A')} seconds\n"
            context += f"- Pitch range: {acoustic.get('pitch_range_hz', 'N/A')} Hz\n"
            context += f"- Pitch status: {acoustic.get('pitch_status', 'N/A')}\n"
            context += f"- Total filler words: {acoustic.get('total_fillers', 'N/A')}\n"
            context += f"- Filler percentage: {acoustic.get('filler_percent', 'N/A')}%\n"

    if len(all_reports) > 1:
        first = all_reports[0]
        latest = all_reports[-1]
        improvement = round(latest.authority_score - first.authority_score)
        context += f"\nProgress:\n"
        context += f"- Total recordings: {len(all_reports)}\n"
        context += f"- First authority score: {round(first.authority_score)}\n"
        context += f"- Current authority score: {round(latest.authority_score)}\n"
        context += f"- Overall improvement: {'+' if improvement >= 0 else ''}{improvement} points\n"

    if bests:
        context += f"\nPersonal Bests:\n"
        seen = set()
        for pb in bests:
            if pb.metric not in seen:
                context += f"- {pb.metric.title()}: {round(pb.new_best)}/100\n"
                seen.add(pb.metric)

    context += f"\nEngagement:\n"
    context += f"- Total practice days: {len(activity_dates)}\n"
    context += f"- XP earned: {user_xp.total_xp if user_xp else 0}\n"
    if active_program:
        program = db.query(models.Program).filter(
            models.Program.id == active_program.program_id
        ).first()
        if program:
            context += f"- Active program: {program.title} (Day {active_program.current_day})\n"

    context += "\n=== COACHING INSTRUCTIONS ===\n"
    context += f"1. Greet {user.name.split()[0]} warmly and mention their current Authority Score.\n"
    context += f"2. Immediately focus on their weakest area and explain why it matters.\n"
    context += f"3. Give one specific exercise they can practice right now.\n"
    context += "4. Be conversational — listen to what they say and respond naturally.\n"
    context += "5. If they ask about a specific score, explain it in simple terms.\n"
    context += "6. Always be encouraging — celebrate any improvement you see in their data.\n"

    return context


@router.post("/start")
async def start_live_coach_session(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not TAVUS_API_KEY:
        raise HTTPException(status_code=500, detail="Tavus API key not configured")
    if not TAVUS_REPLICA_ID:
        raise HTTPException(status_code=500, detail="Tavus Replica ID not configured")

    # Build full user context
    conversation_context = build_user_context(current_user, db)

    # Start Tavus conversation
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TAVUS_API_URL,
                headers={
                    "x-api-key": TAVUS_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "persona_id": TAVUS_REPLICA_ID,
                    "conversational_context": conversation_context,
                    "custom_greeting": f"Hi {current_user.name.split()[0]}! I've reviewed your voice data and I'm ready to help you improve. Your Authority Score is {_get_authority(current_user, db)}. Let's work on your biggest opportunity today.",
                    "properties": {
                        "max_call_duration": 1800,  # 30 minutes max
                        "participant_left_timeout": 60,
                        "enable_recording": False,
                        
                    }
                }
            )

        if response.status_code not in [200, 201]:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Tavus error: {response.text}"
            )

        data = response.json()
        conversation_url = data.get("conversation_url")

        if not conversation_url:
            raise HTTPException(status_code=500, detail="No conversation URL returned from Tavus")

        return {
            "conversation_url": conversation_url,
            "conversation_id": data.get("conversation_id"),
        }

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Tavus connection timed out. Please try again.")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")


def _get_authority(user: models.User, db: Session) -> str:
    latest = db.query(models.Report).filter(
        models.Report.user_id == user.id
    ).order_by(models.Report.created_at.desc()).first()
    if latest:
        return f"{round(latest.authority_score)}/100"
    return "not yet assessed"