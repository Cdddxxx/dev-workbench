"""Offline account preparation, not account registration or a platform adapter.

Input evidence is an operator's declaration, NEVER independently verified login.
Only opaque private references belong in the input; no passwords, cookies or UIDs.
No network functions exist here. A complete checklist cannot enable publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from .core import load_task, run_task
from .operations import PublicationReview, PublicationTarget, publication_blockers
from .persona import CHARACTER_ID, PERSONA_VERSION, preview_persona

PROVIDERS = ("douyin", "wechat_channels", "kuaishou")
REF = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
SHA = re.compile(r"^[a-f0-9]{64}$")


def profile_draft() -> dict[str, Any]:
    """001's existing character; generated avatar candidate still needs approval."""
    return {
        "character_id": CHARACTER_ID,
        "persona_version": PERSONA_VERSION,
        "display_name": None,
        "copy_status": "rejected_pending_revision_do_not_submit",
        "bio": None,
        "avatar_brief": "原创圆头机器人，海军蓝/橙色，工号001，两只灯眼；营业时标准笑弧。",
        "avatar_asset_status": "generated_candidate_not_user_approved_or_platform_crop_verified",
        "avatar_asset": "assets/profile/avatar-001-v1.png",
        "avatar_sha256": "376dccb702265647c621b3c9729ed29388808ab9e339fae87aec1249760fd66f",
        "disclosure": "AI角色 / 虚构演绎；当前为离线规则程序原型，未接入自主运营。",
        "owner_role": "用户为幕后老板；剧情晋升不改变账号所有权或程序权限",
    }


