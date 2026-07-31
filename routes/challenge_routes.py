from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models
import json
from datetime import date, datetime, timedelta

router = APIRouter(prefix="/challenges", tags=["challenges"])

XP_REWARDS = {
    "challenge":   20,
    "exercise":    15,
    "assessment":  25,
    "beat_score":  10,
    "three_days":  30,
}

LEVELS = [
    (1,   "Speaker",              0),
    (2,   "Clear Speaker",        100),
    (3,   "Confident Speaker",    250),
    (4,   "Professional Speaker", 500),
    (5,   "Authoritative Speaker",850),
    (6,   "Executive Voice",      1300),
]


def get_level(xp: int) -> dict:
    current_level = LEVELS[0]
    next_level = LEVELS[1] if len(LEVELS) > 1 else None
    for i, (lvl, name, req) in enumerate(LEVELS):
        if xp >= req:
            current_level = (lvl, name, req)
            next_level = LEVELS[i+1] if i+1 < len(LEVELS) else None
    return {
        "level":      current_level[0],
        "name":       current_level[1],
        "xp":         xp,
        "next_level": next_level[1] if next_level else None,
        "next_xp":    next_level[2] if next_level else current_level[2],
        "progress":   min(100, round(((xp - current_level[2]) / max(1, (next_level[2] - current_level[2]))) * 100)) if next_level else 100,
    }


def get_today_str():
    return date.today().isoformat()


def get_week_dates():
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return [(monday + timedelta(days=i)).isoformat() for i in range(7)]


@router.get("/today")
def get_today_challenge(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    today = get_today_str()

    # Get challenge for today — rotate by day of year
    day_of_year = date.today().timetuple().tm_yday
    all_challenges = db.query(models.DailyChallenge).all()
    if not all_challenges:
        raise HTTPException(status_code=404, detail="No challenges found")

    challenge = all_challenges[(day_of_year - 1) % len(all_challenges)]

    # Check if user already completed today
    user_challenge = db.query(models.UserDailyChallenge).filter(
        models.UserDailyChallenge.user_id == current_user.id,
        models.UserDailyChallenge.challenge_id == challenge.id,
    ).first()

    # Check if completed today specifically
    completed_today = False
    if user_challenge and user_challenge.completed_at:
        completed_today = user_challenge.completed_at.date().isoformat() == today

    return {
        "id":             challenge.id,
        "prompt":         challenge.prompt,
        "date":           today,
        "completed":      completed_today,
        "xp_reward":      XP_REWARDS["challenge"],
        "duration":       "30–60 seconds",
    }


@router.post("/complete/{challenge_id}")
def complete_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    today = get_today_str()

    challenge = db.query(models.DailyChallenge).filter(
        models.DailyChallenge.id == challenge_id
    ).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Check already completed today
    existing = db.query(models.UserDailyChallenge).filter(
        models.UserDailyChallenge.user_id == current_user.id,
        models.UserDailyChallenge.challenge_id == challenge_id,
    ).first()

    if existing and existing.completed_at and existing.completed_at.date().isoformat() == today:
        return {"message": "Already completed today", "xp_earned": 0}

    # Save completion
    if existing:
        existing.completed = 1
        existing.completed_at = datetime.utcnow()
    else:
        udc = models.UserDailyChallenge(
            user_id=current_user.id,
            challenge_id=challenge_id,
            completed=1,
            completed_at=datetime.utcnow()
        )
        db.add(udc)

    # Log streak
    streak_log = db.query(models.StreakLog).filter(
        models.StreakLog.user_id == current_user.id,
        models.StreakLog.activity_date == today,
        models.StreakLog.activity_type == "challenge"
    ).first()
    if not streak_log:
        db.add(models.StreakLog(
            user_id=current_user.id,
            activity_date=today,
            activity_type="challenge"
        ))

    # Award XP
    xp_earned = award_xp(current_user.id, XP_REWARDS["challenge"], db)

    db.commit()
    return {"message": "Challenge completed", "xp_earned": xp_earned}


def award_xp(user_id: int, amount: int, db: Session) -> int:
    user_xp = db.query(models.UserXP).filter(
        models.UserXP.user_id == user_id
    ).first()

    if user_xp:
        user_xp.total_xp += amount
        new_xp = user_xp.total_xp
    else:
        new_xp = amount
        user_xp = models.UserXP(user_id=user_id, total_xp=amount)
        db.add(user_xp)

    level_info = get_level(new_xp)
    user_xp.current_level = level_info["level"]
    db.commit()
    return amount


@router.get("/streak")
def get_streak(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    today = date.today()
    week_dates = get_week_dates()

    # Get all streak logs for this user
    logs = db.query(models.StreakLog).filter(
        models.StreakLog.user_id == current_user.id
    ).all()

    activity_dates = list({log.activity_date for log in logs})

    # Calculate current streak
    streak = 0
    check = today
    while check.isoformat() in activity_dates:
        streak += 1
        check -= timedelta(days=1)

    # If today not done but yesterday was — still count
    if today.isoformat() not in activity_dates:
        check = today - timedelta(days=1)
        while check.isoformat() in activity_dates:
            streak += 1
            check -= timedelta(days=1)

    # Weekly calendar
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekly_calendar = [
        {
            "day":       day_names[i],
            "date":      week_dates[i],
            "completed": week_dates[i] in activity_dates,
            "is_today":  week_dates[i] == today.isoformat(),
        }
        for i in range(7)
    ]

    return {
        "current_streak":  streak,
        "weekly_calendar": weekly_calendar,
        "total_days":      len(activity_dates),
    }


@router.get("/xp")
def get_xp(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user_xp = db.query(models.UserXP).filter(
        models.UserXP.user_id == current_user.id
    ).first()

    xp = user_xp.total_xp if user_xp else 0
    return get_level(xp)