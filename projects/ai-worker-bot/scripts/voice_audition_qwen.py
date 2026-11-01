"""Opt-in, offline-by-default audition of a manually provided Qwen3-TTS model.

Requires explicit local model files and dependencies. No API calls or model
weights are fetched by this script. The generated audio is NOT quality-approved.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Avoid importing ai_worker_bot until sys.path includes a local source checkout.
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from ai_worker_bot.voice_profile import audition_plan  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Create 3 Mandarin voice audition WAVs from a local Qwen3-TTS model")
    parser.add_argument("--model-dir", type=Path, required=True, help="Existing local model directory; never auto-download")
    parser.add_argument("--output", type=Path, default=PROJECT / "output" / "voice-audition")
    args = parser.parse_args()
    if not args.model_dir.is_dir() or not (args.model_dir / "config.json").exists():
        parser.error("--model-dir needs a previously downloaded model directory with config.json")
    try:
        import torch
        import soundfile as sf
        from qwen_tts import Qwen3TTSModel
    except ImportError as exc:
        parser.error(f"optional dependencies absent: {exc}. Install qwen-tts, soundfile, torch explicitly.")

    plan = audition_plan()
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device != "cpu" else torch.float32
    model = Qwen3TTSModel.from_pretrained(str(args.model_dir.resolve()), device_map=device, dtype=dtype)
    args.output.mkdir(parents=True, exist_ok=True)
    for take in plan["takes"]:
        waves, sample_rate = model.generate_custom_voice(
            text=take["sample"], speaker=plan["speaker"],
            language=plan["language"], instruct=take["direction"],
        )
        sf.write(str(args.output / (take["key"] + ".wav")), waves[0], sample_rate)
    (args.output / "audition-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(f"Three WAV auditions written to {args.output}; quality approval is pending human listening.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
