import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from ai_worker_bot.onboarding import (
    PROVIDERS, empty_account, main, preflight, prepare, profile_digest,
    profile_draft, validate_account,
)
from ai_worker_bot.persona import CHARACTER_ID, PERSONA_VERSION
from ai_worker_bot.core import run_task

NOW = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
TASK = Path(__file__).resolve().parents[1] / "examples/day-01.json"


def declared_account():
    account = empty_account("douyin")
    account.update(account_ref="private-account-a", identity_status="owner_attested",
                   verification_status="operator_attested_complete",
                   permission_status="operator_attested", profile_status="operator_attested_readback",
                   profile_digest=profile_digest(), evidence_ref="private-evidence-a",
                   observed_at=NOW.isoformat())
    return account


class OnboardingTests(unittest.TestCase):
    def test_all_providers_default_to_offline_and_blocked(self):
        for provider in PROVIDERS:
            with self.subTest(provider=provider):
                result = preflight(empty_account(provider), NOW)
                self.assertFalse(result["connected"])
                self.assertFalse(result["publish_enabled"])
                self.assertFalse(result["reply_enabled"])
                self.assertIn("account_identity_missing", result["blockers"])
                self.assertIn("platform_adapter_not_implemented", result["blockers"])
                self.assertIn("user_final_approval_missing", result["publication_blockers"])

    def test_full_operator_declaration_is_not_real_connection(self):
        result = preflight(declared_account(), NOW)
        self.assertEqual(result["blockers"], ["platform_adapter_not_implemented", "avatar_asset_not_approved", "profile_copy_rejected_pending_revision"])
        self.assertFalse(result["connected"])
        self.assertIn("not-independently-verified", result["evidence_trust"])

    def test_profile_inherits_canonical_persona(self):
        profile = profile_draft()
        self.assertEqual(profile["character_id"], CHARACTER_ID)
        self.assertEqual(profile["persona_version"], PERSONA_VERSION)
        self.assertIn("海军蓝/橙色", profile["avatar_brief"])
        self.assertIn("两只灯眼", profile["avatar_brief"])
        self.assertIn("不改变", profile["owner_role"])
        self.assertEqual(len(profile_digest()), 64)
        self.assertIsNone(profile["display_name"])
        self.assertIsNone(profile["bio"])
        self.assertIn("rejected", profile["copy_status"])

    def test_avatar_candidate_hash_matches_actual_file(self):
        profile = profile_draft()
        asset = TASK.parents[1] / profile["avatar_asset"]
        self.assertEqual(hashlib.sha256(asset.read_bytes()).hexdigest(), profile["avatar_sha256"])
        self.assertIn("not_user_approved", profile["avatar_asset_status"])

    def test_submission_is_not_readback(self):
        for state in ("draft", "pending_submission", "submitted_awaiting_readback", "mismatch"):
            account = declared_account()
            account["profile_status"] = state
            self.assertIn("profile_not_read_back", preflight(account, NOW)["blockers"])

    def test_changed_profile_invalidates_readback(self):
        account = declared_account()
        account["profile_digest"] = "0" * 64
        self.assertIn("profile_revision_mismatch", preflight(account, NOW)["blockers"])

    def test_identity_verification_revocation_and_denial_fail_closed(self):
        for field, value, blocker in (
            ("identity_status", "mismatch", "owner_identity_not_attested"),
            ("verification_status", "required", "user_verification_incomplete"),
            ("permission_status", "revoked", "permission_not_attested"),
            ("permission_status", "denied", "permission_not_attested"),
            ("safety_status", "access_denied", "safety_stop"),
            ("safety_status", "paused", "safety_stop"),
        ):
            with self.subTest(field=field, value=value):
                account = declared_account()
                account[field] = value
                result = preflight(account, NOW)
                self.assertIn(blocker, result["blockers"])
                self.assertEqual(result["safe_next_action"], "prepare_offline_only")

    def test_missing_stale_and_future_evidence_fail_closed(self):
        for delta in (timedelta(hours=-25), timedelta(seconds=1)):
            account = declared_account()
            account["observed_at"] = (NOW + delta).isoformat()
            self.assertIn("evidence_stale_or_future", preflight(account, NOW)["blockers"])
        account = declared_account()
        account["evidence_ref"] = None
        self.assertIn("evidence_reference_missing", preflight(account, NOW)["blockers"])

    def test_schema_rejects_credentials_unknown_fields_and_bool_status(self):
        for field in ("cookie", "access_token", "password", "publish_enabled"):
            account = empty_account("douyin")
            account[field] = "do-not-store"
            with self.assertRaises(ValueError):
                validate_account(account)
        account = empty_account("douyin")
        account["identity_status"] = True
        with self.assertRaises(ValueError):
            validate_account(account)

    def test_bad_refs_times_and_provider_rejected(self):
        for field, value in (("account_ref", "https://personal.invalid/account"),
                             ("evidence_ref", "../secret"), ("observed_at", "2026-11-01"),
                             ("observed_at", 123), ("provider", "unsupported"),
                             ("profile_digest", "not-a-digest")):
            account = empty_account("douyin")
            account[field] = value
            with self.assertRaises(ValueError):
                validate_account(account)

    def test_pack_contains_real_task_and_audit_without_external_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "pack"
            result = prepare(empty_account("kuaishou"), TASK, output)
            artifact = output / result["task_result"]["deliverable"]
            self.assertTrue(artifact.is_file())
            self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), result["task_result"]["sha256"])
            saved = json.loads((output / "preflight.json").read_text())
            self.assertEqual(saved, result)
            events = [json.loads(line) for line in (output / "audit.jsonl").read_text().splitlines()]
            self.assertEqual(events[-1], {"event": "external_actions_disabled", "published": False, "replied": False})
            self.assertFalse(result["task_result"]["browser_tested"])
            self.assertFalse(result["task_result"]["video_produced"])

    def test_existing_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            sentinel = output / "sentinel"
            sentinel.write_text("preserve")
            with self.assertRaises(FileExistsError):
                prepare(empty_account("douyin"), TASK, output)
            self.assertEqual(sentinel.read_text(), "preserve")
            self.assertEqual(list(output.iterdir()), [sentinel])

    def test_invalid_input_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "pack"
            task = Path(tmp) / "bad.json"
            task.write_text("{}")
            with self.assertRaises(ValueError):
                prepare(empty_account("douyin"), task, output)
            self.assertFalse(output.exists())

    def test_checksum_failure_is_not_reported_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            def corrupt(task, output):
                manifest = run_task(task, output)
                (output / manifest["deliverable"]).write_text("corrupted")
                return manifest
            with patch("ai_worker_bot.onboarding.run_task", side_effect=corrupt):
                with self.assertRaises(RuntimeError):
                    prepare(empty_account("douyin"), TASK, Path(tmp) / "pack")
            events = [json.loads(line) for line in (Path(tmp) / "pack/audit.jsonl").read_text().splitlines()]
            self.assertEqual(events[-1]["event"], "offline_task_failed")
            self.assertFalse((Path(tmp) / "pack/preflight.json").exists())

    def test_cli_provider_mismatch_and_repeat_are_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "pack"
            account = Path(tmp) / "account.json"
            account.write_text(json.dumps(empty_account("kuaishou")))
            args = ["--task", str(TASK), "--output", str(output)]
            self.assertEqual(main(args + ["--account", str(account)]), 1)
            self.assertFalse(output.exists())
            self.assertEqual(main(args), 0)
            self.assertEqual(main(args), 1)
