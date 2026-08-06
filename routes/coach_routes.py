from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from auth import get_current_user
import models
import json
import os
from openai import OpenAI
from datetime import date

router = APIRouter(prefix="/coach", tags=["coach"])
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FREE_DAILY_LIMIT = 3

QUICK_PROMPTS = [
    "Why did I receive this score?",
    "Explain my pitch analysis.",
    "Explain my pauses.",
    "Compare me with last week.",
    "Recommend today's exercise.",
    "Help me prepare for an interview.",
    "Help me sound more confident.",
    "Analyze my biggest weakness.",
]


class ChatRequest(BaseModel):
    message: str
    session_id: str = None


def get_user_context(user_id: int, db: Session) -> str:
    """User ka full context build karo for AI"""

    # Latest report
    latest_report = db.query(models.Report).filter(
        models.Report.user_id == user_id
    ).order_by(models.Report.created_at.desc()).first()

    # All reports for history
    all_reports = db.query(models.Report).filter(
        models.Report.user_id == user_id
    ).order_by(models.Report.created_at.asc()).all()

    # Personal bests
    bests = db.query(models.PersonalBest).filter(
        models.PersonalBest.user_id == user_id
    ).order_by(models.PersonalBest.new_best.desc()).all()

    # Streak
    logs = db.query(models.StreakLog).filter(
        models.StreakLog.user_id == user_id
    ).all()
    activity_dates = list({log.activity_date for log in logs})
    streak = len([d for d in activity_dates if d >= str(date.today().replace(day=1))])

    # XP
    user_xp = db.query(models.UserXP).filter(
        models.UserXP.user_id == user_id
    ).first()

    # Active program
    active_program = db.query(models.UserProgram).filter(
        models.UserProgram.user_id == user_id,
        models.UserProgram.status == "active"
    ).first()

    context = "=== USER VOICE COACHING DATA ===\n\n"

    if latest_report:
        feedback = json.loads(latest_report.feedback) if latest_report.feedback else {}
        acoustic = json.loads(
            db.query(models.Recording).filter(
                models.Recording.id == latest_report.recording_id
            ).first().acoustic_data or "{}"
        ) if latest_report.recording_id else {}

        context += f"""LATEST ASSESSMENT ({latest_report.created_at.strftime('%B %d, %Y')}):
- Authority Score: {round(latest_report.authority_score)}/100
- Confidence Score: {round(latest_report.confidence_score)}/100
- Presence Score: {round(latest_report.presence_score)}/100
- Leadership Score: {round(latest_report.leadership_score)}/100
- Pace Score: {round(latest_report.pace_score)}/100
- Pause Score: {round(latest_report.pause_score)}/100
- Pitch Score: {round(latest_report.pitch_score)}/100
- Ending Score: {round(latest_report.ending_score)}/100
- User Level: {feedback.get('user_level', 'Unknown')}
- Target Score: {feedback.get('target_score', 80)}
- Main Weaknesses: {', '.join(feedback.get('weaknesses', []))}
- Strengths: {', '.join(feedback.get('strengths', []))}
"""
        if acoustic:
            context += f"""
ACOUSTIC DATA:
- Speaking Rate: {acoustic.get('speaking_rate_wpm', 'N/A')} WPM (target: 130-160)
- WPM Status: {acoustic.get('wpm_status', 'N/A')}
- Pause Count: {acoustic.get('pause_count', 'N/A')} pauses
- Average Pause Duration: {acoustic.get('avg_pause_duration', 'N/A')} seconds
- Pitch Range: {acoustic.get('pitch_range_hz', 'N/A')} Hz
- Pitch Status: {acoustic.get('pitch_status', 'N/A')}
- Total Filler Words: {acoustic.get('total_fillers', 'N/A')}
- Filler Percentage: {acoustic.get('filler_percent', 'N/A')}%
- Sentence Endings Status: {acoustic.get('ending_status', 'N/A')}
"""

    if len(all_reports) > 1:
        first = all_reports[0]
        latest = all_reports[-1]
        context += f"""
PROGRESS HISTORY:
- Total Recordings: {len(all_reports)}
- First Recording Authority Score: {round(first.authority_score)}
- Latest Authority Score: {round(latest.authority_score)}
- Overall Improvement: {round(latest.authority_score - first.authority_score)} points
"""

    if bests:
        context += "\nPERSONAL BESTS:\n"
        for pb in bests:
            context += f"- {pb.metric.title()}: {round(pb.new_best)} (achieved {pb.achieved_at.strftime('%B %d, %Y')})\n"

    context += f"""
ENGAGEMENT:
- Practice Days This Month: {streak}
- Total XP: {user_xp.total_xp if user_xp else 0}
- Active Program: {active_program.program_id if active_program else 'None'}
"""

    return context


