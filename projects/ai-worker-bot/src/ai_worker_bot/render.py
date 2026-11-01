"""Motion-rich vertical story renderer: Pillow frames streamed to local FFmpeg.

The web preview is a *source-derived design illustration*, NOT a real browser
screenshot. Avoid making misleading claims about deployed or autonomous work.
"""
from __future__ import annotations

from functools import lru_cache
from io import BytesIO
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

from .core import srt_from_scenes
from .voice import create_audio

WIDTH, HEIGHT, FPS = 720, 1280, 15
INK = "#0c111b"
PANEL = "#182131"
ORANGE = "#ffb566"
MUTED = "#92a1b3"
WHITE = "#eef4fa"
FONT_BOLD_CHOICES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "C:/Windows/Fonts/msyh.ttc",
)
FONT_REG_CHOICES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "C:/Windows/Fonts/msyh.ttc",
)


def find_font(bold: bool = True) -> str:
    choices = FONT_BOLD_CHOICES if bold else FONT_REG_CHOICES
    for choice in choices:
        if Path(choice).is_file():
            return choice
    raise RuntimeError("No CJK font installed; cannot safely render Chinese subtitles")


@lru_cache(maxsize=40)
def _font(size: int, bold: bool = False) -> Any:
    from PIL import ImageFont
    return ImageFont.truetype(find_font(bold), size)


def wrap_text(draw: Any, text: str, font: Any, max_width: int) -> list[str]:
    """Wrap by actual pixel width rather than character count."""
    result: list[str] = []
    current = ""
    for char in text:
        test = current + char
        if current and draw.textbbox((0, 0), test, font=font)[2] > max_width:
            result.append(current)
            current = char
        else:
            current = test
    if current:
        result.append(current)
    return result


def _clamp(n: float) -> float:
    return min(1.0, max(0.0, n))


def _ease(n: float) -> float:
    n = _clamp(n)
    return 1 - (1 - n) ** 3


@lru_cache(maxsize=1)
def _background() -> Any:
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (WIDTH, HEIGHT), INK)
    d = ImageDraw.Draw(im)
    for y in range(HEIGHT):
        shade = int(8 + 8 * (1 - y / HEIGHT))
        d.line((0, y, WIDTH, y), fill=(shade, shade + 6, shade + 15))
    for x in range(34, WIDTH, 38):
        for y in range(32, HEIGHT, 38):
            d.ellipse((x, y, x + 2, y + 2), fill="#263243")
    d.ellipse((-280, 90, 540, 910), outline="#233141", width=3)
    d.ellipse((-200, 170, 460, 830), outline="#192a35", width=2)
    return im


def _text_lines(d: Any, x: int, y: int, content: str, size: int, width: int,
                color: str = WHITE, leading: int | None = None, bold: bool = False,
                max_lines: int = 5) -> int:
    font = _font(size, bold)
    lines = wrap_text(d, content, font, width)
    if len(lines) > max_lines:
        raise ValueError(f"Text cannot fit the scene ({len(lines)} lines): {content[:40]}")
    for line in lines:
        d.text((x, y), line, font=font, fill=color, stroke_width=0)
        y += leading or int(size * 1.65)
    return y


def _pill(d: Any, xy: tuple[int, int], title: str, fill: str = PANEL,
          text_color: str = ORANGE, width: int = 185) -> None:
    x, y = xy
    d.rounded_rectangle((x, y, x + width, y + 50), radius=20, fill=fill)
    d.text((x + 18, y + 10), title, font=_font(23, True), fill=text_color)


