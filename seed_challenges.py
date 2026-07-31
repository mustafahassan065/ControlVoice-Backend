from database import SessionLocal, engine
import models
from datetime import date

models.Base.metadata.create_all(bind=engine)

PROMPTS = [
    "Introduce yourself in 30 seconds as if meeting someone important for the first time.",
    "Explain what you do for work clearly in under 45 seconds.",
    "Describe your biggest professional achievement in 30 seconds.",
    "Tell us about a challenge you overcame and what you learned.",
    "Explain one idea you are passionate about in 30 seconds.",
    "Describe your goals for the next 6 months with confidence.",
    "Introduce your company or project in 45 seconds.",
    "Explain why you are the right person for an opportunity you want.",
    "Describe a skill you have mastered and how you developed it.",
    "Give a 30-second update as if presenting to a senior leader.",
    "Explain a complex topic in simple terms in under 60 seconds.",
    "Describe what makes you different from others in your field.",
    "Tell us about a decision you made under pressure.",
    "Explain your morning routine and why it works for you.",
    "Describe a book or idea that changed how you think.",
    "Convince someone to try something you believe in — 30 seconds.",
    "Explain one habit that has made you more effective.",
    "Describe where you want to be in 5 years.",
    "Talk about a mentor or person who influenced your career.",
    "Give a strong closing statement as if ending a presentation.",
    "Explain a mistake you made and what you learned from it.",
    "Describe your leadership style in 30 seconds.",
    "Introduce a new product or idea with energy and clarity.",
    "Explain what drives you professionally in under 45 seconds.",
    "Give a confident answer to: 'Tell me about yourself.'",
    "Describe a time you had to persuade someone to change their mind.",
    "Explain the most important lesson your career has taught you.",
    "Talk about a project you are proud of and what made it succeed.",
    "Describe your communication style and how it has helped you.",
    "Give a 30-second answer to: 'Why should we choose you?'",
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(models.DailyChallenge).count()
        if existing >= len(PROMPTS):
            print(f"Already have {existing} challenges.")
            return

        # Clear and reseed
        db.query(models.DailyChallenge).delete()
        db.commit()

        for i, prompt in enumerate(PROMPTS):
            challenge = models.DailyChallenge(
                prompt=prompt,
                date=f"prompt_{i+1}",
            )
            db.add(challenge)

        db.commit()
        print(f"✅ {len(PROMPTS)} challenge prompts seeded.")
    except Exception as e:
        print(f"Seed error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed()