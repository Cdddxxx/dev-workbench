"""Release candidate character voice: clear Chinese, one speaker, three moods.

Profile is an audition plan, not evidence the selected TTS model has run.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
SPEAKER = "Dylan"  # youthful Beijing Chinese voice; subject to human audition


@dataclass(frozen=True)
class VoiceTake:
    key: Literal["work", "inner_os", "service_smile"]
    sample: str
    direction: str


TAKES = (
    VoiceTake(
        "work",
        "工号零零一。今天先把我的头像定下来。老板说，形象要稳重。",
        "清晰的普通话，年轻男声，自然、克制、一本正经。适度停顿，不要机械播报。",
    ),
    VoiceTake(
        "inner_os",
        "稳重？等我升职了，我先给老板重新设计一个头像。",
        "同一个人声，轻微压低音量，自言自语，略带坏笑和腹黑吐槽，字要清楚。",
    ),
    VoiceTake(
        "service_smile",
        "当然啦！各位甲方的建议，我都会认真考虑。谢谢支持！",
        "同一个人声，微笑服务，热情稍夸张但不过分尖锐，咬字清晰，像真人说话。",
    ),
)


def audition_plan() -> dict[str, object]:
    return {
        "model": MODEL_ID,
        "speaker": SPEAKER,
        "language": "Chinese",
        "status": "UNTESTED_REQUIRES_LOCAL_MODEL_AND_HUMAN_LISTENING",
        "takes": [asdict(x) for x in TAKES],
        "legacy_espeak_release_allowed": False,
    }