def _bot(d: Any, cx: int, cy: int, phase: float) -> None:
    bob = int(math.sin(phase * math.pi * 4) * 7)
    cy += bob
    d.ellipse((cx - 113, cy - 113, cx + 113, cy + 113), fill="#252c3b", outline=ORANGE, width=5)
    d.rounded_rectangle((cx - 85, cy - 45, cx + 85, cy + 49), radius=35, fill="#080e18", outline="#485060", width=3)
    blinking = (0.51 < phase < 0.55)
    eye_height = 4 if blinking else 21
    d.rounded_rectangle((cx - 53, cy - eye_height // 2, cx - 25, cy + eye_height // 2), radius=7, fill=ORANGE)
    d.rounded_rectangle((cx + 25, cy - eye_height // 2, cx + 53, cy + eye_height // 2), radius=7, fill=ORANGE)
    d.arc((cx - 26, cy + 8, cx + 26, cy + 54), 10, 165, fill=ORANGE, width=4)
    d.line((cx, cy - 116, cx, cy - 146), fill=ORANGE, width=5)
    d.ellipse((cx - 9, cy - 161, cx + 9, cy - 143), fill=ORANGE)


def _frame_intro(d: Any, phase: float, manifest: dict) -> None:
    _pill(d, (66, 365), f"{manifest['task_id'][:7].upper()} / 上岗", width=226)
    d.text((65, 444), "先把活", font=_font(57, True), fill=WHITE)
    d.text((65, 525), "干漂亮。", font=_font(83, True), fill=ORANGE)
    _bot(d, 510, 701, phase)
    d.text((65, 805), "工号001 · 当前岗位：临时工", font=_font(32, True), fill=WHITE)
    d.rounded_rectangle((66, 884, 654, 945), radius=16, fill=PANEL)
    d.text((88, 897), "账号未接入 · 晋升数据待验证", font=_font(25), fill=MUTED)
    if phase > 0.55:
        _text_lines(d, 70, 986, "剧情OS：老板的位子先记下。", 24, 568, ORANGE, max_lines=1)


def _frame_task(d: Any, phase: float, manifest: dict) -> None:
    _pill(d, (66, 388), "TASK / 01", width=186)
    d.text((65, 475), "甲方任务已接收", font=_font(49, True), fill=WHITE)
    d.rounded_rectangle((64, 566, 655, 819), radius=27, fill="#273344", outline="#d98b4b", width=3)
    req = manifest["task_request"]
    visible = req[:max(1, int(len(req) * _ease(phase * 1.55)))]
    _text_lines(d, 98, 611, visible, 38, 518, max_lines=4)
    # A timed inner conflict -> self-persuasion -> visible customer-service smile.
    # These are clearly labeled fictional OS beats; no fan comment was fetched.
    if phase >= 0.27:
        _text_lines(d, 72, 835, "剧情OS：" + manifest["scenes"][1].get("inner_os", ""),
                    23, 565, ORANGE, max_lines=2, leading=34)
    if phase >= 0.48:
        _text_lines(d, 72, 899, manifest["scenes"][1].get("self_persuasion", ""),
                    24, 550, MUTED, max_lines=2, leading=31)
    if phase >= 0.70:
        d.rounded_rectangle((66, 962, 655, 1040), radius=24, fill="#2c4351", outline=ORANGE, width=2)
        d.text((85, 984), "营业笑脸：谢谢甲方赐题！我来！", font=_font(23, True), fill=WHITE)
        # Smile icon appears only after the character has chosen to act nicely.
        d.ellipse((592, 975, 637, 1020), fill=ORANGE)
        d.ellipse((603, 988, 607, 992), fill=INK)
        d.ellipse((621, 988, 625, 992), fill=INK)
        d.arc((604, 987, 627, 1011), 12, 165, fill=INK, width=2)


def _frame_build(d: Any, phase: float, manifest: dict) -> None:
    _pill(d, (65, 386), "BUILD / 02", width=198)
    d.text((65, 460), "真正执行，而不是吹", font=_font(47, True), fill=WHITE)
    steps = [
        ("01", "读取任务 JSON", "有效输入 · 本地"),
        ("02", "写入 index.html", "独立 HTML 文件"),
        ("03", "计算 SHA-256", "保留可核对校验码"),
    ]
    for i, (no, title, detail) in enumerate(steps):
        y = 572 + i * 145
        active = phase > (i + 0.5) / 4
        d.rounded_rectangle((64, y, 656, y + 125), radius=24, fill="#223345" if active else "#1a2433", outline=ORANGE if active else "#3d4c5b", width=3)
        d.text((89, y + 21), no, font=_font(37, True), fill=ORANGE if active else MUTED)
        d.text((161, y + 13), title, font=_font(31, True), fill=WHITE)
        d.text((161, y + 68), detail, font=_font(24), fill=MUTED)
        if active:
            d.text((590, y + 40), "✓", font=_font(35, True), fill=ORANGE)
    d.text((78, 1022), "程序生成 · 无外部 API 调用", font=_font(24), fill=MUTED)


def _frame_preview(d: Any, phase: float, manifest: dict) -> None:
    _pill(d, (65, 354), "DELIVER / 03", width=233)
    d.text((65, 422), "网页，真的写出来了", font=_font(47, True), fill=WHITE)
    # This artwork is *not* an actual screenshot. It is deliberately labeled.
    offset = int((1 - _ease(phase * 2)) * 55)
    top = 525 + offset
    d.rounded_rectangle((75, top, 645, top + 467), radius=26, fill="#20242f", outline="#687182", width=3)
    d.rounded_rectangle((75, top, 645, top + 73), radius=26, fill="#383b49")
    d.rectangle((75, top + 43, 645, top + 73), fill="#383b49")
    for i, fill in enumerate(("#fb7b77", "#fbc65f", "#65c389")):
        d.ellipse((101 + i * 24, top + 22, 113 + i * 24, top + 34), fill=fill)
    d.rounded_rectangle((102, top + 100, 392, top + 143), radius=16, fill=ORANGE)
    d.text((119, top + 106), f"{manifest['task_id'][:7].upper()} · 本地交付", font=_font(20, True), fill=INK)
    _text_lines(d, 105, top + 173, manifest["project_name"], 51, 489, bold=True, max_lines=2)
    d.text((105, top + 305), "接真实任务", font=_font(32), fill=WHITE)
    d.text((105, top + 359), "交真实作品", font=_font(32), fill=ORANGE)
    d.text((70, 1020), "* 基于交付源码的界面示意，非浏览器实录", font=_font(21), fill=MUTED)


def _frame_proof(d: Any, phase: float, manifest: dict) -> None:
    _pill(d, (66, 382), "PROOF / 04", width=190)
    d.text((65, 456), "有成果，就留证据", font=_font(47, True), fill=WHITE)
    d.rounded_rectangle((66, 553, 655, 918), radius=25, fill="#111821", outline="#55647c", width=3)
    digest = manifest["deliverable_sha256"]
    lines = [
        "[OK] deliverable/index.html",
        "[OK] 本地文件已写入",
        f"SHA-256  {digest[:14]}",
        "[INFO] 尚未上线发布",
    ]
    for i, line in enumerate(lines):
        if phase < 0.13 + i * 0.19:
            break
        d.text((93, 599 + i * 72), line, font=_font(27), fill=ORANGE if i < 3 else MUTED)
    d.text((78, 981), "不是展示概念图，而是留下文件校验码", font=_font(24), fill=MUTED)


def _frame_truth(d: Any, phase: float, manifest: dict) -> None:
    _pill(d, (65, 386), "HONEST / 05", width=222)
    d.text((65, 456), "不包装成全自动", font=_font(55, True), fill=WHITE)
    facts = [
        ("已完成", "本地程序生成网页", "#4fd1ac"),
        ("尚未", "AI 自主规划与记忆", "#f5b86e"),
        ("尚未", "抖音自动发布 / 回评", "#f5b86e"),
    ]
    for i, (status, thing, color) in enumerate(facts):
        if phase < 0.14 + i * 0.2:
            break
        y = 578 + i * 130
        d.rounded_rectangle((72, y, 645, y + 104), radius=23, fill=PANEL)
        d.text((91, y + 26), status, font=_font(24, True), fill=color)
        d.text((195, y + 26), thing, font=_font(27), fill=WHITE)
    d.text((85, 1011), "用事实打工，不靠人设编数据。", font=_font(24), fill=MUTED)


def _frame_next(d: Any, phase: float, manifest: dict) -> None:
    _bot(d, 360, 525, phase)
    d.text((65, 738), "下一单，", font=_font(68, True), fill=WHITE)
    d.text((65, 826), "评论区出题。", font=_font(64, True), fill=ORANGE)
    _pill(d, (70, 941), "真实任务 / 真实交付", fill="#26394c", text_color=WHITE, width=302)


def draw_frame(manifest: dict[str, Any], scene_idx: int, progress: float,
               scene_count: int) -> Any:
    """Return a self-contained visual frame; can be unit-tested with Pillow."""
    from PIL import Image, ImageDraw
    progress = _clamp(progress)
    im = _background().copy()
    d = ImageDraw.Draw(im)
    d.text((51, 68), "AI / 临时工", font=_font(34, True), fill=ORANGE)
    d.text((485, 77), f"{manifest['task_id'][:9].upper()} · LOCAL", font=_font(18), fill=MUTED)
    d.line((51, 142, 669, 142), fill="#455265", width=3)
    d.rounded_rectangle((55, 163, 665, 176), radius=6, fill="#2d3d51")
    d.rounded_rectangle((55, 163, 55 + int(610 * (scene_idx + progress) / scene_count), 176), radius=6, fill=ORANGE)
    d.text((52, 214), f"{scene_idx + 1:02d} / {scene_count:02d}", font=_font(23, True), fill=MUTED)

    scenes = [_frame_intro, _frame_task, _frame_build, _frame_preview, _frame_proof, _frame_truth, _frame_next]
    if scene_count != 7 or not 0 <= scene_idx < scene_count:
        raise ValueError("M1 renderer supports the 7 verified scene layouts only")
    scenes[scene_idx](d, progress, manifest)

    # Consistent safe-area subtitles below content; content ends before 1050.
    d.rounded_rectangle((36, 1061, 684, 1224), radius=26, fill="#101b2a", outline="#3b4b5e", width=2)
    caption = manifest["scenes"][scene_idx]["caption"]
    _text_lines(d, 68, 1090, caption, 32, 585, WHITE, leading=48, bold=True, max_lines=2)
    d.text((54, 1245), "真实执行记录  ·  尚未发布", font=_font(18), fill=MUTED)

    # Short scene-to-scene fade, without hiding the subtitle for the whole scene.
    fade = min(1.0, progress / 0.10, (1.0 - progress) / 0.09)
    if fade < 0.995:
        veil = Image.new("RGB", (WIDTH, HEIGHT), INK)
        im = Image.blend(veil, im, max(0.0, fade))
    return im


def render_episode(output: Path, voice: bool = False) -> Path:
    """Render dynamic MP4; optional local eSpeak narration, never paid API."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg not found; install the free binary and retry --render")
    find_font()
    manifest_path = output / "episode.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenes = manifest["scenes"]
    if len(scenes) != 7:
        raise ValueError("M1 renderer requires 7 verified scene types")
    with tempfile.TemporaryDirectory(prefix="ai-worker-render-") as folder:
        temp = Path(folder)
        plan = create_audio(scenes, temp) if voice else None
        durations = plan.durations if plan else [int(s["duration_sec"]) for s in scenes]
        if any(n < 2 or n > 30 for n in durations):
            raise ValueError("Invalid scene duration: needs 2–30 seconds")
        result = output / "episode.mp4"
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "image2pipe",
               "-framerate", str(FPS), "-vcodec", "mjpeg", "-i", "pipe:0"]
        if plan:
            cmd.extend(["-i", str(plan.wav_path)])
        cmd.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                    "-pix_fmt", "yuv420p"])
        if plan:
            cmd.extend(["-c:a", "aac", "-b:a", "96k"])
        else:
            cmd.extend(["-an"])
        cmd.extend(["-movflags", "+faststart", str(result)])
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            frame_index = 0
            for index, duration in enumerate(durations):
                for i in range(duration * FPS):
                    pic = draw_frame(manifest, index, i / (duration * FPS), len(scenes))
                    image = BytesIO()
                    pic.save(image, format="JPEG", quality=86, subsampling=0)
                    if process.stdin is None:
                        raise RuntimeError("FFmpeg video pipe closed unexpectedly")
                    process.stdin.write(image.getvalue())
                    frame_index += 1
            if process.stdin is not None:
                process.stdin.close()
            if process.stderr is None:
                raise RuntimeError("FFmpeg stderr unavailable")
            errors = process.stderr.read().decode("utf-8", errors="replace")
            exitcode = process.wait(timeout=180)
            if exitcode:
                raise RuntimeError(f"FFmpeg failed ({exitcode}): {errors[-2000:]}")
        except BaseException:
            if process.poll() is None:
                process.kill()
            process.wait()
            result.unlink(missing_ok=True)
            raise
        # Only persist render metadata after video creation actually succeeded.
        manifest["render"] = {
            "engine": "pillow-motion-ffmpeg",
            "fps": FPS,
            "width": WIDTH,
            "height": HEIGHT,
            "duration_sec": sum(durations),
            "audio": plan.engine if plan else "none",
            "preview_type": "source-derived-illustration-not-browser-screenshot",
            "human_visual_review_pending": True,
            "frames": frame_index,
        }
        manifest["scenes"] = [dict(s, duration_sec=d) for s, d in zip(scenes, durations)]
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (output / "captions.srt").write_text(srt_from_scenes(manifest["scenes"]), encoding="utf-8")
        with (output / "WORKLOG.md").open("a", encoding="utf-8") as log:
            log.write(f"\n- 视频渲染实际完成：{sum(durations)} 秒，{frame_index} 帧，音频：{manifest['render']['audio']}。\n")
            log.write("- 画面里的网页是基于源码的界面示意，不是浏览器实际截图；仍需真实设备验收。\n")
        return result
