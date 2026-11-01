"""Command-line entry point for the local prototype."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import load_task, run_task


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI 临时工：离线任务→网页交付→视频分镜")
    parser.add_argument("task", type=Path, help="JSON task file")
    parser.add_argument("--output", type=Path, default=Path("output/day-001"))
    parser.add_argument("--render", action="store_true", help="also render a silent vertical MP4 with FFmpeg + Pillow")
    args = parser.parse_args(argv)
    try:
        task = load_task(args.task)
        manifest = run_task(task, args.output)
        print(f"Created webpage, storyboard, subtitles and log in {args.output}")
        print(f"SHA256: {manifest['deliverable_sha256']}")
        if args.render:
            from .render import render_episode

            video = render_episode(args.output)
            print(f"Rendered silent MP4: {video}")
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
