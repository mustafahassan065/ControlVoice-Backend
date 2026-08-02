from sqlalchemy.orm import Session
import models


def check_personal_bests(user_id: int, scores: dict, recording_id: int, db: Session) -> list:
    """
    New scores ko previous bests se compare karo.
    Agar koi new best hai toh save karo aur return karo.
    """
    new_bests = []

    metrics = {
        "authority":  scores.get("authority_score", 0),
        "confidence": scores.get("confidence_score", 0),
        "presence":   scores.get("presence_score", 0),
        "leadership": scores.get("leadership_score", 0),
    }

    for metric, new_score in metrics.items():
        # Previous best dhundo
        prev_best = db.query(models.PersonalBest).filter(
            models.PersonalBest.user_id == user_id,
            models.PersonalBest.metric == metric
        ).order_by(models.PersonalBest.new_best.desc()).first()

        prev_score = prev_best.new_best if prev_best else None

        if prev_score is None or new_score > prev_score:
            # New personal best!
            pb = models.PersonalBest(
                user_id=user_id,
                metric=metric,
                previous_best=prev_score,
                new_best=new_score,
                recording_id=recording_id
            )
            db.add(pb)
            new_bests.append({
                "metric":        metric,
                "new_score":     new_score,
                "previous_best": prev_score,
                "improvement":   round(new_score - prev_score) if prev_score else None,
            })

    if new_bests:
        db.commit()

    return new_bests