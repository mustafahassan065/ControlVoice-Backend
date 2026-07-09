from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_feedback(transcript: str, acoustic_data: dict, scores: dict) -> dict:

    # Weaknesses identify karo
    weaknesses = []
    strengths = []

    wpm_status = acoustic_data.get("wpm_status", "")
    if wpm_status == "too_fast":
        weaknesses.append(f"speaking too fast ({acoustic_data.get('speaking_rate_wpm')} WPM — target is 130–160 WPM)")
    elif wpm_status == "too_slow":
        weaknesses.append(f"speaking too slow ({acoustic_data.get('speaking_rate_wpm')} WPM — target is 130–160 WPM)")
    else:
        strengths.append(f"excellent speaking pace at {acoustic_data.get('speaking_rate_wpm')} WPM")

    pause_status = acoustic_data.get("pause_status", "")
    if pause_status == "no_pauses":
        weaknesses.append("no meaningful pauses — pausing before key ideas builds authority")
    elif pause_status == "too_short":
        weaknesses.append(f"pauses too short (avg {acoustic_data.get('avg_pause_duration')}s — target is 1–2 seconds)")
    elif pause_status == "good":
        strengths.append("good pause control")

    pitch_status = acoustic_data.get("pitch_status", "")
    if pitch_status == "monotone":
        weaknesses.append("monotone delivery — very little pitch variation detected")
    elif pitch_status in ["good", "very_varied"]:
        strengths.append("strong pitch variation and vocal expressiveness")

    ending_status = acoustic_data.get("ending_status", "")
    downward = acoustic_data.get("downward_endings", 0)
    upward = acoustic_data.get("upward_endings", 0)
    if ending_status == "weak":
        weaknesses.append(f"weak sentence endings — {upward} upward (questioning) endings detected vs {downward} strong downward endings")
    elif ending_status == "strong":
        strengths.append(f"strong sentence endings — {downward} out of {downward + upward} sentences ended with authority")

    filler_status = acoustic_data.get("filler_status", "")
    total_fillers = acoustic_data.get("total_fillers", 0)
    filler_words = acoustic_data.get("filler_words", {})
    if filler_status == "needs_work":
        filler_list = ", ".join([f'"{w}"' for w in filler_words.keys()])
        weaknesses.append(f"too many filler words ({total_fillers} detected: {filler_list})")
    elif filler_status == "excellent":
        strengths.append("excellent filler word control")

    # Prompt build karo
    weakness_text = "\n".join([f"- {w}" for w in weaknesses]) if weaknesses else "- None identified"
    strength_text = "\n".join([f"- {s}" for s in strengths]) if strengths else "- None identified"

    prompt = f"""You are an expert voice and executive communication coach. 
Analyze this speaker's voice assessment and provide personalized coaching feedback.

TRANSCRIPT:
"{transcript}"

VOICE METRICS:
- Speaking Rate: {acoustic_data.get('speaking_rate_wpm')} WPM ({wpm_status})
- Pauses: {acoustic_data.get('pause_count')} pauses, avg {acoustic_data.get('avg_pause_duration')}s ({pause_status})
- Pitch Range: {acoustic_data.get('pitch_range_hz')} Hz ({pitch_status})
- Filler Words: {total_fillers} found ({filler_status})
- Sentence Endings: {downward} strong, {upward} weak

SCORES:
- Authority Score: {scores.get('authority_score')}/100
- Confidence Score: {scores.get('confidence_score')}/100
- Presence Score: {scores.get('presence_score')}/100
- Leadership Score: {scores.get('leadership_score')}/100
- User Level: {scores.get('user_level')}

IDENTIFIED STRENGTHS:
{strength_text}

IDENTIFIED WEAKNESSES:
{weakness_text}

Write a personalized coaching feedback in 3 short paragraphs:
1. Overall assessment (2-3 sentences) — mention their Authority Score and current level
2. Top 2-3 specific weaknesses to work on with clear explanation of why it matters
3. One actionable exercise they can do TODAY to improve their biggest weakness

Keep the tone like a world-class executive coach — direct, encouraging, specific. 
Do NOT use bullet points. Write in flowing paragraphs.
Maximum 200 words total."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert voice coach specializing in executive presence and authority communication. Be direct, specific, and actionable."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=400,
        temperature=0.7
    )

    feedback_text = response.choices[0].message.content.strip()

    return {
        "feedback_text": feedback_text,
        "weaknesses": weaknesses,
        "strengths": strengths,
    }

def generate_practice_sentences(template: str, category: str) -> list:
    """GPT-4 se 5 custom practice sentences generate karo"""

    category_context = {
        "pause_control":  "pausing effectively before key ideas",
        "strong_endings": "ending statements with downward authoritative pitch",
        "pitch_movement": "varying pitch to emphasize important words",
        "pace_control":   "speaking at a measured, authoritative pace",
    }

    context = category_context.get(category, "improving vocal authority")

    prompt = f"""You are a voice coaching expert. Generate 5 unique practice sentences based on this template.

Template: "{template}"
Focus: {context}

Rules:
- Each sentence should be different but follow the same structure as the template
- Keep sentences between 10–20 words
- Make them feel natural and professional — like something a business leader would say
- Do NOT number them
- Return ONLY the 5 sentences, one per line, nothing else

Generate 5 sentences now:"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.8
    )

    text = response.choices[0].message.content.strip()
    sentences = [s.strip() for s in text.split('\n') if s.strip()]
    return sentences[:5]