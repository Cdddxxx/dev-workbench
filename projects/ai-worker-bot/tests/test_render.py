"""Renderer and narration boundary tests. No paid API calls or GUI required."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_worker_bot.core import run_task
from ai_worker_bot.render import draw_frame
from ai_worker_bot.voice import create_audio


class RenderingTests(unittest.TestCase):
    def sample(self):
        return {"id": "day-002", "request": "做一个离线展示页面", "project_name": "第二期",
                "tagline": "不依赖云端 API", "goal": "落地到 index.html"}

    def test_all_seven_scenes_draw_at_multiple_times(self):
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("Pillow optional render dependency not installed")
        with tempfile.TemporaryDirectory() as tmp:
            manifest = run_task(self.sample(), Path(tmp))
            for i in range(7):
                for position in (0, 0.5, 0.95):
                    frame = draw_frame(manifest, i, position, 7)
                    self.assertEqual(frame.size, (720, 1280))
            before = draw_frame(manifest, 1, 0.1, 7).tobytes()
            after = draw_frame(manifest, 1, 0.9, 7).tobytes()
            self.assertNotEqual(before, after, "Task scene must really animate")

    def test_preview_is_explicitly_not_browser_screenshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = run_task(self.sample(), Path(tmp))
            self.assertIn("website browser-tested", manifest["not_verified"])
            self.assertIn("界面示意", manifest["scenes"][3]["caption"])

    def test_voice_has_no_silent_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = run_task(self.sample(), Path(tmp))
            with patch("ai_worker_bot.voice.shutil.which", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "requires.*espeak"):
                    create_audio(manifest["scenes"], Path(tmp))

    @unittest.skipUnless(shutil.which("espeak"), "eSpeak not installed")
    def test_espeak_creates_synchronized_scene_lengths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = run_task(self.sample(), root)
            audio = create_audio(manifest["scenes"], root)
            self.assertGreater(audio.wav_path.stat().st_size, 2000)
            self.assertEqual(len(audio.durations), 7)
            self.assertTrue(all(d >= s["duration_sec"] for d, s in zip(audio.durations, manifest["scenes"])))
            self.assertEqual(audio.engine, "espeak-zh-offline")


if __name__ == "__main__":
    unittest.main()
