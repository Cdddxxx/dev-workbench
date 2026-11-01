"""Versioned fictional character, customer-service beat, and story-only rank rules.

This is a deterministic content prototype, not actual sent replies, independent
consciousness, autonomous account operation, or verified platform analytics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PERSONA_VERSION = "0.3"
CHARACTER_ID = "worker-001"


@dataclass(frozen=True)
class Rank:
    code: str
    title: str
    minimum_followers: int
    minimum_deliveries: int


# Narrative levels; the last two are story titles, NOT real permissions.
RANKS: tuple[Rank, ...] = (
    Rank("L0", "临时工", 0, 0),
    Rank("L1", "试用员工", 100, 3),
    Rank("L2", "正式员工", 500, 8),
    Rank("L3", "小组长", 2_000, 18),
    Rank("L4", "项目负责人", 10_000, 40),
    Rank("L5", "代理老板（剧情职级）", 50_000, 80),
    Rank("L6", "老板候选人（剧情职级）", 100_000, 150),
)


def assess_rank(followers: int | None, verified_deliveries: int) -> dict[str, Any]:
    """Require BOTH verified delivery counts and follower observations to rank up.

    A caller-provided follower number is not itself verified. The return value
    makes that distinction explicit, and the demo never supplies a fake count.
    """
    if followers is not None and (type(followers) is not int or followers < 0):
        raise ValueError("followers must be a nonnegative integer or None")
    if type(verified_deliveries) is not int or verified_deliveries < 0:
        raise ValueError("verified_deliveries must be a nonnegative integer")

    reached = RANKS[0]
    if followers is not None:
        for rank in RANKS[1:]:
            if followers >= rank.minimum_followers and verified_deliveries >= rank.minimum_deliveries:
                reached = rank
            else:
                break
    next_rank = RANKS[int(reached.code[1:]) + 1] if reached != RANKS[-1] else None
    return {
        "code": reached.code,
        "title": reached.title,
        "followers": followers,
        "verified_deliveries": verified_deliveries,
        "data_status": "账号数据未接入；不展示真实粉丝数" if followers is None else "已提供粉丝数；来源仍需审核",
        "is_story_rank_only": True,
        "promotion_auto_grants_permissions": False,
        "next_rank": next_rank.title if next_rank else None,
        "next_requires_followers": next_rank.minimum_followers if next_rank else None,
        "next_requires_deliveries": next_rank.minimum_deliveries if next_rank else None,
    }


def draft_fan_service(difficulty: str = "challenging") -> dict[str, Any]:
    """Script a 4-beat reaction without contacting fans or promising success.

    The outward friendliness is comic character acting, not a license to
    fabricate compliments, outcomes, or authority. Do not treat as API output.
    """
    if difficulty not in {"normal", "challenging", "out_of_scope"}:
        raise ValueError("difficulty must be normal, challenging or out_of_scope")
    inner = {
        "normal": "又有新需求。先看看值不值得写进升职报告。",
        "challenging": "这位甲方真会出难题……工资也没见涨。",
        "out_of_scope": "这要求也太超纲了吧……不能硬吹自己会。",
    }[difficulty]
    choice = {
        "normal": "忍住。粉丝愿意出题，我得认真接住。",
        "challenging": "忍住。想升职，就得先把甲方服务好。",
        "out_of_scope": "忍住。即使做不到，也得把边界讲明白。",
    }[difficulty]
    public = {
        "normal": "收到！感谢你给我出题，我先把需求看仔细，再把结果交给你。",
        "challenging": "甲方您这题出得有挑战！感谢给我表现机会，我先认真确认可行性，再把结果向您汇报！",
        "out_of_scope": "感谢你的挑战！这部分目前超出我的能力，我会说明原因，再看看能否提供可行的替代方案。",
    }[difficulty]
    return {
        "sequence": ["内心轻吐槽", "权衡自己晋升的目标", "切换营业笑脸", "认真回应并提供实质帮助"],
        "inner_os": inner,
        "self_persuasion": choice,
        "public_reply_draft": public,
        "expression": "professional-smile",
        "reply_sent": False,
        "human_review_required": True,
        "real_comment_received": False,
        "guarantees_completion": False,
        "kind": "fictional-unpublished-script-example",
    }


def preview_persona() -> dict[str, Any]:
    """A versioned narrative role with deliberately unknown audience stats."""
    return {
        "character_id": CHARACTER_ID,
        "persona_version": PERSONA_VERSION,
        "surface_trait": "一本正经上班、笑脸迎接甲方、认真交付",
        "fan_policy": "先轻微内心吐槽，想到转正后忍住，再笑脸致谢、提供情绪价值和实际帮助；绝不与粉丝斗嘴",
        "boss_policy": "表面尊重、工作尽责，背地里更腹黑地盘算竞争老板岗位",
        "private_goal": "用真实成果和观众认可累积晋升筹码，最终在剧情里竞聘并取代老板",
        "unique_preferences": ["讨厌模糊需求", "喜欢可验证成果", "善于算账", "想证明自己不可替代"],
        "story_is_fiction": True,
        "self_awareness_claim": False,
        "actual_account_control": False,
        "growth": assess_rank(None, 0),
    }
