from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models
import json

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/latest/{user_id}")
def get_latest_report(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Sirf apni report dekh sako
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    report = db.query(models.Report).filter(
        models.Report.user_id == user_id
    ).order_by(models.Report.created_at.desc()).first()

    if not report:
        raise HTTPException(status_code=404, detail="No reports found")

    return {
        "id":               report.id,
        "user_id":          report.user_id,
        "recording_id":     report.recording_id,
        "authority_score":  round(report.authority_score),
        "confidence_score": round(report.confidence_score),
        "presence_score":   round(report.presence_score),
        "leadership_score": round(report.leadership_score),
        "pace_score":       round(report.pace_score),
        "pause_score":      round(report.pause_score),
        "pitch_score":      round(report.pitch_score),
        "ending_score":     round(report.ending_score),
        "feedback":         json.loads(report.feedback) if report.feedback else {},
        "created_at":       report.created_at,
    }


@router.get("/{report_id}")
def get_report(
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

    return {
        "id":               report.id,
        "user_id":          report.user_id,
        "recording_id":     report.recording_id,
        "authority_score":  round(report.authority_score),
        "confidence_score": round(report.confidence_score),
        "presence_score":   round(report.presence_score),
        "leadership_score": round(report.leadership_score),
        "pace_score":       round(report.pace_score),
        "pause_score":      round(report.pause_score),
        "pitch_score":      round(report.pitch_score),
        "ending_score":     round(report.ending_score),
        "feedback":         json.loads(report.feedback) if report.feedback else {},
        "created_at":       report.created_at,
    }

@router.get("/comparison/{user_id}")
def get_before_after(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    reports = db.query(models.Report).filter(
        models.Report.user_id == user_id
    ).order_by(models.Report.created_at.asc()).all()

    if len(reports) < 2:
        return {"has_comparison": False}

    first = reports[0]
    latest = reports[-1]

    first_feedback  = json.loads(first.feedback)  if first.feedback  else {}
    latest_feedback = json.loads(latest.feedback) if latest.feedback else {}

    return {
        "has_comparison": True,
        "first": {
            "date":             first.created_at.strftime("%b %d, %Y"),
            "authority_score":  round(first.authority_score),
            "confidence_score": round(first.confidence_score),
            "presence_score":   round(first.presence_score),
            "leadership_score": round(first.leadership_score),
            "user_level":       first_feedback.get("user_level", "Beginner Speaker"),
        },
        "latest": {
            "date":             latest.created_at.strftime("%b %d, %Y"),
            "authority_score":  round(latest.authority_score),
            "confidence_score": round(latest.confidence_score),
            "presence_score":   round(latest.presence_score),
            "leadership_score": round(latest.leadership_score),
            "user_level":       latest_feedback.get("user_level", "Beginner Speaker"),
        },
        "improvements": {
            "authority":  round(latest.authority_score  - first.authority_score),
            "confidence": round(latest.confidence_score - first.confidence_score),
            "presence":   round(latest.presence_score   - first.presence_score),
            "leadership": round(latest.leadership_score - first.leadership_score),
        }
    }


@router.get("/personal-bests/{user_id}")
def get_personal_bests(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    bests = db.query(models.PersonalBest).filter(
        models.PersonalBest.user_id == user_id
    ).order_by(models.PersonalBest.achieved_at.desc()).all()

    result = {}
    for pb in bests:
        if pb.metric not in result:
            result[pb.metric] = {
                "metric":       pb.metric,
                "best_score":   round(pb.new_best),
                "achieved_at":  pb.achieved_at.strftime("%b %d, %Y"),
            }

    return list(result.values())