from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database import get_db
from auth import get_current_user
import models
import json
from datetime import datetime

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

GOALS_LIST = [
    "Speak more confidently",
    "Sound more authoritative",
    "Improve my voice",
    "Improve articulation",
    "Stop rushing when I speak",
    "Improve public speaking",
    "Become more comfortable with audiences",
    "Handle criticism better",
    "Handle rejection better",
    "Stay composed during disagreement",
    "Improve presentations",
    "Speak more clearly",
    "Improve professional communication",
    "Speak better on camera",
]

SITUATIONS_LIST = [
    "Meetings",
    "Presentations",
    "Job interviews",
    "Speaking to groups",
    "Speaking to senior people",
    "Camera or video calls",
    "Being interrupted",
    "Being criticized",
    "Disagreement or conflict",
    "Rejection",
    "Difficult conversations",
    "Answering unexpected questions",
]

BASELINE_TASKS = [
    {
        "type":        "read_aloud",
        "title":       "Task 1 — Read Aloud",
        "instruction": "Read the following passage aloud clearly and at a natural pace.",
        "content":     "The ability to communicate clearly is one of the most valuable professional skills you can develop. When you speak with confidence and purpose, people listen. Your voice carries your ideas into the room. The way you pace your words, the pauses you choose, and the clarity of your delivery all affect how your message is received. Today, focus on speaking each word fully and ending each sentence with a controlled, downward tone.",
        "duration":    60,
        "prep_time":   0,
    },
    {
        "type":        "free_speaking",
        "title":       "Task 2 — Free Speaking",
        "instruction": "Speak for 60 seconds about something you know well. It can be your job, a skill, a hobby, or anything you are comfortable explaining.",
        "content":     None,
        "duration":    60,
        "prep_time":   0,
    },
    {
        "type":        "impromptu",
        "title":       "Task 3 — Impromptu Speaking",
        "instruction": "You have 15 seconds to prepare, then speak for 60 seconds on the topic below.",
        "content":     "Describe a decision you made that changed something important in your life.",
        "duration":    60,
        "prep_time":   15,
    },
    {
        "type":        "pressure",
        "title":       "Task 4 — Pressure Response",
        "instruction": "A colleague says the following to you. Respond calmly and clearly for 30 seconds.",
        "content":     "\"I don't think you've thought this through properly.\"",
        "duration":    30,
        "prep_time":   0,
    },
]


class ProfileData(BaseModel):
    goals: List[str]
    difficult_situations: List[str]
    sessions_per_day: int = 2


@router.get("/goals-list")
def get_goals_list():
    return {
        "goals":      GOALS_LIST,
        "situations": SITUATIONS_LIST,
    }


@router.post("/save-profile")
def save_profile(
    data: ProfileData,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == current_user.id
    ).first()

    if profile:
        profile.goals = json.dumps(data.goals)
        profile.difficult_situations = json.dumps(data.difficult_situations)
        profile.sessions_per_day = data.sessions_per_day
    else:
        profile = models.UserProfile(
            user_id=current_user.id,
            goals=json.dumps(data.goals),
            difficult_situations=json.dumps(data.difficult_situations),
            sessions_per_day=data.sessions_per_day,
        )
        db.add(profile)

    db.commit()
    return {"message": "Profile saved"}


@router.get("/baseline-tasks")
def get_baseline_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    completed = db.query(models.BaselineAssessment).filter(
        models.BaselineAssessment.user_id == current_user.id
    ).all()

    completed_types = {b.task_type for b in completed if b.completed == 1}

    tasks = []
    for task in BASELINE_TASKS:
        tasks.append({
            **task,
            "completed": task["type"] in completed_types,
        })

    return {
        "tasks":           tasks,
        "total":           len(BASELINE_TASKS),
        "completed_count": len(completed_types),
        "all_done":        len(completed_types) >= len(BASELINE_TASKS),
    }


@router.post("/complete-baseline-task")
def complete_baseline_task(
    task_type: str,
    recording_id: int = None,
    score: float = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    existing = db.query(models.BaselineAssessment).filter(
        models.BaselineAssessment.user_id == current_user.id,
        models.BaselineAssessment.task_type == task_type,
    ).first()

    if existing:
        existing.completed = 1
        existing.completed_at = datetime.utcnow()
        if recording_id: existing.recording_id = recording_id
        if score: existing.score = score
    else:
        db.add(models.BaselineAssessment(
            user_id=current_user.id,
            task_type=task_type,
            recording_id=recording_id,
            score=score,
            completed=1,
            completed_at=datetime.utcnow(),
        ))

    db.commit()

    # Award XP
    from routes.challenge_routes import award_xp
    award_xp(current_user.id, 25, db)

    # Check if all 4 done — mark onboarding complete
    completed_count = db.query(models.BaselineAssessment).filter(
        models.BaselineAssessment.user_id == current_user.id,
        models.BaselineAssessment.completed == 1,
    ).count()

    if completed_count >= 4:
        user = db.query(models.User).filter(models.User.id == current_user.id).first()
        user.onboarding_completed = 1
        db.commit()
        return {"message": "Task complete", "onboarding_complete": True}

    return {"message": "Task complete", "onboarding_complete": False}


@router.get("/status")
def get_onboarding_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return {
        "onboarding_completed": current_user.onboarding_completed == 1,
    }