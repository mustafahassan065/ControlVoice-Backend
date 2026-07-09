from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)

exercises = [
    # ─── PAUSE CONTROL (10) ───
    {
        "category": "pause_control",
        "title": "The Power Pause",
        "instruction": "Before delivering your most important point, pause for 2 full seconds. This creates anticipation and signals importance. Most speakers rush through their key ideas — the pause is what makes them land.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "The most important thing I want you to remember is..."
    },
    {
        "category": "pause_control",
        "title": "Pause Before Numbers",
        "instruction": "Whenever you say a number or statistic, pause before AND after it. This gives your listener time to absorb the data and makes you sound more authoritative.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "We increased revenue by... 40 percent... in just 90 days."
    },
    {
        "category": "pause_control",
        "title": "The Breath Pause",
        "instruction": "Use your natural breath points as pauses. Every time you would breathe, make it intentional. Breathe through your nose, pause visibly, then continue. Leaders breathe slowly and speak calmly.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "This decision will affect everyone on this team... and I want to be clear about why."
    },
    {
        "category": "pause_control",
        "title": "Pause After Questions",
        "instruction": "When you ask a rhetorical question, pause for 3 seconds after it. This forces your audience to mentally answer and creates deep engagement.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "What would it mean for your career if you mastered this skill?..."
    },
    {
        "category": "pause_control",
        "title": "The Transition Pause",
        "instruction": "Pause for 1.5 seconds every time you move from one idea to the next. This separates your thoughts clearly and prevents your speech from sounding like one long run-on sentence.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "First, let me explain the problem... Now, here is the solution."
    },
    {
        "category": "pause_control",
        "title": "Silence Is Strength",
        "instruction": "Record yourself speaking for 30 seconds, then review. Count how many times you used 'um' or 'uh' to fill silence. Replace every single one with a pause. Silence sounds confident — filler words sound nervous.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "The reason I believe this will work is..."
    },
    {
        "category": "pause_control",
        "title": "Three-Point Pause",
        "instruction": "When listing three things, pause between each one. Say item one, pause. Say item two, pause. Say item three, pause longer. This gives each point weight and makes lists memorable.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "You need three things to succeed: clarity... commitment... and courage."
    },
    {
        "category": "pause_control",
        "title": "The Dramatic Pause",
        "instruction": "Before revealing the conclusion or punchline of your message, pause for 2–3 seconds. Look at your audience if in person. Then deliver your point. This is the most powerful pause in communication.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "After six months of hard work, the results were..."
    },
    {
        "category": "pause_control",
        "title": "Slow Your Opening",
        "instruction": "The first 10 seconds of any speech or presentation sets your authority. Speak your opening sentence, then pause completely for 2 seconds before continuing. Never rush your opening.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "Good morning. My name is [your name]... and today I want to talk about something that matters."
    },
    {
        "category": "pause_control",
        "title": "End With Silence",
        "instruction": "After your final sentence, do not say 'thank you' immediately. Pause for 2 seconds, let your words land, then close. This is what separates good speakers from great ones.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "And that is why I believe this is the right decision for all of us."
    },

    # ─── STRONG ENDINGS (10) ───
    {
        "category": "strong_endings",
        "title": "Drop Your Pitch",
        "instruction": "Record yourself saying a statement. Listen to whether your voice goes UP at the end (like a question) or DOWN (like a declaration). Practice ending every statement with a downward pitch. Down = authority. Up = uncertainty.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "This is the direction we are moving in."
    },
    {
        "category": "strong_endings",
        "title": "The Declaration Exercise",
        "instruction": "Say each sentence as if you are declaring a fact that cannot be questioned. Your voice should feel like it is landing on solid ground at the end — not floating upward into the air.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "I am confident this is the right approach."
    },
    {
        "category": "strong_endings",
        "title": "Never Question Your Statements",
        "instruction": "Most people unconsciously end statements with rising intonation, which makes everything sound like a question. Record 5 statements. Listen back. If any end going up, re-record until they all end going down.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "We have done the research and the data supports this."
    },
    {
        "category": "strong_endings",
        "title": "Slow The Last Word",
        "instruction": "Slightly slow down on the last word of each sentence. This gives your ending weight and prevents your voice from rushing upward at the finish. Slow last word = strong ending.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "The answer is absolutely clear."
    },
    {
        "category": "strong_endings",
        "title": "Full Stop Practice",
        "instruction": "After your last word, stop completely. No 'um', no 'so', no trailing off. The full stop after a strong ending is what makes the sentence feel complete and authoritative.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "This is my final recommendation."
    },
    {
        "category": "strong_endings",
        "title": "The Leader's Statement",
        "instruction": "Leaders make statements, not suggestions. Change 'I think we could maybe try...' to 'We will do this.' Practice turning every suggestion into a clear declaration.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "We will launch this by the end of the month."
    },
    {
        "category": "strong_endings",
        "title": "Anchor Your Closing Word",
        "instruction": "Choose the most important word in your sentence and make it your ending. Rearrange your sentences so the key word comes last, then drop your pitch on it.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "What matters most in this situation is trust."
    },
    {
        "category": "strong_endings",
        "title": "The Conviction Read",
        "instruction": "Take any paragraph and read it aloud three times. First at normal speed. Second, emphasizing every last word. Third, at 80% speed with downward pitch on every ending. Record all three and compare.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "Our team worked hard. We delivered results. The client is satisfied."
    },
    {
        "category": "strong_endings",
        "title": "No Trailing Off",
        "instruction": "Many speakers trail off at the end of sentences — their voice gets quieter and weaker as the sentence ends. Practice keeping your volume steady or even slightly increasing through to the last syllable.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "Every person in this room has the ability to lead."
    },
    {
        "category": "strong_endings",
        "title": "The Two-Sentence Drill",
        "instruction": "Say two sentences back to back. Make the first one end strong. Then pause. Make the second one end even stronger. Record and listen. The contrast between strong endings creates natural rhythm and authority.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "We know the problem. Now we will solve it."
    },

    # ─── PITCH MOVEMENT (10) ───
    {
        "category": "pitch_movement",
        "title": "High-Low Contrast",
        "instruction": "Say the first half of your sentence at a slightly higher pitch, and drop to a lower pitch for the second half. This natural contrast prevents monotone delivery and keeps listeners engaged.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "The challenge we face is significant... but the opportunity is even greater."
    },
    {
        "category": "pitch_movement",
        "title": "Emphasize Key Words",
        "instruction": "In every sentence, identify the ONE most important word. Raise your pitch slightly on that word only. Everything else stays flat. This creates natural, focused emphasis without sounding dramatic.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "This is the MOST important decision we will make this year."
    },
    {
        "category": "pitch_movement",
        "title": "The Storyteller's Rise",
        "instruction": "When building toward a point, let your pitch gradually rise with each sentence, then drop sharply on your conclusion. This is the natural arc of compelling storytelling.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "It started small. Then it grew. Then it changed everything."
    },
    {
        "category": "pitch_movement",
        "title": "Pitch On Positive Words",
        "instruction": "Every time you say a positive or exciting word — 'opportunity', 'growth', 'success', 'results' — let your pitch rise naturally. For serious or negative words, drop your pitch. Pitch should match meaning.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "The RESULTS exceeded expectations and the GROWTH was remarkable."
    },
    {
        "category": "pitch_movement",
        "title": "Avoid The Robot",
        "instruction": "Record yourself reading a paragraph in your normal voice. Then read it again, deliberately varying your pitch every 2–3 words. It may feel dramatic — but on playback it sounds natural and engaging.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "I have been working in this industry for ten years and I have learned that the most important skill is communication."
    },
    {
        "category": "pitch_movement",
        "title": "The Question-Answer Arc",
        "instruction": "When asking a rhetorical question, let your pitch rise. When answering it, bring your pitch back down. This question-answer arc is one of the most natural and powerful pitch patterns in speech.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "What is the solution?... The solution is simpler than you think."
    },
    {
        "category": "pitch_movement",
        "title": "Sing Your Sentence",
        "instruction": "Take one sentence and literally sing it — exaggerate the pitch changes completely. Then say it normally. You will find your natural pitch variation increases without even trying. This unlocks your vocal range.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "I am excited to share this news with all of you today."
    },
    {
        "category": "pitch_movement",
        "title": "Three Level Drill",
        "instruction": "Say the same sentence at three different pitch levels: high, medium, and low. Notice how each version creates a different emotional tone. Then find the version that sounds most like the emotion you want to convey.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "We need to talk about what happened."
    },
    {
        "category": "pitch_movement",
        "title": "Descending List",
        "instruction": "When listing items that are decreasing in importance, let your pitch descend with each item. When listing items building in importance, let it ascend. Your pitch pattern should mirror your content structure.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "We need focus... dedication... and above all, courage."
    },
    {
        "category": "pitch_movement",
        "title": "The Warmth Pitch",
        "instruction": "Warmth and connection are conveyed through a mid-to-high pitch with gentle variation. Practice speaking as if you genuinely care about every word. Authentic emotion creates natural, compelling pitch movement.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "I want you to know that your work truly makes a difference."
    },

    # ─── PACE CONTROL (10) ───
    {
        "category": "pace_control",
        "title": "The 140 WPM Target",
        "instruction": "The ideal speaking pace for authority is 130–160 WPM. Record yourself for 60 seconds, count the words, divide by duration. If above 160 — slow down. If below 120 — pick up energy. Practice until you hit 140 WPM naturally.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "I want to walk you through the key findings from our latest research and explain exactly what they mean for our strategy going forward."
    },
    {
        "category": "pace_control",
        "title": "Slow Down For Emphasis",
        "instruction": "At your normal pace, identify your most important sentence. Now say that one sentence at 70% of your normal speed. The contrast with your normal pace automatically signals importance to your listener.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "And the result... was beyond anything we expected."
    },
    {
        "category": "pace_control",
        "title": "The Metronome Method",
        "instruction": "Use a metronome app set to 70 BPM. Try to speak one stressed syllable per beat. This trains your internal rhythm and prevents the unconscious speeding up that happens when speakers get nervous.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "Every word I say is intentional and deliberate."
    },
    {
        "category": "pace_control",
        "title": "Fast-Slow Contrast",
        "instruction": "Deliberately speak faster during background information, then slow to 70% speed for your key point. This contrast is one of the most powerful pace techniques — it signals to the brain: 'this part matters.'",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "We analyzed the data, reviewed all options, considered every scenario — and the conclusion is this."
    },
    {
        "category": "pace_control",
        "title": "Read Aloud Slowly",
        "instruction": "Take any article and read it aloud at 70% of your natural speed. This feels painfully slow at first. But this is exactly how great speakers sound. Do this for 5 minutes every day for one week.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "Leadership is not about being in charge. It is about taking care of those in your charge."
    },
    {
        "category": "pace_control",
        "title": "One Thought At A Time",
        "instruction": "Many speakers rush because they are trying to deliver multiple thoughts at once. Practice saying one complete thought, pausing, then saying the next. One thought. Pause. Next thought. Pause. This naturally regulates pace.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "The first issue is timing. The second issue is resources. The third issue is communication."
    },
    {
        "category": "pace_control",
        "title": "Breathe To Control Speed",
        "instruction": "Nervous speakers hold their breath and rush. Calm speakers breathe fully between sentences. Practice taking a full breath after every 2–3 sentences. Your pace will naturally slow to a commanding rhythm.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "I appreciate everyone being here today. [breath] We have a lot to cover. [breath] Let us get started."
    },
    {
        "category": "pace_control",
        "title": "The Anchor Word Slow",
        "instruction": "Identify the most important word in each sentence. Slow down on that word — stretch it very slightly. This micro-deceleration on key words creates a natural, authoritative rhythm without slowing your overall pace too much.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "What we need right now is clarity."
    },
    {
        "category": "pace_control",
        "title": "Count To Three",
        "instruction": "At the end of every major point, silently count to three before starting your next sentence. This feels like an eternity to you but sounds perfectly natural to your listener. It gives them time to absorb what you said.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "That is the core of our strategy. [1, 2, 3] Now let me tell you how we execute it."
    },
    {
        "category": "pace_control",
        "title": "Energy Without Speed",
        "instruction": "High energy does not mean fast speech. Practice speaking with maximum vocal energy, enthusiasm, and presence — while keeping your pace at 130 WPM. Energy comes from pitch variation, volume, and pauses — not speed.",
        "wrong_audio_url": None,
        "correct_audio_url": None,
        "practice_template": "I am genuinely excited about what we are building together and I want you to feel that too."
    },
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(models.Exercise).count()
        if existing > 0:
            print(f"Already have {existing} exercises — skipping seed.")
            return

        for ex in exercises:
            exercise = models.Exercise(
                category=ex["category"],
                title=ex["title"],
                instruction=ex["instruction"],
                wrong_audio_url=ex["wrong_audio_url"],
                correct_audio_url=ex["correct_audio_url"],
                practice_template=ex["practice_template"]
            )
            db.add(exercise)

        db.commit()
        print(f"✅ {len(exercises)} exercises seeded successfully.")
    except Exception as e:
        print(f"Seed error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed()