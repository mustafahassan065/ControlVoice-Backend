from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)

programs = [
    {
        "title": "Authority Foundation",
        "description": "Build the core habits of a commanding speaker from the ground up. This program focuses on the fundamental techniques that separate confident speakers from hesitant ones — strong endings, intentional pauses, and a measured pace that signals control.",
        "duration_days": 30,
        "focus": "pause_control,strong_endings,pace_control",
    },
    {
        "title": "Executive Presence",
        "description": "Elevate your communication to C-suite level. This advanced program trains the subtle vocal patterns that command boardrooms — deep pitch authority, zero filler words, and the kind of deliberate pace that makes every word feel intentional and weighty.",
        "duration_days": 30,
        "focus": "pitch_movement,strong_endings,pause_control",
    },
    {
        "title": "Public Speaking",
        "description": "Command a stage, deliver keynotes, and hold audience attention from the first word to the last. This program builds vocal energy, dynamic pitch range, and the rhythm patterns that keep hundreds of people engaged for an entire presentation.",
        "duration_days": 30,
        "focus": "pitch_movement,pace_control,strong_endings",
    },
    {
        "title": "Interview Confidence",
        "description": "Sound calm, credible, and unshakeable in any interview format — job interviews, media appearances, or investor pitches. This program eliminates filler words, builds steady pacing under pressure, and trains you to end every answer with conviction.",
        "duration_days": 30,
        "focus": "pace_control,pause_control,strong_endings",
    },
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(models.Program).count()
        if existing > 0:
            print(f"Already have {existing} programs — skipping seed.")
            return

        for p in programs:
            program = models.Program(
                title=p["title"],
                description=p["description"],
                duration_days=p["duration_days"],
                focus=p["focus"],
            )
            db.add(program)

        db.commit()
        print(f"✅ {len(programs)} programs seeded successfully.")
    except Exception as e:
        print(f"Seed error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed()