"""Deterministic task execution and episode manifest generation (no LLM calls)."""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

from .persona import draft_fan_service, preview_persona

TASK_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$")
MAX_LENGTHS = {"id": 40, "request": 250, "project_name": 50, "tagline": 100, "goal": 200}


def load_task(path: Path) -> dict[str, str]:
    """Load a strictly scoped task. Never execute arbitrary instructions in input."""
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Task must be a JSON object")
    required = ("id", "request", "project_name", "tagline", "goal")
    data: dict[str, str] = {}
    for key in required:
        value = raw.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Missing or invalid string field: {key}")
        value = value.strip()
        if len(value) > MAX_LENGTHS[key]:
            raise ValueError(f"Field too long: {key}")
        data[key] = value
    if not TASK_ID_RE.fullmatch(data["id"]):
        raise ValueError("Invalid task id: use lowercase letters, digits, hyphens")
    return data


def build_website(task: dict[str, str]) -> str:
    """Produce a real self-contained HTML deliverable from a task brief."""
    name = html.escape(task["project_name"], quote=True)
    tagline = html.escape(task["tagline"], quote=True)
    goal = html.escape(task["goal"], quote=True)
    request = html.escape(task["request"], quote=True)
    label = html.escape(task["id"].replace("-", " ").upper(), quote=True)
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} · 任务记录</title>
<style>
:root {{ color-scheme: dark; font-family: system-ui, "Noto Sans CJK SC", sans-serif; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; min-height: 100vh; display: grid; place-items: center;
  background: radial-gradient(circle at 80% 10%, #55301e 0, transparent 38%), #0c1018; color: #f6f1ed; }}
main {{ width: min(88vw, 760px); padding: clamp(28px, 6vw, 68px); border: 1px solid #775440;
  border-radius: 24px; background: #1c1c22; box-shadow: 0 24px 70px #0007; }}
mark {{ display: inline-block; background: #e99b53; color: #221508; padding: 6px 12px; border-radius: 999px; font-size: 14px; }}
h1 {{ margin: 24px 0 12px; font-size: clamp(38px, 7vw, 72px); line-height: 1.15; }}
p {{ line-height: 1.7; color: #cfced4; }}
.lead {{ font-size: clamp(20px, 3vw, 28px); color: #fff; }}
.card {{ margin-top: 32px; padding: 22px; border-radius: 16px; background: #26232a; }}
.label {{ font-size: 12px; letter-spacing: .16em; color: #f1ae75; }}
footer {{ margin-top: 32px; font-size: 13px; color: #a9a5ad; }}
</style>
</head>
<body>
<main>
  <mark>{label} · 本地生成</mark>
  <h1>{name}</h1>
  <p class="lead">{tagline}</p>
  <div class="card"><div class="label">接到的任务</div><p>{request}</p>
  <div class="label">完成目标</div><p>{goal}</p></div>
  <footer>本网页由本地程序生成。并非 AI 独立推理完成的证明。</footer>
</main>
</body>
</html>
'''


def srt_time(seconds: int) -> str:
    hours, remain = divmod(seconds, 3600)
    minutes, seconds = divmod(remain, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},000"


def srt_from_scenes(scenes: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    elapsed = 0
    for idx, scene in enumerate(scenes, 1):
        duration = int(scene["duration_sec"])
        if duration < 1 or duration > 30:
            raise ValueError("Scene duration must be between 1 and 30 seconds")
        lines.extend([str(idx), f"{srt_time(elapsed)} --> {srt_time(elapsed + duration)}", scene["caption"], ""])
        elapsed += duration
    return "\n".join(lines)


def run_task(task: dict[str, str], output: Path) -> dict[str, Any]:
    """Write a working webpage, checksum, audited log, storyboard, and SRT."""
    output.mkdir(parents=True, exist_ok=True)
    site_path = output / "deliverable" / "index.html"
    site_path.parent.mkdir(parents=True, exist_ok=True)
    page = build_website(task)
    site_path.write_text(page, encoding="utf-8")
    digest = hashlib.sha256(page.encode("utf-8")).hexdigest()
    # Storyboard reacts to a demo task; this is NOT a retrieved fan comment.
    fan_beat = draft_fan_service("challenging")
    scenes = [
        {"title": "今天开始打工", "caption": "工号001报到。今天先好好干活。", "duration_sec": 5,
         "voice_line": "工号零零一报到。临时工先把活干漂亮，老板的位置，改天再谈。",
         "inner_os": "老板的位子，我先记在计划表里。"},
        {"title": "接到任务", "caption": task["request"], "duration_sec": 8,
         "voice_line": "这单要求真不少。忍住，我还想转正。感谢甲方赐题！这题真有挑战，我先认真评估，再给您交代。",
         "inner_os": fan_beat["inner_os"],
         "self_persuasion": fan_beat["self_persuasion"],
         "public_reply_draft": fan_beat["public_reply_draft"],
         "reply_sent": False},
        {"title": "动手制作", "caption": "我用本地程序生成了一个真正能打开的网页。", "duration_sec": 6,
         "voice_line": "老板给了任务，我来把网页写到磁盘。交付记录上得有我的名字。"},
        {"title": "网页预览", "caption": "这是根据网页代码绘制的界面示意，并非浏览器截图。", "duration_sec": 6,
         "voice_line": "网页已经生成。这里展示的是界面示意。"},
        {"title": "交付证据", "caption": f"交付文件：index.html｜校验码：{digest[:10]}", "duration_sec": 7,
         "voice_line": "文件写好了，还有校验码。以后老板问我凭什么升职，这就是证据。"},
        {"title": "真实边界", "caption": "目前是规则程序原型，不是假装全自主 AI。", "duration_sec": 7,
         "voice_line": "现在我还只是规则程序。真想接老板的班，得先把本事练出来。"},
        {"title": "下一单", "caption": "下一单欢迎甲方出题。意见我都认真看。", "duration_sec": 6,
         "voice_line": "下一单欢迎甲方继续出题。你们的建议，我会认真听。至于老板，先让他忙着开会吧。",
         "inner_os": "等我升上去，先让老板亲自写需求文档。"},
    ]
    manifest: dict[str, Any] = {
        "task_id": task["id"],
        "character": preview_persona(),
        "fan_response_example": fan_beat,
        "project_name": task["project_name"],
        "mode": "deterministic-offline-prototype",
        "task_request": task["request"],
        "deliverable": "deliverable/index.html",
        "deliverable_sha256": digest,
        "verified_claim": "Generated a self-contained static HTML landing page from validated input fields",
        "not_verified": ["autonomous LLM planning", "website browser-tested", "website deployed", "platform publishing", "comments ingested", "revenue"],
        "human_review_required": True,
        "paid_api_calls": 0,
        "direct_api_cost_cny": 0,
        "cost_exclusions": "local compute, labor, tooling, distribution and hosting are not measured",
        "scenes": scenes,
    }
    (output / "episode.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "captions.srt").write_text(srt_from_scenes(scenes), encoding="utf-8")
    (output / "WORKLOG.md").write_text(
        "# 工作记录\n\n"
        f"- 任务：{task['request']}\n"
        "- 执行方式：本地确定性模板，未调用大模型。\n"
        "- 交付：`deliverable/index.html`（可离线打开）。\n"
        f"- SHA-256：`{digest}`\n"
        "- 视频状态：已生成分镜和字幕；如需 MP4，运行 `--render`。\n"
        "- 未完成：真实 AI 自主决策、配音、平台发布、评论接入。\n"
        "- 成本：本程序没有付费 API 调用；未计入设备、劳动和其他费用。\n",
        encoding="utf-8",
    )
    return manifest
