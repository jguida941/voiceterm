"""Tests for ``devctl pipeline`` recovery command.

These tests exercise the status / recover / abandon / refresh-
authorization handlers against isolated temporary fixtures so we
never touch the live pipeline artifact.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.cli import COMMAND_HANDLERS, build_parser
from dev.scripts.devctl.commands.pipeline.abandon_action import run_abandon
from dev.scripts.devctl.commands.pipeline.command import run as pipeline_run
from dev.scripts.devctl.commands.pipeline.recover_action import run_recover
from dev.scripts.devctl.commands.pipeline.refresh_authorization_action import (
    _apply_refresh as apply_refresh_authorization,
    run_refresh_authorization,
)
from dev.scripts.devctl.commands.pipeline.status_action import (
    build_status_view,
    run_status,
)
from dev.scripts.devctl.commands.pipeline.support import (
    ABANDONED_RECEIPT_FILENAME,
    PIPELINE_FILENAME,
    RECOVER_RECEIPT_FILENAME,
    REFRESH_RECEIPT_FILENAME,
    load_pipeline_payload,
    resolve_pipeline_paths,
)
from dev.scripts.devctl.runtime.pipeline_recovery_receipt import (
    PipelineRecoveryReceipt,
)


def _sample_pipeline_payload(
    *,
    state: str = "commit_recorded",
    pipeline_id: str = "pipeline-test-0001",
    authorized_head_sha: str = "deadbeef00000000000000000000000000000000",
    expires_at_utc: str = "2099-01-01T00:00:00.000000Z",
    commit_sha: str | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_id": "RemoteCommitPipelineContract",
        "pipeline_id": pipeline_id,
        "state": state,
        "commit_sha": commit_sha or authorized_head_sha,
        "push_authorization": {
            "schema_version": 1,
            "contract_id": "PushAuthorizationRecord",
            "authorization_id": "push-auth-test-001",
            "pipeline_id": pipeline_id,
            "authorized_head_sha": authorized_head_sha,
            "approved_at_utc": "2026-04-09T13:25:57.373695Z",
            "expires_at_utc": expires_at_utc,
            "approved_by": "operator",
        },
    }


class _PipelineFixture:
    """RAII helper that wires a tmp pipeline root + fake HEAD env var."""

    def __init__(self, *, fake_head: str | None = None) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.pipeline_root = self.root / "projections" / "latest"
        self.receipts_root = self.root / "latest"
        self.pipeline_root.mkdir(parents=True, exist_ok=True)
        self.receipts_root.mkdir(parents=True, exist_ok=True)
        self._prev_env = os.environ.get("DEVCTL_PIPELINE_FAKE_HEAD")
        if fake_head is not None:
            os.environ["DEVCTL_PIPELINE_FAKE_HEAD"] = fake_head

    def close(self) -> None:
        if self._prev_env is None:
            os.environ.pop("DEVCTL_PIPELINE_FAKE_HEAD", None)
        else:
            os.environ["DEVCTL_PIPELINE_FAKE_HEAD"] = self._prev_env
        self._tmp.cleanup()

    def set_head(self, sha: str) -> None:
        os.environ["DEVCTL_PIPELINE_FAKE_HEAD"] = sha

    def write_payload(self, payload: dict[str, object]) -> None:
        (self.pipeline_root / PIPELINE_FILENAME).write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )

    def read_payload(self) -> dict[str, object]:
        path = self.pipeline_root / PIPELINE_FILENAME
        return json.loads(path.read_text(encoding="utf-8"))

    def namespace(self, **extra: object) -> SimpleNamespace:
        base = dict(
            action="",
            reason="",
            operator_actor="operator",
            pipeline_root_override=str(self.pipeline_root),
            receipts_root_override=str(self.receipts_root),
            format="json",
        )
        base.update(extra)
        return SimpleNamespace(**base)

    def paths(self):
        return resolve_pipeline_paths(
            pipeline_root_override=self.pipeline_root,
            receipts_root_override=self.receipts_root,
        )


class PipelineStatusTests(unittest.TestCase):
    def test_status_returns_current_pipeline_fields(self) -> None:
        fixture = _PipelineFixture(fake_head="deadbeef00000000000000000000000000000000")
        try:
            fixture.write_payload(_sample_pipeline_payload())
            view = build_status_view(fixture.paths())
            self.assertTrue(view["ok"])
            self.assertEqual(view["pipeline_id"], "pipeline-test-0001")
            self.assertEqual(view["state"], "commit_recorded")
            self.assertEqual(
                view["authorized_head_sha"],
                "deadbeef00000000000000000000000000000000",
            )
            self.assertEqual(
                view["current_head_sha"],
                "deadbeef00000000000000000000000000000000",
            )
            self.assertFalse(view["head_has_moved"])
            self.assertFalse(view["authorization_expired"])
        finally:
            fixture.close()

    def test_status_idempotent_when_called_twice(self) -> None:
        fixture = _PipelineFixture(fake_head="deadbeef00000000000000000000000000000000")
        try:
            fixture.write_payload(_sample_pipeline_payload())
            first = build_status_view(fixture.paths())
            second = build_status_view(fixture.paths())
            self.assertEqual(first, second)
        finally:
            fixture.close()

    def test_status_recommends_recover_when_head_changed(self) -> None:
        fixture = _PipelineFixture(fake_head="cafebabe00000000000000000000000000000000")
        try:
            fixture.write_payload(_sample_pipeline_payload())
            view = build_status_view(fixture.paths())
            self.assertTrue(view["head_has_moved"])
            self.assertEqual(view["recommended_next_action"], "recover")
        finally:
            fixture.close()

    def test_status_recommends_abandon_when_authorization_expired(self) -> None:
        fixture = _PipelineFixture(fake_head="deadbeef00000000000000000000000000000000")
        try:
            expired = "2000-01-01T00:00:00.000000Z"
            fixture.write_payload(
                _sample_pipeline_payload(expires_at_utc=expired)
            )
            view = build_status_view(fixture.paths())
            self.assertTrue(view["authorization_expired"])
            # HEAD matches → "refresh-authorization" recommended
            self.assertEqual(
                view["recommended_next_action"],
                "refresh-authorization",
            )
        finally:
            fixture.close()

    def test_status_when_no_pipeline_artifact_exits_nonzero(self) -> None:
        fixture = _PipelineFixture(fake_head="deadbeef")
        try:
            args = fixture.namespace(action="status")
            rc = run_status(args)
            self.assertEqual(rc, 1)
        finally:
            fixture.close()


class PipelineAbandonTests(unittest.TestCase):
    def test_abandon_requires_reason(self) -> None:
        fixture = _PipelineFixture(fake_head="deadbeef")
        try:
            fixture.write_payload(_sample_pipeline_payload())
            args = fixture.namespace(action="abandon", reason="")
            rc = run_abandon(args)
            self.assertEqual(rc, 2)
        finally:
            fixture.close()

    def test_abandon_requires_min_reason_length(self) -> None:
        fixture = _PipelineFixture(fake_head="deadbeef")
        try:
            fixture.write_payload(_sample_pipeline_payload())
            args = fixture.namespace(action="abandon", reason="short")
            rc = run_abandon(args)
            self.assertEqual(rc, 2)
        finally:
            fixture.close()

    def test_abandon_transitions_state_to_abandoned(self) -> None:
        fixture = _PipelineFixture(fake_head="deadbeef")
        try:
            fixture.write_payload(_sample_pipeline_payload())
            args = fixture.namespace(
                action="abandon",
                reason="manual recovery test fixture",
            )
            rc = run_abandon(args)
            self.assertEqual(rc, 0)
            updated = fixture.read_payload()
            self.assertEqual(updated["state"], "abandoned")
            receipt_path = fixture.receipts_root / ABANDONED_RECEIPT_FILENAME
            self.assertTrue(receipt_path.exists())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["contract_id"], "PipelineRecoveryReceipt")
            self.assertEqual(receipt["action"], "abandon")
            self.assertEqual(receipt["previous_state"], "commit_recorded")
            self.assertEqual(receipt["new_state"], "abandoned")
        finally:
            fixture.close()

    def test_abandon_refuses_when_already_terminal(self) -> None:
        fixture = _PipelineFixture(fake_head="deadbeef")
        try:
            fixture.write_payload(
                _sample_pipeline_payload(state="push_completed")
            )
            args = fixture.namespace(
                action="abandon",
                reason="attempted invalid abandon",
            )
            rc = run_abandon(args)
            self.assertEqual(rc, 1)
            updated = fixture.read_payload()
            self.assertEqual(updated["state"], "push_completed")
        finally:
            fixture.close()


class PipelineRecoverTests(unittest.TestCase):
    def test_recover_refuses_when_head_matches_authorized(self) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            fixture.write_payload(_sample_pipeline_payload())
            args = fixture.namespace(action="recover")
            rc = run_recover(args)
            self.assertEqual(rc, 1)
            updated = fixture.read_payload()
            # Untouched
            self.assertEqual(
                updated["push_authorization"]["authorization_id"],
                "push-auth-test-001",
            )
        finally:
            fixture.close()

    def test_recover_rebinds_when_head_has_moved(self) -> None:
        moved_head = "cafebabe00000000000000000000000000000000"
        fixture = _PipelineFixture(fake_head=moved_head)
        try:
            fixture.write_payload(_sample_pipeline_payload())
            args = fixture.namespace(action="recover")
            rc = run_recover(args)
            self.assertEqual(rc, 0)
            updated = fixture.read_payload()
            self.assertEqual(
                updated["push_authorization"]["authorized_head_sha"],
                moved_head,
            )
            self.assertEqual(updated["commit_sha"], moved_head)
            receipt_path = fixture.receipts_root / RECOVER_RECEIPT_FILENAME
            self.assertTrue(receipt_path.exists())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["action"], "recover")
        finally:
            fixture.close()

    def test_recover_refuses_when_state_is_terminal(self) -> None:
        fixture = _PipelineFixture(
            fake_head="cafebabe00000000000000000000000000000000",
        )
        try:
            fixture.write_payload(
                _sample_pipeline_payload(state="push_completed")
            )
            args = fixture.namespace(action="recover")
            rc = run_recover(args)
            self.assertEqual(rc, 1)
        finally:
            fixture.close()


class PipelineRefreshAuthorizationTests(unittest.TestCase):
    def test_refresh_authorization_extends_expiry(self) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            expired = "2000-01-01T00:00:00.000000Z"
            fixture.write_payload(
                _sample_pipeline_payload(expires_at_utc=expired)
            )
            args = fixture.namespace(action="refresh-authorization")
            rc = run_refresh_authorization(args)
            self.assertEqual(rc, 0)
            updated = fixture.read_payload()
            new_expires = updated["push_authorization"]["expires_at_utc"]
            self.assertNotEqual(new_expires, expired)
            # The new timestamp should parse as a future datetime.
            parsed = datetime.fromisoformat(new_expires.replace("Z", "+00:00"))
            self.assertGreater(parsed, datetime.now(timezone.utc))
            receipt_path = fixture.receipts_root / REFRESH_RECEIPT_FILENAME
            self.assertTrue(receipt_path.exists())
        finally:
            fixture.close()

    def test_refresh_refuses_when_head_has_moved(self) -> None:
        moved_head = "cafebabe00000000000000000000000000000000"
        fixture = _PipelineFixture(fake_head=moved_head)
        try:
            expired = "2000-01-01T00:00:00.000000Z"
            fixture.write_payload(
                _sample_pipeline_payload(expires_at_utc=expired)
            )
            args = fixture.namespace(action="refresh-authorization")
            rc = run_refresh_authorization(args)
            self.assertEqual(rc, 1)
            result = apply_refresh_authorization(
                paths=fixture.paths(),
                reason="test",
                operator_actor="operator",
            )
            self.assertEqual(result["recommended_next_action"], "recover")
            # Pipeline artifact must be untouched — no fresh auth minted.
            updated = fixture.read_payload()
            self.assertEqual(
                updated["push_authorization"]["authorization_id"],
                "push-auth-test-001",
            )
            self.assertEqual(
                updated["push_authorization"]["expires_at_utc"],
                expired,
            )
        finally:
            fixture.close()

    def test_refresh_refuses_when_head_unavailable(self) -> None:
        fixture = _PipelineFixture(fake_head="")
        try:
            expired = "2000-01-01T00:00:00.000000Z"
            fixture.write_payload(
                _sample_pipeline_payload(expires_at_utc=expired)
            )
            result = apply_refresh_authorization(
                paths=fixture.paths(),
                reason="test",
                operator_actor="operator",
            )
            self.assertFalse(result["ok"])
            self.assertEqual(result["reason_refused"], "current_head_unavailable")
            self.assertEqual(result["recommended_next_action"], "none")
            updated = fixture.read_payload()
            self.assertEqual(
                updated["push_authorization"]["expires_at_utc"],
                expired,
            )
        finally:
            fixture.close()

    def test_refresh_refuses_when_state_not_refreshable(self) -> None:
        fixture = _PipelineFixture(fake_head="deadbeef")
        try:
            fixture.write_payload(
                _sample_pipeline_payload(state="push_completed")
            )
            args = fixture.namespace(action="refresh-authorization")
            rc = run_refresh_authorization(args)
            self.assertEqual(rc, 1)
        finally:
            fixture.close()


class PipelineCLIIntegrationTests(unittest.TestCase):
    def test_pipeline_command_registered_in_handlers(self) -> None:
        self.assertIn("pipeline", COMMAND_HANDLERS)

    def test_pipeline_parser_builds_with_required_action(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["pipeline", "--action", "status"])
        self.assertEqual(args.command, "pipeline")
        self.assertEqual(args.action, "status")

    def test_pipeline_parser_rejects_unknown_action(self) -> None:
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["pipeline", "--action", "bogus"])

    def test_dispatcher_rejects_empty_action(self) -> None:
        args = SimpleNamespace(action="", format="md")
        rc = pipeline_run(args)
        self.assertEqual(rc, 2)


class PipelineRecoveryReceiptTests(unittest.TestCase):
    def test_receipt_requires_valid_action(self) -> None:
        with self.assertRaises(ValueError):
            PipelineRecoveryReceipt(
                action="bogus",
                pipeline_id="pipeline-1",
                previous_state="commit_recorded",
                new_state="abandoned",
                reason="test",
                operator_actor="operator",
                generated_at_utc="2026-04-09T00:00:00.000000Z",
            )

    def test_receipt_to_dict_round_trip(self) -> None:
        receipt = PipelineRecoveryReceipt(
            action="abandon",
            pipeline_id="pipeline-1",
            previous_state="commit_recorded",
            new_state="abandoned",
            reason="manual abandon",
            operator_actor="operator",
            generated_at_utc="2026-04-09T00:00:00.000000Z",
            artifact_paths=("a.json", "b.json"),
        )
        data = receipt.to_dict()
        self.assertEqual(data["contract_id"], "PipelineRecoveryReceipt")
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["artifact_paths"], ["a.json", "b.json"])


if __name__ == "__main__":
    unittest.main()
