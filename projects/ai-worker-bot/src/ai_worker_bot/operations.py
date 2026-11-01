"""Offline gatekeeping contracts for future account operations.

No network, credentials, platform API calls, or messages are sent by this module.
It is intentionally strict: a plausible story is not evidence of a publishable video.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class WorkflowState(str, Enum):
    PLANNED = "planned"
    PRODUCING = "producing"
    QUALITY_REVIEW = "quality_review"
    USER_APPROVAL = "user_approval"
    READY_TO_SUBMIT = "ready_to_submit"
    SUBMITTED_AWAITING_CONFIRMATION = "submitted_awaiting_confirmation"
    CONFIRMED_PUBLISHED = "confirmed_published"
    FAILED = "failed"


TRANSITIONS: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.PLANNED: {WorkflowState.PRODUCING, WorkflowState.FAILED},
    WorkflowState.PRODUCING: {WorkflowState.QUALITY_REVIEW, WorkflowState.FAILED},
    WorkflowState.QUALITY_REVIEW: {WorkflowState.PRODUCING, WorkflowState.USER_APPROVAL, WorkflowState.FAILED},
    WorkflowState.USER_APPROVAL: {WorkflowState.PRODUCING, WorkflowState.READY_TO_SUBMIT, WorkflowState.FAILED},
    WorkflowState.READY_TO_SUBMIT: {WorkflowState.SUBMITTED_AWAITING_CONFIRMATION, WorkflowState.FAILED},
    WorkflowState.SUBMITTED_AWAITING_CONFIRMATION: {WorkflowState.CONFIRMED_PUBLISHED, WorkflowState.FAILED},
    WorkflowState.CONFIRMED_PUBLISHED: set(),
    WorkflowState.FAILED: {WorkflowState.PRODUCING},
}


def transition(current: WorkflowState, target: WorkflowState) -> WorkflowState:
    if target not in TRANSITIONS[current]:
        raise ValueError(f"Illegal transition from {current.value} to {target.value}")
    return target


@dataclass(frozen=True)
class PublicationReview:
    """Evidence flags verified by the user/authorized account holder, not by AI claims."""

    real_artifact_verified: bool = False
    visual_review_passed: bool = False
    mobile_playback_passed: bool = False
    natural_voice_listening_passed: bool = False
    voice_engine: str = "legacy-espeak"  # Do not approve old robotic speech for release.
    media_rights_checked: bool = False
    privacy_checked: bool = False
    ai_content_label_confirmed: bool = False
    fictional_role_label_confirmed: bool = False
    user_final_approved: bool = False


@dataclass(frozen=True)
class PublicationTarget:
    """Describes an intended submission; no API implementation exists yet."""

    platform: Literal["douyin", "kuaishou", "bilibili", "wechat_channels"]
    method: Literal["manual", "authorized_api"] = "manual"
    permission_verified: bool = False
    user_aware_of_this_submission: bool = False


def publication_blockers(review: PublicationReview, target: PublicationTarget) -> list[str]:
    """Returns every reason why we must not submit this episode.

    A successful call returns **preflight ready**, NEVER 'published'. Actual
    publication requires a separate authorized adapter and status verification.
    """
    checks = {
        "real_artifact_unverified": review.real_artifact_verified,
        "visual_review_missing": review.visual_review_passed,
        "mobile_playback_unverified": review.mobile_playback_passed,
        "natural_voice_not_listened": review.natural_voice_listening_passed,
        "media_rights_unchecked": review.media_rights_checked,
        "privacy_review_missing": review.privacy_checked,
        "ai_content_label_missing": review.ai_content_label_confirmed,
        "fictional_role_label_missing": review.fictional_role_label_confirmed,
        "user_final_approval_missing": review.user_final_approved,
    }
    problems = [name for name, passed in checks.items() if not passed]
    if review.voice_engine in {"legacy-espeak", "espeak", "none", "unknown"}:
        problems.append("unacceptable_demo_voice_engine")
    if target.method == "authorized_api":
        if not target.permission_verified:
            problems.append("platform_api_permission_not_verified")
        if not target.user_aware_of_this_submission:
            problems.append("user_not_aware_of_this_submission")
    return problems


@dataclass(frozen=True)
class CommentSource:
    source_type: Literal["user_provided", "authorized_platform_api"]
    public_comment_id: str | None
    text: str
    platform: str


def create_unsent_reply_draft(comment: CommentSource, reply: str) -> dict[str, object]:
    """Draft only; never reply or fetch a comment without explicit source."""
    if not comment.text.strip() or not reply.strip():
        raise ValueError("Comment and draft text are required")
    if len(reply) > 800:
        raise ValueError("Reply draft too long")
    return {
        "platform": comment.platform,
        "source_type": comment.source_type,
        "comment_id": comment.public_comment_id,
        "reply_draft": reply,
        "requires_human_review": True,
        "sent": False,
    }
