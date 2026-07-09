def calculate_scores(acoustic_data: dict) -> dict:

    # ─── COMPONENT SCORES (0-100) ───

    # 1. Strong Endings Score (25%)
    total_sentences = acoustic_data.get("total_sentences", 0)
    downward_endings = acoustic_data.get("downward_endings", 0)
    upward_endings = acoustic_data.get("upward_endings", 0)

    if total_sentences > 0:
        ending_score = round((downward_endings / total_sentences) * 100)
    else:
        ending_score = 50  # neutral default

    # 2. Pause Control Score (20%)
    pause_status = acoustic_data.get("pause_status", "no_pauses")
    avg_pause = acoustic_data.get("avg_pause_duration", 0)
    pause_count = acoustic_data.get("pause_count", 0)

    if pause_status == "good":
        pause_score = 85
    elif pause_status == "too_short":
        # short pauses — partial credit
        pause_score = max(30, round(50 + (avg_pause / 1.0) * 35))
    elif pause_status == "too_long":
        pause_score = max(30, round(85 - (avg_pause - 2.0) * 15))
    elif pause_status == "no_pauses":
        pause_score = 20
    else:
        pause_score = 50

    # Bonus for good pause frequency
    if pause_count >= 3:
        pause_score = min(100, pause_score + 10)

    # 3. Pace Control Score (20%)
    wpm = acoustic_data.get("speaking_rate_wpm", 0)
    wpm_status = acoustic_data.get("wpm_status", "error")

    if wpm_status == "optimal":
        pace_score = 90
    elif wpm_status == "too_fast":
        overage = wpm - 160
        pace_score = max(20, round(90 - (overage / 160) * 70))
    elif wpm_status == "too_slow":
        underage = 120 - wpm
        pace_score = max(20, round(90 - (underage / 120) * 70))
    else:
        pace_score = 50

    # 4. Pitch Variety Score (15%)
    pitch_status = acoustic_data.get("pitch_status", "no_pitch")
    pitch_std = acoustic_data.get("pitch_std_hz", 0)

    if pitch_status == "good":
        pitch_score = 80
    elif pitch_status == "very_varied":
        pitch_score = 95
    elif pitch_status == "monotone":
        pitch_score = max(20, round((pitch_std / 20) * 40))
    else:
        pitch_score = 50

    # 5. Vocal Energy Score (10%)
    # Pitch range se energy estimate karo
    pitch_range = acoustic_data.get("pitch_range_hz", 0)
    if pitch_range > 200:
        energy_score = 90
    elif pitch_range > 100:
        energy_score = 70
    elif pitch_range > 50:
        energy_score = 50
    elif pitch_range > 0:
        energy_score = 30
    else:
        energy_score = 20

    # 6. Filler Word Control Score (10%)
    filler_status = acoustic_data.get("filler_status", "needs_work")
    filler_percent = acoustic_data.get("filler_percent", 0)

    if filler_status == "excellent":
        filler_score = 95
    elif filler_status == "good":
        filler_score = 75
    else:
        filler_score = max(10, round(75 - (filler_percent - 5) * 5))

    # ─── AUTHORITY SCORE (main formula from document) ───
    authority_score = round(
        (ending_score * 0.25) +
        (pause_score  * 0.20) +
        (pace_score   * 0.20) +
        (pitch_score  * 0.15) +
        (energy_score * 0.10) +
        (filler_score * 0.10)
    )
    authority_score = max(0, min(100, authority_score))

    # ─── CONFIDENCE SCORE ───
    confidence_score = round(
        (pace_score   * 0.30) +
        (filler_score * 0.30) +
        (energy_score * 0.25) +
        (pause_score  * 0.15)
    )
    confidence_score = max(0, min(100, confidence_score))

    # ─── PRESENCE SCORE ───
    presence_score = round(
        (pitch_score  * 0.35) +
        (energy_score * 0.30) +
        (ending_score * 0.20) +
        (pause_score  * 0.15)
    )
    presence_score = max(0, min(100, presence_score))

    # ─── LEADERSHIP SCORE ───
    leadership_score = round(
        (ending_score * 0.30) +
        (pause_score  * 0.25) +
        (pitch_score  * 0.25) +
        (pace_score   * 0.20)
    )
    leadership_score = max(0, min(100, leadership_score))

    # ─── USER LEVEL (document ke mutabiq) ───
    if authority_score <= 40:
        user_level = "Beginner Speaker"
    elif authority_score <= 60:
        user_level = "Developing Presence"
    elif authority_score <= 75:
        user_level = "Confident Speaker"
    elif authority_score <= 90:
        user_level = "Authoritative Speaker"
    else:
        user_level = "Executive Presence"

    # ─── TARGET SCORE ───
    if authority_score < 100:
        if authority_score <= 40:
            target_score = 60
        elif authority_score <= 60:
            target_score = 75
        elif authority_score <= 75:
            target_score = 90
        else:
            target_score = 100
    else:
        target_score = 100

    progress_to_target = round((authority_score / target_score) * 100)

    return {
        "authority_score":   authority_score,
        "confidence_score":  confidence_score,
        "presence_score":    presence_score,
        "leadership_score":  leadership_score,
        "pace_score":        pace_score,
        "pause_score":       pause_score,
        "pitch_score":       pitch_score,
        "ending_score":      ending_score,
        "energy_score":      energy_score,
        "filler_score":      filler_score,
        "user_level":        user_level,
        "target_score":      target_score,
        "progress_to_target": progress_to_target,
    }