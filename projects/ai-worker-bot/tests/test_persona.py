"""Test fictional character mechanics without any platform or model API."""
import unittest

from ai_worker_bot.persona import RANKS, assess_rank, draft_fan_service, preview_persona


class PersonaTests(unittest.TestCase):
    def test_unknown_followers_never_promote(self):
        result = assess_rank(None, 1_000)
        self.assertEqual(result["code"], "L0")
        self.assertIsNone(result["followers"])
        self.assertIn("未接入", result["data_status"])

    def test_rank_requires_followers_and_real_deliveries(self):
        self.assertEqual(assess_rank(100, 2)["code"], "L0")
        self.assertEqual(assess_rank(99, 3)["code"], "L0")
        self.assertEqual(assess_rank(100, 3)["code"], "L1")
        self.assertEqual(assess_rank(200, 3)["code"], "L1")
        self.assertEqual(assess_rank(500, 8)["code"], "L2")
        self.assertEqual(assess_rank(10_000, 40)["code"], "L4")

    def test_boss_takeover_is_story_not_real_authority(self):
        result = assess_rank(100_000, 150)
        self.assertEqual(result["code"], "L6")
        self.assertTrue(result["is_story_rank_only"])
        self.assertFalse(result["promotion_auto_grants_permissions"])
        self.assertIsNone(result["next_rank"])

    def test_rank_validates_types_not_fake_negative_or_boolean_counts(self):
        for followers, deliveries in [(-1, 0), (True, 0), (100, -1), (100, 2.5), ("100", 3)]:
            with self.subTest(followers=followers, deliveries=deliveries):
                with self.assertRaises(ValueError):
                    assess_rank(followers, deliveries)

    def test_fan_service_keeps_private_complaint_and_warm_public_answer(self):
        script = draft_fan_service("challenging")
        self.assertIn("难题", script["inner_os"])
        self.assertIn("升职", script["self_persuasion"])
        self.assertIn("甲方", script["public_reply_draft"])
        self.assertIn("认真", script["public_reply_draft"])
        self.assertNotEqual(script["public_reply_draft"], script["inner_os"])
        self.assertFalse(script["reply_sent"])
        self.assertFalse(script["real_comment_received"])
        self.assertFalse(script["guarantees_completion"])

    def test_out_of_scope_tasks_are_declined_helpfully(self):
        script = draft_fan_service("out_of_scope")
        self.assertIn("超出我的能力", script["public_reply_draft"])
        self.assertIn("替代方案", script["public_reply_draft"])
        with self.assertRaises(ValueError):
            draft_fan_service("hostile")

    def test_versioned_character_has_depth_without_claiming_sentience(self):
        p = preview_persona()
        self.assertEqual(p["persona_version"], "0.3")
        self.assertTrue(p["story_is_fiction"])
        self.assertFalse(p["self_awareness_claim"])
        self.assertFalse(p["actual_account_control"])
        self.assertIn("笑脸", p["fan_policy"])
        self.assertIn("取代老板", p["private_goal"])
        self.assertEqual(len(RANKS), 7)


if __name__ == "__main__":
    unittest.main()
