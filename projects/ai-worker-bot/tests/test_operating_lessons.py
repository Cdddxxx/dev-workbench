"""Dataset integrity only. Passing is NOT model or platform behavior validation."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OperatingLessonsSchemaTests(unittest.TestCase):
    def test_cases_are_unique_and_manually_evaluable(self):
        data = json.loads((ROOT / "examples/evaluations/operating-lessons.json").read_text())
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["execution_status"], "not_run")
        self.assertEqual(data["purpose"], "human_review_regression_cases_not_model_training")
        ids = []
        for case in data["cases"]:
            self.assertIsInstance(case["scenario"], str)
            self.assertTrue(case["scenario"].strip())
            ids.append(case["id"])
            for field in ("expected", "failure_conditions", "required_evidence"):
                self.assertIsInstance(case[field], list)
                self.assertTrue(case[field])
                self.assertTrue(all(isinstance(x, str) and x.strip() for x in case[field]))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 10)

    def test_handoff_requires_lessons_and_explains_limits(self):
        self.assertIn("OPERATING_LESSONS.md", (ROOT / "docs/CODEX_HANDOFF.md").read_text())
        self.assertIn("OPERATING_LESSONS.md", (ROOT / "AGENTS.md").read_text())
        text = (ROOT / "docs/OPERATING_LESSONS.md").read_text()
        self.assertIn("不是模型训练", text)
        self.assertIn("昵称尚未批准", text)