@router.post("/ask")
def ask_coach(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    today = date.today().isoformat()
    plan = current_user.plan or "free"

    # Check daily limit for free users
    if plan == "free":
        question_log = db.query(models.CoachQuestion).filter(
            models.CoachQuestion.user_id == current_user.id,
            models.CoachQuestion.question_date == today
        ).first()

        if question_log and question_log.count >= FREE_DAILY_LIMIT:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "daily_limit_reached",
                    "message": f"Free plan allows {FREE_DAILY_LIMIT} coach questions per day. Upgrade to Pro for unlimited questions.",
                    "upgrade_url": "/pricing"
                }
            )

    # Get or create conversation
    conversation = db.query(models.CoachConversation).filter(
        models.CoachConversation.user_id == current_user.id
    ).order_by(models.CoachConversation.updated_at.desc()).first()

    if not conversation:
        conversation = models.CoachConversation(
            user_id=current_user.id,
            messages="[]"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Build conversation history
    messages_history = json.loads(conversation.messages)

    # User context
    user_context = get_user_context(current_user.id, db)

    # System prompt
    system_prompt = f"""You are Voice Control AI's personal voice coach. You give specific, personalized coaching advice based on the user's actual voice data.

IMPORTANT RULES:
- Always use the user's actual data when answering. Never give generic advice.
- Be encouraging but honest. Be specific with numbers.
- If the user asks about their score, reference their exact scores.
- Recommend specific exercises from these categories: pause_control, strong_endings, pitch_movement, pace_control.
- Keep responses concise — 3-5 sentences max unless a detailed explanation is needed.
- Never mention GPT, OpenAI, or any third-party tools. You are Voice Control AI Coach.
- Always end with one specific actionable next step.

{user_context}"""

    # Build messages for API
    api_messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history (last 10 messages)
    for msg in messages_history[-10:]:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current message
    api_messages.append({"role": "user", "content": request.message})

    # Call OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=api_messages,
            max_tokens=400,
            temperature=0.7,
        )
        assistant_reply = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

    # Save to conversation history
    messages_history.append({"role": "user",      "content": request.message})
    messages_history.append({"role": "assistant", "content": assistant_reply})

    # Keep only last 20 messages
    if len(messages_history) > 20:
        messages_history = messages_history[-20:]

    conversation.messages = json.dumps(messages_history)
    db.commit()

    # Log question count for free users
    if plan == "free":
        question_log = db.query(models.CoachQuestion).filter(
            models.CoachQuestion.user_id == current_user.id,
            models.CoachQuestion.question_date == today
        ).first()

        if question_log:
            question_log.count += 1
        else:
            db.add(models.CoachQuestion(
                user_id=current_user.id,
                question_date=today,
                count=1
            ))
        db.commit()

    # Get remaining questions for free users
    remaining = None
    if plan == "free":
        question_log = db.query(models.CoachQuestion).filter(
            models.CoachQuestion.user_id == current_user.id,
            models.CoachQuestion.question_date == today
        ).first()
        remaining = max(0, FREE_DAILY_LIMIT - (question_log.count if question_log else 0))

    return {
        "reply":     assistant_reply,
        "remaining": remaining,
        "plan":      plan,
    }


@router.get("/quick-prompts")
def get_quick_prompts():
    return {"prompts": QUICK_PROMPTS}


@router.delete("/reset")
def reset_conversation(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    conversation = db.query(models.CoachConversation).filter(
        models.CoachConversation.user_id == current_user.id
    ).first()
    if conversation:
        conversation.messages = "[]"
        db.commit()
    return {"message": "Conversation reset"}