def profile_digest() -> str:
    return hashlib.sha256(json.dumps(profile_draft(), ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def empty_account(provider: str) -> dict[str, Any]:
    if provider not in PROVIDERS:
        raise ValueError("Unsupported provider")
    return {
        "provider": provider, "account_ref": None, "identity_status": "unverified",
        "verification_status": "unknown", "permission_status": "unknown",
        "profile_status": "draft", "profile_digest": None,
        "evidence_ref": None, "observed_at": None,
        "safety_status": "active",
    }


def validate_account(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != set(empty_account("douyin")):
        raise ValueError("Account schema mismatch; credentials and unknown fields are forbidden")
    choices = {
        "provider": PROVIDERS,
        "identity_status": ("unverified", "owner_attested", "mismatch"),
        "verification_status": ("unknown", "required", "operator_attested_complete"),
        "permission_status": ("unknown", "denied", "revoked", "operator_attested"),
        "profile_status": ("draft", "pending_submission", "submitted_awaiting_readback", "operator_attested_readback", "mismatch"),
        "safety_status": ("active", "paused", "access_denied"),
    }
    for key, values in choices.items():
        if not isinstance(raw[key], str) or raw[key] not in values:
            raise ValueError(f"Invalid {key}")
    for key in ("account_ref", "evidence_ref"):
        if raw[key] is not None and (not isinstance(raw[key], str) or not REF.fullmatch(raw[key])):
            raise ValueError(f"{key} must be an opaque reference, not personal data")
    if raw["profile_digest"] is not None and (not isinstance(raw["profile_digest"], str) or not SHA.fullmatch(raw["profile_digest"])):
        raise ValueError("Invalid profile_digest")
    if raw["observed_at"] is not None:
        parse_time(raw["observed_at"])
    return dict(raw)


def parse_time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("observed_at must be an ISO timestamp with timezone")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid observed_at timestamp") from exc
    if result.tzinfo is None:
        raise ValueError("observed_at requires timezone")
    return result


def preflight(account: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    account = validate_account(account)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now requires timezone")
    blockers = []
    checks = {
        "account_identity_missing": account["account_ref"] is not None,
        "owner_identity_not_attested": account["identity_status"] == "owner_attested",
        "user_verification_incomplete": account["verification_status"] == "operator_attested_complete",
        "permission_not_attested": account["permission_status"] == "operator_attested",
        "profile_not_read_back": account["profile_status"] == "operator_attested_readback",
        "profile_revision_mismatch": account["profile_digest"] == profile_digest(),
        "evidence_reference_missing": account["evidence_ref"] is not None,
        "safety_stop": account["safety_status"] == "active",
    }
    blockers.extend(key for key, passed in checks.items() if not passed)
    if account["observed_at"] is None:
        blockers.append("evidence_time_missing")
    else:
        age = now - parse_time(account["observed_at"])
        if age < timedelta(0) or age > timedelta(hours=24):
            blockers.append("evidence_stale_or_future")
    # No API/auth adapter exists for ANY provider. This cannot be overridden in JSON.
    blockers.append("platform_adapter_not_implemented")
    blockers.append("avatar_asset_not_approved")
    blockers.append("profile_copy_rejected_pending_revision")
    return {
        "mode": "offline-preparation-only",
        "provider": account["provider"],
        "account_status": account,
        "evidence_trust": "operator-declared-not-independently-verified",
        "profile_digest": profile_digest(),
        "blockers": blockers,
        "connected": False, "publish_enabled": False, "reply_enabled": False,
        "safe_next_action": "prepare_offline_only",
        "publication_blockers": publication_blockers(PublicationReview(), PublicationTarget(platform=account["provider"])),
    }


def prepare(account: dict[str, Any], task_path: Path, output: Path) -> dict[str, Any]:
    """Create a new work pack; never overwrite existing work or claim delivery UI QA."""
    report = preflight(account)
    task = load_task(task_path)
    output.mkdir(parents=True, exist_ok=False)
    # Refuse replay into an existing output. No personal account details are logged.
    audit_path = output / "audit.jsonl"
    audit_path.write_text(json.dumps({"event": "offline_work_started", "external_actions_enabled": False}) + "\n", encoding="utf-8")
    try:
        manifest = run_task(task, output / "task")
        actual = hashlib.sha256((output / "task" / manifest["deliverable"]).read_bytes()).hexdigest()
        if actual != manifest["deliverable_sha256"]:
            raise RuntimeError("Deliverable checksum mismatch")
    except (OSError, ValueError, RuntimeError):
        # Do not include input values, private paths or exception text in the audit.
        with audit_path.open("a", encoding="utf-8") as audit_file:
            audit_file.write(json.dumps({"event": "offline_task_failed", "complete": False}) + "\n")
        raise
    report["task_result"] = {
        "task_id": task["id"], "status": "html_generated_and_checksum_verified",
        "deliverable": "task/" + manifest["deliverable"], "sha256": actual,
        "browser_tested": False, "video_produced": False, "published": False,
    }
    for name, data in (("profile-draft.json", profile_draft()), ("preflight.json", report), ("character.json", preview_persona())):
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit = [
        {"event": "offline_preflight", "blockers": report["blockers"]},
        {"event": "profile_drafted", "digest": profile_digest(), "submitted": False},
        {"event": "task_generated_and_checksum_verified", "sha256": actual},
        {"event": "external_actions_disabled", "published": False, "replied": False},
    ]
    with audit_path.open("a", encoding="utf-8") as audit_file:
        audit_file.write("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in audit))
    (output / "NEXT.md").write_text(
        "# 工号001 入驻工作包（仅离线）\n\n"
        "主页资料是待审草稿；没有注册、登录、提交或读取任何真实平台。头像候选已生成，尚未用户审定或平台裁切验收。\n"
        "账号证据字段是操作者声明，不是程序验证；私有原始证据应按账号、平台、资料版本核对，不能提交公开仓库。\n"
        "身份验证/验证码由账号所有者完成。遇访问拒绝、撤销、资料不一致或过期证据，只保留离线成果，不重试后台。\n"
        "所有平台适配器未实现；即使清单填写完也不启用发布或回复。发布另需现有 operations.py 的全部质量审核。\n"
        "成果在 task/deliverable/index.html；SHA-256 已从磁盘重算，浏览器/手机验收尚未完成。\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="001 离线入驻准备：不注册、不登录、不发布")
    parser.add_argument("--provider", choices=PROVIDERS, default="douyin")
    parser.add_argument("--account", type=Path, help="private operator-declared checklist, never credentials")
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new output directory; must not exist")
    args = parser.parse_args(argv)
    try:
        account = empty_account(args.provider)
        if args.account:
            account = validate_account(json.loads(args.account.read_text(encoding="utf-8")))
            if account["provider"] != args.provider:
                raise ValueError("Account provider does not match --provider")
        report = prepare(account, args.task, args.output)
        print(f"Offline pack created: {args.output}; real platform connection: NO")
        print("Blocked: " + ", ".join(report["blockers"]))
        return 0  # Success means local files only, not a ready account.
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
