from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from acoustic_analysis import analyze_audio
from scoring_engine import calculate_scores
from ai_feedback import generate_feedback
import models
import os, shutil, uuid, json
from plan_guard import check_analysis_limit
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/audio", tags=["audio"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcribe_and_analyze(recording_id: int, filepath: str, db: Session):
    try:
        # Step 1 — Whisper
        with open(filepath, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
        transcript = result.text

        # Step 2 — Acoustic Analysis
        acoustic_data = analyze_audio(filepath, transcript)

        # Step 3 — Scoring
        scores = calculate_scores(acoustic_data)

        # Step 4 — AI Feedback
        ai_feedback = generate_feedback(transcript, acoustic_data, scores)

        # Step 5 — Save recording
        recording = db.query(models.Recording).filter(
            models.Recording.id == recording_id
        ).first()

        if recording:
            recording.transcript = transcript
            recording.acoustic_data = json.dumps(acoustic_data)
            db.commit()

        # Step 6 — Save report
        report = models.Report(
            user_id=recording.user_id,
            recording_id=recording_id,
            authority_score=scores["authority_score"],
            confidence_score=scores["confidence_score"],
            presence_score=scores["presence_score"],
            leadership_score=scores["leadership_score"],
            pace_score=scores["pace_score"],
            pause_score=scores["pause_score"],
            pitch_score=scores["pitch_score"],
            ending_score=scores["ending_score"],
            feedback=json.dumps({
                "user_level":         scores["user_level"],
                "target_score":       scores["target_score"],
                "progress_to_target": scores["progress_to_target"],
                "energy_score":       scores["energy_score"],
                "filler_score":       scores["filler_score"],
                "feedback_text":      ai_feedback["feedback_text"],
                "weaknesses":         ai_feedback["weaknesses"],
                "strengths":          ai_feedback["strengths"],
            })
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        # Step 7 — Progress Snapshot save karo (document requirement)
        snapshot = models.ProgressSnapshot(
            user_id=recording.user_id,
            authority_score=scores["authority_score"],
            confidence_score=scores["confidence_score"],
            presence_score=scores["presence_score"],
            leadership_score=scores["leadership_score"],
        )
        db.add(snapshot)
        db.commit()

        print(f"✅ Report ID {report.id} + Snapshot saved — Authority: {scores['authority_score']}")

    except Exception as e:
        print(f"Analysis error: {e}")

@router.post("/upload")
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    duration: float = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Plan limit check — Free user sirf 1
    check_analysis_limit(current_user, db)

    ext = file.filename.split(".")[-1] if "." in file.filename else "webm"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    recording = models.Recording(
        user_id=current_user.id,
        audio_url=f"/uploads/{filename}",
        duration=duration
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)

    background_tasks.add_task(
        transcribe_and_analyze,
        recording.id,
        filepath,
        db
    )

    return {
        "id":        recording.id,
        "user_id":   recording.user_id,
        "audio_url": recording.audio_url,
        "duration":  recording.duration,
        "transcript": None,
        "created_at": recording.created_at
    }


@router.get("/my-recordings")
def get_my_recordings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    recordings = db.query(models.Recording).filter(
        models.Recording.user_id == current_user.id
    ).order_by(models.Recording.created_at.desc()).all()

    result = []
    for rec in recordings:
        report = db.query(models.Report).filter(
            models.Report.recording_id == rec.id
        ).first()

        result.append({
            "id": rec.id,
            "audio_url": rec.audio_url,
            "transcript": rec.transcript,
            "acoustic_data": json.loads(rec.acoustic_data) if rec.acoustic_data else None,
            "report": {
                "id":               report.id,
                "authority_score":  report.authority_score,
                "confidence_score": report.confidence_score,
                "presence_score":   report.presence_score,
                "leadership_score": report.leadership_score,
                "pace_score":       report.pace_score,
                "pause_score":      report.pause_score,
                "pitch_score":      report.pitch_score,
                "ending_score":     report.ending_score,
                "feedback":         json.loads(report.feedback) if report.feedback else {},
            } if report else None,
            "duration": rec.duration,
            "created_at": rec.created_at
        })
    return result


@router.get("/recording/{recording_id}")
def get_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    recording = db.query(models.Recording).filter(
        models.Recording.id == recording_id,
        models.Recording.user_id == current_user.id
    ).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    report = db.query(models.Report).filter(
        models.Report.recording_id == recording_id
    ).first()

    return {
        "id": recording.id,
        "audio_url": recording.audio_url,
        "transcript": recording.transcript,
        "acoustic_data": json.loads(recording.acoustic_data) if recording.acoustic_data else None,
        "report": {
            "id":               report.id,
            "authority_score":  report.authority_score,
            "confidence_score": report.confidence_score,
            "presence_score":   report.presence_score,
            "leadership_score": report.leadership_score,
            "pace_score":       report.pace_score,
            "pause_score":      report.pause_score,
            "pitch_score":      report.pitch_score,
            "ending_score":     report.ending_score,
            "feedback":         json.loads(report.feedback) if report.feedback else {},
        } if report else None,
        "duration": recording.duration,
        "created_at": recording.created_at
    }