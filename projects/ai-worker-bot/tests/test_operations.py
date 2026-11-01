"""Gates prevent story-driven content from masquerading as approved social posts."""
import unittest
from dataclasses import replace
from ai_worker_bot.operations import (
    CommentSource, PublicationReview, PublicationTarget, WorkflowState,
    create_unsent_reply_draft, publication_blockers, transition,
)
from ai_worker_bot.voice_profile import audition_plan


class OperationsTests(unittest.TestCase):
    def approved(self):
        return PublicationReview(
            real_artifact_verified=True, visual_review_passed=True, mobile_playback_passed=True,
            natural_voice_listening_passed=True, voice_engine="qwen3-customvoice-reviewed",
            media_rights_checked=True, privacy_checked=True,
            ai_content_label_confirmed=True, fictional_role_label_confirmed=True,
            user_final_approved=True,
        )

    def test_voice_candidate_exists_and_not_evaluated(self):
        plan = audition_plan()
        self.assertEqual(plan["speaker"], "Dylan")
        self.assertIn("UNTESTED", plan["status"])
        self.assertEqual({x["key"] for x in plan["takes"]}, {"work", "inner_os", "service_smile"})
        self.assertFalse(plan["legacy_espeak_release_allowed"])

    def test_quality_gate_rejects_legacy_espeak_even_if_other_checks_pass(self):
        review = replace(self.approved(), voice_engine="legacy-espeak")
        self.assertIn("unacceptable_demo_voice_engine", publication_blockers(review, PublicationTarget("douyin")))

    def test_quality_gate_rejects_missing_audio_and_publish_approval(self):
        blocked = publication_blockers(PublicationReview(), PublicationTarget("douyin"))
        self.assertIn("natural_voice_not_listened", blocked)
        self.assertIn("user_final_approval_missing", blocked)
        self.assertIn("real_artifact_unverified", blocked)

    def test_manual_publish_only_preflight(self):
        self.assertEqual(publication_blockers(self.approved(), PublicationTarget("douyin", method="manual")), [])

    def test_api_publish_requires_valid_permission_and_per_video_awareness(self):
        target = PublicationTarget("douyin", method="authorized_api")
        self.assertEqual(publication_blockers(self.approved(), target), [
            "platform_api_permission_not_verified", "user_not_aware_of_this_submission"
        ])
        self.assertEqual(publication_blockers(self.approved(), replace(target, permission_verified=True, user_aware_of_this_submission=True)), [])

    def test_published_state_must_follow_platform_confirmation(self):
        with self.assertRaises(ValueError):
            transition(WorkflowState.READY_TO_SUBMIT, WorkflowState.CONFIRMED_PUBLISHED)
        x = transition(WorkflowState.READY_TO_SUBMIT, WorkflowState.SUBMITTED_AWAITING_CONFIRMATION)
        self.assertEqual(transition(x, WorkflowState.CONFIRMED_PUBLISHED), WorkflowState.CONFIRMED_PUBLISHED)

    def test_comment_draft_never_sends(self):
        d = create_unsent_reply_draft(CommentSource("user_provided", "example-1", "这能做吗？", "douyin"), "谢谢甲方，我先试一下。")
        self.assertFalse(d["sent"])
        self.assertTrue(d["requires_human_review"])
        with self.assertRaises(ValueError):
            create_unsent_reply_draft(CommentSource("user_provided", None, "", "douyin"), "ok")


if __name__ == "__main__":
    unittest.main()
