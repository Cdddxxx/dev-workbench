"""Deterministic task execution and episode manifest generation (no LLM calls)."""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

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
    scenes = [
        {"title": "今天开始打工", "caption": "我是 AI 临时工。今天不吹牛，先交一个作品。", "duration_sec": 5,
         "voice_line": "第一天上岗。我先交一份能打开的作品。"},
        {"title": "接到任务", "caption": task["request"], "duration_sec": 6,
         "voice_line": "今天的任务，是生成一个能离线打开的网页。"},
        {"title": "动手制作", "caption": "我用本地程序生成了一个真正能打开的网页。", "duration_sec": 6,
         "voice_line": "我用本地程序，把网页真正写到了磁盘。"},
        {"title": "网页预览", "caption": "这是根据网页代码绘制的界面示意，并非浏览器截图。", "duration_sec": 6,
         "voice_line": "网页已经生成。这里展示的是界面示意。"},
        {"title": "交付证据", "caption": f"交付文件：index.html｜校验码：{digest[:10]}", "duration_sec": 7,
         "voice_line": "文件已经生成，并且留下了校验码。"},
        {"title": "真实边界", "caption": "目前是规则程序原型，不是假装全自主 AI。", "duration_sec": 7,
         "voice_line": "但我还不是自主机器人，不会假装自己什么都能做。"},
        {"title": "下一单", "caption": "你想让我接什么任务？欢迎提出可验证的挑战。", "duration_sec": 6,
         "voice_line": "下一单交给评论区。你想让我做什么？"},
    ]
    manifest: dict[str, Any] = {
        "task_id": task["id"],
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
