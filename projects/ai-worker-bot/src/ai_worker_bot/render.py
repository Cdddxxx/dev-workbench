"""Optional local vertical MP4 renderer: Pillow + FFmpeg, no paid services."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

WIDTH, HEIGHT = 720, 1280


def find_font() -> str:
    """Choose a local font with CJK glyphs; explicit failure prevents blank subtitles."""
    choices = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for file in choices:
        if Path(file).is_file():
            return file
    raise RuntimeError("No compatible CJK font found; install a Chinese font or add its path to find_font()")


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


def make_frame(path: Path, scene: dict[str, Any], idx: int, total: int, font_path: str) -> None:
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (WIDTH, HEIGHT), "#0d0d12")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((30, 90, 690, 1190), radius=36, fill="#1c1a1f", outline="#7f4d2c", width=3)
    draw.rounded_rectangle((70, 135, 430, 194), radius=24, fill="#f4a45e")
    brand_font = ImageFont.truetype(font_path, 26)
    draw.text((98, 148), "AI 临时工 / DAY 01", font=brand_font, fill="#1a1009")
    headline = ImageFont.truetype(font_path, 54)
    body = ImageFont.truetype(font_path, 44)
    detail = ImageFont.truetype(font_path, 28)
    draw.text((75, 275), scene["title"], font=headline, fill="#f0b280")
    lines = wrap_text(draw, scene["caption"], body, 560)
    if len(lines) > 8:
        raise ValueError("Scene too long to display; shorten text before rendering")
    y = 440
    for line in lines:
        draw.text((75, y), line, font=body, fill="#ffffff")
        y += 76
    draw.line((75, 1040, 645, 1040), fill="#5a4440", width=3)
    draw.text((75, 1070), "真实工作记录 · 首版无配音", font=detail, fill="#a6a3af")
    draw.text((535, 1070), f"{idx:02d} / {total:02d}", font=detail, fill="#f0b280")
    image.save(path)


def render_episode(output: Path) -> Path:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg not found; install it and retry --render")
    font_path = find_font()
    manifest = json.loads((output / "episode.json").read_text(encoding="utf-8"))
    scenes = manifest["scenes"]
    with tempfile.TemporaryDirectory(prefix="ai-worker-") as folder:
        work = Path(folder)
        concat_lines: list[str] = []
        for i, scene in enumerate(scenes, 1):
            png = work / f"scene-{i:02d}.png"
            make_frame(png, scene, i, len(scenes), font_path)
            concat_lines.extend([f"file '{png.as_posix()}'", f"duration {int(scene['duration_sec'])}"])
        # FFmpeg concat demuxer needs a repeated final frame to honor the final duration.
        concat_lines.append(f"file '{png.as_posix()}'")
        frames_txt = work / "frames.txt"
        frames_txt.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")
        result = output / "episode.mp4"
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-safe", "0", "-f", "concat",
            "-i", str(frames_txt), "-vsync", "vfr", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(result),
        ]
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if completed.returncode:
            raise RuntimeError(f"FFmpeg exited with {completed.returncode}: {completed.stderr.strip()}")
    return result
