from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from exercise_engine import get_recommended_exercises
from ai_feedback import generate_practice_sentences
import models
import json

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/recommended/{report_id}")
def get_recommended(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    report = db.query(models.Report).filter(
        models.Report.id == report_id,
        models.Report.user_id == current_user.id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    scores = {
        "pause_score":   report.pause_score,
        "ending_score":  report.ending_score,
        "pitch_score":   report.pitch_score,
        "pace_score":    report.pace_score,
    }

    exercises = get_recommended_exercises(scores, db)
    return {"exercises": exercises, "report_id": report_id}

@router.get("/all")
def get_all_exercises(
    category: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Exercise)
    if category:
        query = query.filter(models.Exercise.category == category)
    exercises = query.all()
    return [
        {
            "id":                ex.id,
            "category":          ex.category,
            "title":             ex.title,
            "instruction":       ex.instruction,
            "practice_template": ex.practice_template,
            "wrong_audio_url":   ex.wrong_audio_url,
            "correct_audio_url": ex.correct_audio_url,
        }
        for ex in exercises
    ]


@router.get("/practice-sentences/{exercise_id}")
async def get_practice_sentences(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    exercise = db.query(models.Exercise).filter(
        models.Exercise.id == exercise_id
    ).first()

    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    sentences = generate_practice_sentences(
        exercise.practice_template,
        exercise.category
    )

    return {"sentences": sentences, "template": exercise.practice_template}