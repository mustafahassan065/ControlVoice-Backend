from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models
from datetime import datetime
from plan_guard import check_feature_access

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("/all")
def get_all_programs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    programs = db.query(models.Program).all()

    # User ka active program bhi bhejo
    user_programs = db.query(models.UserProgram).filter(
        models.UserProgram.user_id == current_user.id
    ).all()
    user_program_map = {up.program_id: up for up in user_programs}

    result = []
    for p in programs:
        up = user_program_map.get(p.id)
        result.append({
            "id":           p.id,
            "title":        p.title,
            "description":  p.description,
            "duration_days": p.duration_days,
            "focus":        p.focus.split(",") if p.focus else [],
            "user_program": {
                "id":          up.id,
                "current_day": up.current_day,
                "status":      up.status,
                "started_at":  up.started_at,
            } if up else None,
        })
    return result

@router.post("/assign/{program_id}")
def assign_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Programs sirf Pro+ ke liye
    check_feature_access(current_user, "programs")

    # Executive program sirf Executive plan ke liye
    program = db.query(models.Program).filter(
        models.Program.id == program_id
    ).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    if program.title == "Executive Presence":
        check_feature_access(current_user, "executive_program")

    # baaki code same...
    existing = db.query(models.UserProgram).filter(
        models.UserProgram.user_id == current_user.id,
        models.UserProgram.program_id == program_id
    ).first()

    if existing:
        if existing.status == "completed":
            existing.current_day = 1
            existing.status = "active"
            existing.started_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return {"message": "Program restarted", "user_program": {
                "id": existing.id,
                "current_day": existing.current_day,
                "status": existing.status,
                "started_at": existing.started_at,
            }}
        return {"message": "Already enrolled", "user_program": {
            "id": existing.id,
            "current_day": existing.current_day,
            "status": existing.status,
            "started_at": existing.started_at,
        }}

    db.query(models.UserProgram).filter(
        models.UserProgram.user_id == current_user.id,
        models.UserProgram.status == "active"
    ).update({"status": "paused"})

    user_program = models.UserProgram(
        user_id=current_user.id,
        program_id=program_id,
        current_day=1,
        status="active"
    )
    db.add(user_program)
    db.commit()
    db.refresh(user_program)

    return {
        "message": "Program started",
        "user_program": {
            "id":          user_program.id,
            "current_day": user_program.current_day,
            "status":      user_program.status,
            "started_at":  user_program.started_at,
        }
    }

@router.get("/my-programs")
def get_my_programs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user_programs = db.query(models.UserProgram).filter(
        models.UserProgram.user_id == current_user.id
    ).all()

    result = []
    for up in user_programs:
        program = db.query(models.Program).filter(
            models.Program.id == up.program_id
        ).first()
        result.append({
            "id":           up.id,
            "program_id":   up.program_id,
            "title":        program.title,
            "description":  program.description,
            "duration_days": program.duration_days,
            "current_day":  up.current_day,
            "status":       up.status,
            "started_at":   up.started_at,
            "progress_percent": round((up.current_day / program.duration_days) * 100),
        })
    return result


@router.post("/progress/{user_program_id}")
def update_progress(
    user_program_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user_program = db.query(models.UserProgram).filter(
        models.UserProgram.id == user_program_id,
        models.UserProgram.user_id == current_user.id
    ).first()

    if not user_program:
        raise HTTPException(status_code=404, detail="Program not found")

    program = db.query(models.Program).filter(
        models.Program.id == user_program.program_id
    ).first()

    if user_program.current_day < program.duration_days:
        user_program.current_day += 1
    else:
        user_program.status = "completed"

    db.commit()
    db.refresh(user_program)

    return {
        "current_day":       user_program.current_day,
        "status":            user_program.status,
        "progress_percent":  round((user_program.current_day / program.duration_days) * 100),
    }


@router.post("/pause/{user_program_id}")
def pause_program(
    user_program_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user_program = db.query(models.UserProgram).filter(
        models.UserProgram.id == user_program_id,
        models.UserProgram.user_id == current_user.id
    ).first()
    if not user_program:
        raise HTTPException(status_code=404, detail="Not found")

    user_program.status = "paused" if user_program.status == "active" else "active"
    db.commit()

    return {"status": user_program.status}