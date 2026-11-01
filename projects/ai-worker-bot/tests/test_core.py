import json
import tempfile
import unittest
from pathlib import Path

from ai_worker_bot.core import build_website, load_task, run_task, srt_from_scenes
from ai_worker_bot.render import wrap_text


class TaskTests(unittest.TestCase):
    def sample(self):
        return {
            "id": "day-001",
            "request": "做一个网页",
            "project_name": "AI 临时工",
            "tagline": "真正交付",
            "goal": "可离线打开",
        }

    def test_build_site_escapes_untrusted_fields(self):
        task = self.sample()
        task["project_name"] = '<img src=x onerror="alert(1)">'
        result = build_website(task)
        self.assertIn("&lt;img", result)
        self.assertNotIn('<img src=x', result)

    def test_reject_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "input.json"
            task = self.sample()
            task["id"] = "../../bad"
            file.write_text(json.dumps(task), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_task(file)

    def test_reject_invalid_input_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "input.json"
            file.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_task(file)

    def test_real_deliverable_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = run_task(self.sample(), root)
            self.assertTrue((root / "deliverable" / "index.html").exists())
            self.assertTrue((root / "captions.srt").exists())
            self.assertEqual(manifest["mode"], "deterministic-offline-prototype")
            self.assertEqual(manifest["paid_api_calls"], 0)
            self.assertEqual(manifest["character"]["persona_version"], "0.3")
            self.assertEqual(manifest["character"]["growth"]["code"], "L0")
            self.assertIsNone(manifest["character"]["growth"]["followers"])
            self.assertFalse(manifest["fan_response_example"]["reply_sent"])
            self.assertFalse(manifest["fan_response_example"]["real_comment_received"])
            self.assertIn("笑脸", manifest["fan_response_example"]["sequence"][2])
            self.assertIn("内心", manifest["fan_response_example"]["sequence"][0])
            self.assertIn("甲方", manifest["scenes"][1]["public_reply_draft"])
            self.assertEqual(len(manifest["deliverable_sha256"]), 64)
            total = sum(scene["duration_sec"] for scene in manifest["scenes"])
            self.assertEqual(total, 45)
            self.assertIn("00:00:45,000", (root / "captions.srt").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["scenes"]), 7)
            self.assertTrue(all("voice_line" in x for x in manifest["scenes"]))

    def test_srt_durations_checked(self):
        with self.assertRaises(ValueError):
            srt_from_scenes([{"caption": "x", "duration_sec": 0}])

    def test_wrap_scene_text(self):
        # lightweight text measurement stub, independent from Pillow
        class DummyDraw:
            def textbbox(self, xy, text, font):
                return (0, 0, len(text) * 10, 12)
        self.assertEqual(wrap_text(DummyDraw(), "ABCDE", None, 20), ["AB", "CD", "E"])


if __name__ == "__main__":
    unittest.main()
