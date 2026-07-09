import parselmouth
from parselmouth.praat import call
import librosa
import numpy as np
import re
import subprocess
import os
import tempfile

def convert_to_wav(audio_path: str) -> str:
    """Any format ko WAV mein convert karo Parselmouth ke liye"""
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    tmp_path = tmp.name
    tmp.close()
    
    subprocess.run([
        'ffmpeg', '-y', '-i', audio_path,
        '-ar', '16000',
        '-ac', '1',
        '-f', 'wav',
        tmp_path
    ], capture_output=True)
    
    return tmp_path


def analyze_audio(audio_path: str, transcript: str) -> dict:
    results = {}
    
    # Convert to WAV first
    wav_path = convert_to_wav(audio_path)
    
    try:
        # ─── 1. SPEAKING RATE (WPM) ───
        try:
            words = [w for w in transcript.strip().split() if w]
            word_count = len(words)

            sound = parselmouth.Sound(wav_path)
            duration_seconds = sound.duration
            duration_minutes = duration_seconds / 60

            wpm = round(word_count / duration_minutes) if duration_minutes > 0 else 0
            results["word_count"] = word_count
            results["duration_seconds"] = round(duration_seconds, 2)
            results["speaking_rate_wpm"] = wpm
            results["wpm_status"] = (
                "too_slow" if wpm < 120
                else "optimal" if wpm <= 160
                else "too_fast"
            )
        except Exception as e:
            results["speaking_rate_wpm"] = 0
            results["wpm_status"] = "error"
            print(f"WPM error: {e}")

        # ─── 2. PAUSE DURATION & FREQUENCY ───
        try:
            y, sr = librosa.load(wav_path, sr=None, mono=True)

            frame_length = 2048
            hop_length = 512
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            silence_threshold = np.percentile(rms, 20)

            is_silent = rms < silence_threshold

            pauses = []
            in_pause = False
            pause_start = 0
            frame_duration = hop_length / sr

            for i, silent in enumerate(is_silent):
                if silent and not in_pause:
                    in_pause = True
                    pause_start = i
                elif not silent and in_pause:
                    in_pause = False
                    pause_duration = (i - pause_start) * frame_duration
                    if pause_duration >= 0.3:
                        pauses.append(round(pause_duration, 2))

            results["pause_count"] = len(pauses)
            results["pause_durations"] = pauses
            results["avg_pause_duration"] = round(float(np.mean(pauses)), 2) if pauses else 0
            results["pause_status"] = (
                "good" if pauses and 1.0 <= np.mean(pauses) <= 2.0
                else "too_short" if pauses and np.mean(pauses) < 1.0
                else "too_long" if pauses and np.mean(pauses) > 2.0
                else "no_pauses"
            )
        except Exception as e:
            results["pause_count"] = 0
            results["avg_pause_duration"] = 0
            results["pause_status"] = "error"
            print(f"Pause error: {e}")

        # ─── 3. PITCH RANGE & MOVEMENT ───
        try:
            sound = parselmouth.Sound(wav_path)
            pitch = call(sound, "To Pitch", 0.0, 75, 600)
            pitch_values = pitch.selected_array['frequency']
            voiced = pitch_values[pitch_values > 0]

            if len(voiced) > 0:
                pitch_min = round(float(np.min(voiced)), 1)
                pitch_max = round(float(np.max(voiced)), 1)
                pitch_mean = round(float(np.mean(voiced)), 1)
                pitch_std = round(float(np.std(voiced)), 1)
                pitch_range = round(pitch_max - pitch_min, 1)

                results["pitch_min_hz"] = pitch_min
                results["pitch_max_hz"] = pitch_max
                results["pitch_mean_hz"] = pitch_mean
                results["pitch_std_hz"] = pitch_std
                results["pitch_range_hz"] = pitch_range
                results["pitch_values"] = [
                    round(float(v), 1) for v in voiced[::10][:50]
                ]
                results["pitch_status"] = (
                    "monotone" if pitch_std < 20
                    else "good" if 20 <= pitch_std <= 60
                    else "very_varied"
                )
            else:
                results["pitch_min_hz"] = 0
                results["pitch_max_hz"] = 0
                results["pitch_mean_hz"] = 0
                results["pitch_std_hz"] = 0
                results["pitch_range_hz"] = 0
                results["pitch_values"] = []
                results["pitch_status"] = "no_pitch"
        except Exception as e:
            results["pitch_range_hz"] = 0
            results["pitch_status"] = "error"
            print(f"Pitch error: {e}")

        # ─── 4. FILLER WORDS ───
        try:
            filler_list = ["um", "uh", "like", "you know", "actually",
                           "basically", "literally", "right", "so", "okay", "hmm"]
            transcript_lower = transcript.lower()
            filler_counts = {}
            total_fillers = 0

            for filler in filler_list:
                pattern = r'\b' + re.escape(filler) + r'\b'
                count = len(re.findall(pattern, transcript_lower))
                if count > 0:
                    filler_counts[filler] = count
                    total_fillers += count

            word_count = len(transcript.split())
            filler_percent = round((total_fillers / word_count * 100), 1) if word_count > 0 else 0

            results["filler_words"] = filler_counts
            results["total_fillers"] = total_fillers
            results["filler_percent"] = filler_percent
            results["filler_status"] = (
                "excellent" if filler_percent < 2
                else "good" if filler_percent < 5
                else "needs_work"
            )
        except Exception as e:
            results["filler_words"] = {}
            results["total_fillers"] = 0
            results["filler_status"] = "error"
            print(f"Filler error: {e}")

        # ─── 5. SENTENCE ENDINGS ───
        try:
            sound = parselmouth.Sound(wav_path)
            pitch = call(sound, "To Pitch", 0.0, 75, 600)
            pitch_values = pitch.selected_array['frequency']
            voiced = pitch_values[pitch_values > 0]

            upward_endings = 0
            downward_endings = 0

            if len(voiced) > 20:
                sentences = re.split(r'[.!?]+', transcript)
                sentences = [s.strip() for s in sentences if s.strip()]
                total_sentences = len(sentences)

                segment_size = max(1, len(voiced) // max(total_sentences, 1))

                for idx in range(total_sentences):
                    start = idx * segment_size
                    end = min(start + segment_size, len(voiced))
                    segment = voiced[start:end]

                    if len(segment) > 4:
                        first_half = np.mean(segment[:len(segment)//2])
                        second_half = np.mean(segment[len(segment)//2:])
                        if second_half > first_half * 1.05:
                            upward_endings += 1
                        else:
                            downward_endings += 1

                results["upward_endings"] = upward_endings
                results["downward_endings"] = downward_endings
                results["total_sentences"] = total_sentences
                results["ending_status"] = (
                    "strong" if downward_endings >= upward_endings
                    else "weak"
                )
            else:
                results["upward_endings"] = 0
                results["downward_endings"] = 0
                results["total_sentences"] = 0
                results["ending_status"] = "insufficient_data"

        except Exception as e:
            results["upward_endings"] = 0
            results["downward_endings"] = 0
            results["ending_status"] = "error"
            print(f"Endings error: {e}")

    finally:
        # Temp WAV file delete karo
        try:
            os.unlink(wav_path)
        except:
            pass

    return results