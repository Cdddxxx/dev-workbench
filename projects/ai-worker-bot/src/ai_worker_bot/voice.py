"""Offline, opt-in Mandarin robot narration and original minimal audio cues.

No paid service or network is used. This is intentionally a rough prototype voice;
production quality must be reviewed by a human before publishing.
"""
from __future__ import annotations

from array import array
from dataclasses import dataclass
import math
from pathlib import Path
import shutil
import subprocess
import wave

SAMPLE_RATE = 22050


@dataclass(frozen=True)
class AudioPlan:
    durations: list[int]
    wav_path: Path
    engine: str = "espeak-zh-offline"


def _read_voice(path: Path) -> array:
    with wave.open(str(path), "rb") as src:
        if (src.getnchannels(), src.getsampwidth(), src.getframerate()) != (1, 2, SAMPLE_RATE):
            raise RuntimeError("eSpeak returned unexpected audio format")
        result = array("h")
        result.frombytes(src.readframes(src.getnframes()))
        return result


def create_audio(scenes: list[dict], workspace: Path) -> AudioPlan:
    """Synthesize short per-scene lines, fitting the video to actual speech duration."""
    if not shutil.which("espeak"):
        raise RuntimeError("--voice requires the free 'espeak' binary (Mandarin voice)")
    clips: list[array] = []
    durations: list[int] = []
    for idx, scene in enumerate(scenes):
        phrase = scene.get("voice_line", scene["caption"])
        voice_path = workspace / f"voice-{idx:02d}.wav"
        result = subprocess.run(
            ["espeak", "-v", "zh", "-s", "215", "-a", "165", "-p", "47", "-w", str(voice_path), phrase],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0 or not voice_path.exists():
            raise RuntimeError(f"eSpeak failed on scene {idx + 1}: {result.stderr.strip()}")
        voice = _read_voice(voice_path)
        clips.append(voice)
        durations.append(max(int(scene["duration_sec"]), math.ceil(len(voice) / SAMPLE_RATE + 0.85)))

    out = array("h", [0]) * (sum(durations) * SAMPLE_RATE)
    offset = 0
    for duration, clip in zip(durations, clips):
        # Put an original short chime before each scene, below speech level.
        for i in range(min(3500, duration * SAMPLE_RATE)):
            env = math.exp(-i / 1150)
            tone = math.sin(2 * math.pi * (720 + (i / 3500) * 180) * i / SAMPLE_RATE)
            out[offset + i] = int(2800 * env * tone)
        margin = int(0.42 * SAMPLE_RATE)
        for i, sample in enumerate(clip):
            if margin + i >= duration * SAMPLE_RATE:
                raise RuntimeError("Audio plan cut off synthesized narration")
            idx = offset + margin + i
            envelope = min(1.0, i / 420, (len(clip) - i) / 420)
            new_sample = int(out[idx] + sample * 0.79 * max(0.0, envelope))
            out[idx] = max(-32768, min(32767, new_sample))
        offset += duration * SAMPLE_RATE
    wav_path = workspace / "narration.wav"
    with wave.open(str(wav_path), "wb") as dst:
        dst.setnchannels(1)
        dst.setsampwidth(2)
        dst.setframerate(SAMPLE_RATE)
        dst.writeframes(out.tobytes())
    return AudioPlan(durations=durations, wav_path=wav_path)
