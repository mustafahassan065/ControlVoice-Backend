from sqlalchemy.orm import Session
import models


def get_recommended_exercises(scores: dict, db: Session, limit: int = 6) -> list:
    """
    Scores ke weak areas ke mutabiq exercises recommend karo.
    Sab se weak category ko sab se zyada exercises milenge.
    """

    # Score to category mapping
    category_scores = {
        "pause_control":  scores.get("pause_score", 50),
        "strong_endings": scores.get("ending_score", 50),
        "pitch_movement": scores.get("pitch_score", 50),
        "pace_control":   scores.get("pace_score", 50),
    }

    # Sort by score ascending (weakest first)
    sorted_categories = sorted(category_scores.items(), key=lambda x: x[1])

    recommended = []
    slots = {
        0: 3,  # weakest category gets 3 exercises
        1: 2,  # second weakest gets 2
        2: 1,  # third gets 1
        3: 0,  # strongest gets 0
    }

    for rank, (category, score) in enumerate(sorted_categories):
        count = slots.get(rank, 0)
        if count == 0:
            continue

        exercises = db.query(models.Exercise).filter(
            models.Exercise.category == category
        ).limit(count).all()

        for ex in exercises:
            recommended.append({
                "id":                ex.id,
                "category":          ex.category,
                "title":             ex.title,
                "instruction":       ex.instruction,
                "practice_template": ex.practice_template,
                "wrong_audio_url":   ex.wrong_audio_url,
                "correct_audio_url": ex.correct_audio_url,
                "score":             score,
                "priority":          rank + 1,
            })

    return recommended[:limit]