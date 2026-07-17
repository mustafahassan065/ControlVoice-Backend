from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models
import json
from datetime import datetime, timedelta

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/chart/{user_id}")
def get_progress_chart(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Document ke mutabiq — progress_snapshots se chart data"""
    if current_user.id != user_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not authorized")

    snapshots = db.query(models.ProgressSnapshot).filter(
        models.ProgressSnapshot.user_id == user_id
    ).order_by(models.ProgressSnapshot.recording_date.asc()).all()

    chart_data = []
    for snap in snapshots:
        chart_data.append({
            "date":             snap.recording_date.strftime("%b %d"),
            "authority_score":  round(snap.authority_score or 0),
            "confidence_score": round(snap.confidence_score or 0),
            "presence_score":   round(snap.presence_score or 0),
            "leadership_score": round(snap.leadership_score or 0),
        })

    return {"chart_data": chart_data}


@router.get("/{user_id}")
def get_progress(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # All reports
    reports = db.query(models.Report).filter(
        models.Report.user_id == current_user.id
    ).order_by(models.Report.created_at.asc()).all()

    # All recordings
    recordings = db.query(models.Recording).filter(
        models.Recording.user_id == current_user.id
    ).order_by(models.Recording.created_at.asc()).all()

    # Snapshots for chart (document ke mutabiq)
    snapshots = db.query(models.ProgressSnapshot).filter(
        models.ProgressSnapshot.user_id == current_user.id
    ).order_by(models.ProgressSnapshot.recording_date.asc()).all()

    chart_data = []
    for snap in snapshots:
        chart_data.append({
            "date":             snap.recording_date.strftime("%b %d"),
            "authority_score":  round(snap.authority_score or 0),
            "confidence_score": round(snap.confidence_score or 0),
            "presence_score":   round(snap.presence_score or 0),
            "leadership_score": round(snap.leadership_score or 0),
        })

    latest_report = reports[-1] if reports else None
    prev_report   = reports[-2] if len(reports) >= 2 else None

    latest_feedback = json.loads(latest_report.feedback) if latest_report and latest_report.feedback else {}

    # 7-day improvement
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent = [r for r in reports if r.created_at.replace(tzinfo=None) >= seven_days_ago]
    older  = [r for r in reports if r.created_at.replace(tzinfo=None) < seven_days_ago]

    if recent and older:
        seven_day_improvement = round(recent[-1].authority_score - older[-1].authority_score)
    elif len(reports) >= 2:
        seven_day_improvement = round(reports[-1].authority_score - reports[-2].authority_score)
    else:
        seven_day_improvement = 0

    # 30-day improvement
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    old_30 = [r for r in reports if r.created_at.replace(tzinfo=None) < thirty_days_ago]

    if old_30 and latest_report:
        thirty_day_improvement = round(latest_report.authority_score - old_30[-1].authority_score)
    elif len(reports) >= 2:
        thirty_day_improvement = round(reports[-1].authority_score - reports[0].authority_score)
    else:
        thirty_day_improvement = 0

    # Streak
    streak = 0
    if recordings:
        check_date = datetime.utcnow().date()
        dates_recorded = sorted(
            list({r.created_at.date() for r in recordings}),
            reverse=True
        )
        for d in dates_recorded:
            if d == check_date or d == check_date - timedelta(days=1):
                streak += 1
                check_date = d
            else:
                break

    # Active program
    active_program = None
    user_program = db.query(models.UserProgram).filter(
        models.UserProgram.user_id == current_user.id,
        models.UserProgram.status == "active"
    ).first()

    if user_program:
        program = db.query(models.Program).filter(
            models.Program.id == user_program.program_id
        ).first()
        if program:
            active_program = {
                "title":            program.title,
                "current_day":      user_program.current_day,
                "duration_days":    program.duration_days,
                "progress_percent": round((user_program.current_day / program.duration_days) * 100),
                "user_program_id":  user_program.id,
            }

    return {
        "chart_data":             chart_data,
        "total_recordings":       len(recordings),
        "latest_authority":       round(latest_report.authority_score) if latest_report else 0,
        "latest_confidence":      round(latest_report.confidence_score) if latest_report else 0,
        "latest_presence":        round(latest_report.presence_score) if latest_report else 0,
        "latest_leadership":      round(latest_report.leadership_score) if latest_report else 0,
        "best_authority":         round(max(r.authority_score for r in reports)) if reports else 0,
        # existing return mein yeh add karo:
        "latest_pause":    round(latest_report.pause_score)   if latest_report else 0,
        "latest_ending":   round(latest_report.ending_score)  if latest_report else 0,
        "latest_pitch":    round(latest_report.pitch_score)   if latest_report else 0,
        "latest_pace":     round(latest_report.pace_score)    if latest_report else 0,
        "user_level":             latest_feedback.get("user_level", "Beginner Speaker"),
        "target_score":           latest_feedback.get("target_score", 80),
        "progress_to_target":     latest_feedback.get("progress_to_target", 0),
        "seven_day_improvement":  seven_day_improvement,
        "thirty_day_improvement": thirty_day_improvement,
        "practice_streak":        streak,
        "active_program":         active_program,
        "prev_authority":         round(prev_report.authority_score) if prev_report else None,
    }