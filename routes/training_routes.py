from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models
import json
from datetime import date, datetime

router = APIRouter(prefix="/training", tags=["training"])

SESSION_FOCUS = {
    "morning":   {
        "title":       "Morning Voice Training",
        "focus":       "Voice Mechanics",
        "description": "Physical technique — warm up your voice for the day.",
        "categories":  ["pause_control", "pace_control"],
        "icon":        "🌅",
    },
    "afternoon": {
        "title":       "Speaking Challenge",
        "focus":       "Applied Speaking",
        "description": "Practice speaking clearly in real-world scenarios.",
        "categories":  ["strong_endings", "pitch_movement"],
        "icon":        "☀️",
    },
    "evening":   {
        "title":       "Confidence Training",
        "focus":       "Composure & Presence",
        "description": "Practice staying composed under pressure.",
        "categories":  ["pause_control", "strong_endings"],
        "icon":        "🌙",
    },
}


def get_today_session_exercise(session_type: str, user_id: int, db: Session):
    """Pick exercise for session — avoid repeating today's exercises"""
    focus = SESSION_FOCUS[session_type]
    categories = focus["categories"]

    # Already used exercise IDs today
    today = date.today().isoformat()
    used_today = db.query(models.TrainingSession).filter(
        models.TrainingSession.user_id == user_id,
        models.TrainingSession.session_date == today,
    ).all()
    used_ids = {s.exercise_id for s in used_today if s.exercise_id}

    # Try each category
    for category in categories:
        exercises = db.query(models.Exercise).filter(
            models.Exercise.category == category
        ).all()
        for ex in exercises:
            if ex.id not in used_ids:
                return ex

    # Fallback — any exercise
    return db.query(models.Exercise).first()


@router.get("/today")
def get_today_sessions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    today = date.today().isoformat()
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == current_user.id
    ).first()

    sessions_per_day = profile.sessions_per_day if profile else 2

    session_types = ["morning", "afternoon", "evening"]
    if sessions_per_day == 1:
        session_types = ["morning"]
    elif sessions_per_day == 2:
        session_types = ["morning", "afternoon"]

    result = []
    for stype in session_types:
        # Check if completed today
        existing = db.query(models.TrainingSession).filter(
            models.TrainingSession.user_id == current_user.id,
            models.TrainingSession.session_type == stype,
            models.TrainingSession.session_date == today,
        ).first()

        exercise = None
        if existing and existing.exercise_id:
            exercise = db.query(models.Exercise).filter(
                models.Exercise.id == existing.exercise_id
            ).first()
        else:
            exercise = get_today_session_exercise(stype, current_user.id, db)

        focus = SESSION_FOCUS[stype]

        session_data = {
            "session_type":  stype,
            "title":         focus["title"],
            "focus":         focus["focus"],
            "description":   focus["description"],
            "icon":          focus["icon"],
            "completed":     existing.completed == 1 if existing else False,
            "has_retry":     existing.retry_recording_id is not None if existing else False,
            "score_attempt1": existing.score_attempt1 if existing else None,
            "score_attempt2": existing.score_attempt2 if existing else None,
            "improvement":   existing.improvement if existing else None,
            "session_id":    existing.id if existing else None,
            "exercise": {
                "id":               exercise.id,
                "title":            exercise.title,
                "instruction":      exercise.instruction,
                "practice_template": exercise.practice_template,
                "category":         exercise.category,
            } if exercise else None,
        }
        result.append(session_data)

    return {"sessions": result, "date": today}


@router.post("/start-session")
def start_session(
    session_type: str,
    exercise_id: int,
    recording_id: int,
    score: float = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    today = date.today().isoformat()

    # Check already started
    existing = db.query(models.TrainingSession).filter(
        models.TrainingSession.user_id == current_user.id,
        models.TrainingSession.session_type == session_type,
        models.TrainingSession.session_date == today,
    ).first()

    if existing:
        existing.recording_id = recording_id
        existing.score_attempt1 = score
    else:
        existing = models.TrainingSession(
            user_id=current_user.id,
            session_type=session_type,
            session_date=today,
            exercise_id=exercise_id,
            recording_id=recording_id,
            score_attempt1=score,
        )
        db.add(existing)

    # Log streak
    streak_log = db.query(models.StreakLog).filter(
        models.StreakLog.user_id == current_user.id,
        models.StreakLog.activity_date == today,
        models.StreakLog.activity_type == "exercise"
    ).first()
    if not streak_log:
        db.add(models.StreakLog(
            user_id=current_user.id,
            activity_date=today,
            activity_type="exercise"
        ))

    # Award XP
    from routes.challenge_routes import award_xp
    award_xp(current_user.id, 15, db)

    db.commit()
    db.refresh(existing)
    return {"message": "Session started", "session_id": existing.id}


@router.post("/complete-retry")
def complete_retry(
    session_id: int,
    retry_recording_id: int,
    score_attempt2: float = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    session = db.query(models.TrainingSession).filter(
        models.TrainingSession.id == session_id,
        models.TrainingSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.retry_recording_id = retry_recording_id
    session.score_attempt2 = score_attempt2
    session.completed = 1

    if session.score_attempt1 and score_attempt2:
        session.improvement = round(score_attempt2 - session.score_attempt1, 1)

    # Award XP for improvement
    if session.improvement and session.improvement > 0:
        from routes.challenge_routes import award_xp
        award_xp(current_user.id, 10, db)

    db.commit()
    return {
        "message":     "Session complete",
        "improvement": session.improvement,
        "score1":      session.score_attempt1,
        "score2":      session.score_attempt2,
    }


@router.get("/history")
def get_training_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    sessions = db.query(models.TrainingSession).filter(
        models.TrainingSession.user_id == current_user.id,
    ).order_by(models.TrainingSession.created_at.desc()).limit(30).all()

    result = []
    for s in sessions:
        exercise = db.query(models.Exercise).filter(
            models.Exercise.id == s.exercise_id
        ).first() if s.exercise_id else None

        result.append({
            "id":            s.id,
            "session_type":  s.session_type,
            "session_date":  s.session_date,
            "exercise_title": exercise.title if exercise else None,
            "score_attempt1": s.score_attempt1,
            "score_attempt2": s.score_attempt2,
            "improvement":   s.improvement,
            "completed":     s.completed,
        })

    return result