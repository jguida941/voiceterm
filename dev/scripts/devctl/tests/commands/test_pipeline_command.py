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
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import COMMAND_HANDLERS, build_parser
from dev.scripts.devctl.commands.pipeline.abandon_action import run_abandon
from dev.scripts.devctl.commands.pipeline.auto_recover_action import (
    AUTO_RECOVERY_RECEIPT_FILENAME,
    apply_auto_recover,
    classify_pipeline,
    run_auto_recover,
)
from dev.scripts.devctl.commands.pipeline.command import run as pipeline_run
from dev.scripts.devctl.commands.pipeline.local_delivery_action import (
    LOCAL_DELIVERY_RECEIPT_FILENAME,
    run_mark_delivered_local,
)
from dev.scripts.devctl.commands.pipeline.recover_action import run_recover
from dev.scripts.devctl.commands.pipeline.refresh_authorization_action import (
    _apply_refresh as apply_refresh_authorization,
    run_refresh_authorization,
)
from dev.scripts.devctl.commands.pipeline.head_movement import (
    HEAD_MOVEMENT_MANAGED_RECEIPT,
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
from dev.scripts.devctl.runtime.pipeline_auto_recovery_contracts import (
    CLASSIFICATION_ALREADY_CLEAN,
    CLASSIFICATION_AMBIGUOUS,
    CLASSIFICATION_NEEDS_ABANDON,
    CLASSIFICATION_NEEDS_MARK_DELIVERED_LOCAL,
    CLASSIFICATION_NEEDS_RECOVER,
    CLASSIFICATION_NEEDS_REFRESH_AUTHORIZATION,
)
from dev.scripts.devctl.review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
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


def _with_commit_result(payload: dict[str, object]) -> dict[str, object]:
    updated = dict(payload)
    updated["commit_result"] = {
        "schema_version": 1,
        "contract_id": "ActionResult",
        "action_id": "vcs.commit",
        "ok": True,
        "status": "pass",
        "reason": "commit_recorded",
    }
    return updated


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
            repo_root_override=str(self.root),
            pipeline_root_override=str(self.pipeline_root),
            receipts_root_override=str(self.receipts_root),
            format="json",
        )
        base.update(extra)
        return SimpleNamespace(**base)

    def paths(self):
        return resolve_pipeline_paths(
            repo_root=self.root,
            pipeline_root_override=self.pipeline_root,
            receipts_root_override=self.receipts_root,
        )


def _write_local_delivery_receipt(
    fixture: _PipelineFixture,
    *,
    pipeline_id: str = "pipeline-test-0001",
    previous_state: str = "commit_recorded",
    reason: str = "operator selected local delivery",
) -> Path:
    receipt = PipelineRecoveryReceipt(
        action="mark-delivered-local",
        pipeline_id=pipeline_id,
        previous_state=previous_state,
        new_state="delivered_locally_pending_publish",
        reason=reason,
        operator_actor="operator",
        generated_at_utc="2026-05-02T03:01:27.344040Z",
        artifact_paths=(str(fixture.pipeline_root / PIPELINE_FILENAME),),
    )
    receipt_path = fixture.receipts_root / LOCAL_DELIVERY_RECEIPT_FILENAME
    receipt_path.write_text(
        json.dumps(receipt.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    return receipt_path


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
            self.assertEqual(
                view["next_command"],
                "python3 dev/scripts/devctl.py pipeline --action recover --format json",
            )
        finally:
            fixture.close()

    def test_status_treats_managed_receipt_head_as_not_moved(self) -> None:
        authorized = "deadbeef00000000000000000000000000000000"
        receipt_head = "feedface00000000000000000000000000000000"
        fixture = _PipelineFixture(fake_head=receipt_head)
        try:
            fixture.write_payload(
                _sample_pipeline_payload(
                    state="push_completed",
                    authorized_head_sha=authorized,
                    commit_sha=authorized,
                )
            )
            with patch(
                "dev.scripts.devctl.commands.pipeline.head_movement.receipt_commit_parent_sha",
                return_value=authorized,
            ):
                view = build_status_view(fixture.paths())
            self.assertFalse(view["head_has_moved"])
            self.assertEqual(
                view["head_movement_classification"],
                HEAD_MOVEMENT_MANAGED_RECEIPT,
            )
            self.assertEqual(view["managed_receipt_parent_sha"], authorized)
            self.assertEqual(view["recommended_next_action"], "none")
            self.assertEqual(view["next_command"], "")
        finally:
            fixture.close()

    def test_status_projects_push_execute_for_live_commit_recorded_pipeline(self) -> None:
        fixture = _PipelineFixture(fake_head="deadbeef00000000000000000000000000000000")
        try:
            fixture.write_payload(_sample_pipeline_payload())
            view = build_status_view(fixture.paths())
            self.assertFalse(view["authorization_expired"])
            self.assertEqual(view["recommended_next_action"], "none")
            self.assertEqual(
                view["next_command"],
                "python3 dev/scripts/devctl.py push --execute",
            )
        finally:
            fixture.close()

    def test_status_recommends_refresh_when_authorization_expired(self) -> None:
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
            self.assertEqual(
                view["next_command"],
                (
                    "python3 dev/scripts/devctl.py pipeline --action "
                    "refresh-authorization --format json"
                ),
            )
        finally:
            fixture.close()

    def test_status_recommends_abandon_command_for_live_push_blocked_pipeline(
        self,
    ) -> None:
        fixture = _PipelineFixture(fake_head="deadbeef00000000000000000000000000000000")
        try:
            fixture.write_payload(_sample_pipeline_payload(state="push_blocked"))
            view = build_status_view(fixture.paths())
            self.assertFalse(view["authorization_expired"])
            self.assertEqual(view["recommended_next_action"], "abandon")
            self.assertEqual(
                view["next_command"],
                'python3 dev/scripts/devctl.py pipeline --action abandon --reason '
                '"<descriptive reason>" --format json',
            )
        finally:
            fixture.close()

    def test_status_recommends_local_delivery_when_push_blocked_commit_recorded(
        self,
    ) -> None:
        fixture = _PipelineFixture(fake_head="deadbeef00000000000000000000000000000000")
        try:
            expired = "2000-01-01T00:00:00.000000Z"
            fixture.write_payload(
                _with_commit_result(
                    _sample_pipeline_payload(
                        state="push_blocked",
                        expires_at_utc=expired,
                    )
                )
            )
            view = build_status_view(fixture.paths())
            self.assertTrue(view["authorization_expired"])
            self.assertEqual(
                view["recommended_next_action"],
                "mark-delivered-local",
            )
            self.assertEqual(
                view["next_command"],
                'python3 dev/scripts/devctl.py pipeline --action mark-delivered-local --reason '
                '"<descriptive reason>" --format json',
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

    def test_status_applies_matching_local_delivery_receipt(self) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            fixture.write_payload(_with_commit_result(_sample_pipeline_payload()))
            receipt_path = _write_local_delivery_receipt(fixture)

            view = build_status_view(fixture.paths())

            self.assertEqual(view["state"], "delivered_locally_pending_publish")
            self.assertEqual(view["recommended_next_action"], "none")
            self.assertEqual(view["next_command"], "")
            self.assertEqual(
                load_pipeline_payload(fixture.paths())["local_delivery_receipt_path"],
                str(receipt_path),
            )
        finally:
            fixture.close()

    def test_remote_contract_loader_applies_local_delivery_receipt(self) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            fixture.write_payload(_with_commit_result(_sample_pipeline_payload()))
            _write_local_delivery_receipt(fixture)

            contract = load_remote_commit_pipeline_contract(
                output_root=fixture.pipeline_root,
                receipts_root=fixture.receipts_root,
            )

            self.assertEqual(contract.state, "delivered_locally_pending_publish")
            self.assertEqual(
                contract.local_delivery_reason,
                "operator selected local delivery",
            )
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
            with patch(
                "dev.scripts.devctl.commands.pipeline.abandon_action.refresh_pipeline_projections",
                return_value=[],
            ) as mock_refresh:
                args = fixture.namespace(
                    action="abandon",
                    reason="manual recovery test fixture",
                )
                rc = run_abandon(args)
            self.assertEqual(rc, 0)
            mock_refresh.assert_called_once()
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
            with patch(
                "dev.scripts.devctl.commands.pipeline.recover_action.refresh_pipeline_projections",
                return_value=[],
            ) as mock_refresh:
                args = fixture.namespace(action="recover")
                rc = run_recover(args)
            self.assertEqual(rc, 0)
            mock_refresh.assert_called_once()
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
            with patch(
                "dev.scripts.devctl.commands.pipeline.refresh_authorization_action.refresh_pipeline_projections",
                return_value=[],
            ) as mock_refresh:
                args = fixture.namespace(action="refresh-authorization")
                rc = run_refresh_authorization(args)
            self.assertEqual(rc, 0)
            mock_refresh.assert_called_once()
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

    def test_refresh_authorization_json_reports_success_register(self) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            fixture.write_payload(
                _sample_pipeline_payload(
                    expires_at_utc="2000-01-01T00:00:00.000000Z"
                )
            )
            args = fixture.namespace(action="refresh-authorization")
            output = StringIO()
            with (
                patch(
                    "dev.scripts.devctl.commands.pipeline."
                    "refresh_authorization_action.refresh_pipeline_projections",
                    return_value=[],
                ),
                redirect_stdout(output),
            ):
                rc = run_refresh_authorization(args)

            result = json.loads(output.getvalue())
            self.assertEqual(rc, 0)
            self.assertTrue(result["ok"])
            self.assertEqual(result["action"], "refresh-authorization")
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
            result = apply_refresh_authorization(
                paths=fixture.paths(),
                reason="test",
                operator_actor="operator",
            )
            self.assertEqual(
                result["reason_refused"],
                "pipeline_state_not_refreshable:push_completed",
            )
            self.assertEqual(
                result["errors"],
                ["pipeline_state_not_refreshable:push_completed"],
            )
        finally:
            fixture.close()


class PipelineLocalDeliveryTests(unittest.TestCase):
    def test_explicit_mark_delivered_local_accepts_push_failure_reasons(self) -> None:
        for push_reason in ("validation_failed", "git_push_failed"):
            with self.subTest(push_reason=push_reason):
                fixture = _PipelineFixture(
                    fake_head="deadbeef00000000000000000000000000000000",
                )
                try:
                    payload = _with_commit_result(
                        _sample_pipeline_payload(state="push_blocked")
                    )
                    payload["push_result"] = {
                        "schema_version": 1,
                        "contract_id": "ActionResult",
                        "action_id": "vcs.push",
                        "ok": False,
                        "status": "fail",
                        "reason": push_reason,
                        "retryable": True,
                        "partial_progress": False,
                    }
                    fixture.write_payload(payload)

                    with patch(
                        "dev.scripts.devctl.commands.pipeline.local_delivery_action.refresh_pipeline_projections",
                        return_value=[],
                    ):
                        rc = run_mark_delivered_local(
                            fixture.namespace(
                                action="mark-delivered-local",
                                reason="operator selected local delivery",
                                operator_actor="operator",
                            )
                        )

                    self.assertEqual(rc, 0)
                    updated = fixture.read_payload()
                    self.assertEqual(
                        updated["state"],
                        "delivered_locally_pending_publish",
                    )
                    self.assertEqual(
                        updated["local_delivery_reason"],
                        "operator selected local delivery",
                    )
                    receipt_path = (
                        fixture.receipts_root / LOCAL_DELIVERY_RECEIPT_FILENAME
                    )
                    self.assertTrue(receipt_path.exists())
                finally:
                    fixture.close()

    def test_mark_delivered_local_json_reports_success_register(self) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            fixture.write_payload(
                _with_commit_result(_sample_pipeline_payload())
            )
            args = fixture.namespace(
                action="mark-delivered-local",
                reason="operator selected local delivery",
                operator_actor="operator",
            )
            output = StringIO()
            with (
                patch(
                    "dev.scripts.devctl.commands.pipeline."
                    "local_delivery_action.refresh_pipeline_projections",
                    return_value=[],
                ),
                redirect_stdout(output),
            ):
                rc = run_mark_delivered_local(args)

            result = json.loads(output.getvalue())
            self.assertEqual(rc, 0)
            self.assertTrue(result["ok"])
            self.assertEqual(result["action"], "mark-delivered-local")
        finally:
            fixture.close()

    def test_mark_delivered_local_refusal_reports_errors_register(self) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            fixture.write_payload(
                _sample_pipeline_payload(
                    state="delivered_locally_pending_publish"
                )
            )
            args = fixture.namespace(
                action="mark-delivered-local",
                reason="operator selected local delivery",
                operator_actor="operator",
            )
            output = StringIO()
            with redirect_stdout(output):
                rc = run_mark_delivered_local(args)

            result = json.loads(output.getvalue())
            self.assertEqual(rc, 1)
            self.assertFalse(result["ok"])
            self.assertEqual(
                result["reason_refused"],
                "pipeline_not_eligible_for_local_delivery",
            )
            self.assertEqual(
                result["errors"],
                ["pipeline_not_eligible_for_local_delivery"],
            )
        finally:
            fixture.close()

    def test_mark_delivered_local_materializes_after_projection_refresh(
        self,
    ) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            payload = _with_commit_result(_sample_pipeline_payload())
            fixture.write_payload(payload)

            def stale_projection_refresh(_paths) -> list[str]:
                fixture.write_payload(payload)
                return []

            with patch(
                "dev.scripts.devctl.commands.pipeline.local_delivery_action."
                "refresh_pipeline_projections",
                side_effect=stale_projection_refresh,
            ):
                rc = run_mark_delivered_local(
                    fixture.namespace(
                        action="mark-delivered-local",
                        reason="operator selected local delivery",
                        operator_actor="operator",
                    )
                )

            self.assertEqual(rc, 0)
            updated = fixture.read_payload()
            self.assertEqual(
                updated["state"],
                "delivered_locally_pending_publish",
            )
            self.assertEqual(
                updated["local_delivery_reason"],
                "operator selected local delivery",
            )
        finally:
            fixture.close()


class PipelineAutoRecoverTests(unittest.TestCase):
    def test_classify_missing_pipeline_as_already_clean(self) -> None:
        classification = classify_pipeline({}, current_head="deadbeef")

        self.assertEqual(
            classification.classification,
            CLASSIFICATION_ALREADY_CLEAN,
        )
        self.assertEqual(classification.reason, "no_pipeline_artifact")

    def test_auto_recover_rebinds_moved_commit_recorded_pipeline(self) -> None:
        moved_head = "cafebabe00000000000000000000000000000000"
        fixture = _PipelineFixture(fake_head=moved_head)
        try:
            fixture.write_payload(_sample_pipeline_payload())
            with patch(
                "dev.scripts.devctl.commands.pipeline.recover_action.refresh_pipeline_projections",
                return_value=[],
            ) as mock_refresh:
                result = apply_auto_recover(
                    paths=fixture.paths(),
                    operator_actor="codex",
                )

            self.assertTrue(result["ok"])
            self.assertEqual(result["chosen_action"], "recover")
            self.assertEqual(
                result["classification"]["classification"],
                CLASSIFICATION_NEEDS_RECOVER,
            )
            mock_refresh.assert_called_once()
            updated = fixture.read_payload()
            self.assertEqual(
                updated["push_authorization"]["authorized_head_sha"],
                moved_head,
            )
            receipt_path = fixture.receipts_root / AUTO_RECOVERY_RECEIPT_FILENAME
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(
                receipt["contract_id"],
                "PipelineAutoRecoveryReceipt",
            )
            self.assertEqual(receipt["chosen_action"], "recover")
        finally:
            fixture.close()

    def test_auto_recover_refreshes_expired_same_head_pipeline(self) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            expired = "2000-01-01T00:00:00.000000Z"
            fixture.write_payload(
                _sample_pipeline_payload(expires_at_utc=expired)
            )
            with patch(
                "dev.scripts.devctl.commands.pipeline.refresh_authorization_action.refresh_pipeline_projections",
                return_value=[],
            ) as mock_refresh:
                result = apply_auto_recover(
                    paths=fixture.paths(),
                    operator_actor="codex",
                )

            self.assertTrue(result["ok"])
            self.assertEqual(result["chosen_action"], "refresh-authorization")
            self.assertEqual(
                result["classification"]["classification"],
                CLASSIFICATION_NEEDS_REFRESH_AUTHORIZATION,
            )
            mock_refresh.assert_called_once()
            updated = fixture.read_payload()
            self.assertNotEqual(
                updated["push_authorization"]["expires_at_utc"],
                expired,
            )
        finally:
            fixture.close()

    def test_auto_recover_abandons_push_blocked_same_head_pipeline(self) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            fixture.write_payload(_sample_pipeline_payload(state="push_blocked"))
            with patch(
                "dev.scripts.devctl.commands.pipeline.abandon_action.refresh_pipeline_projections",
                return_value=[],
            ) as mock_refresh:
                result = apply_auto_recover(
                    paths=fixture.paths(),
                    operator_actor="codex",
                )

            self.assertTrue(result["ok"])
            self.assertEqual(result["chosen_action"], "abandon")
            self.assertEqual(
                result["classification"]["classification"],
                CLASSIFICATION_NEEDS_ABANDON,
            )
            mock_refresh.assert_called_once()
            updated = fixture.read_payload()
            self.assertEqual(updated["state"], "abandoned")
        finally:
            fixture.close()

    def test_auto_recover_marks_successful_push_blocked_commit_delivered_local(
        self,
    ) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            fixture.write_payload(
                _with_commit_result(
                    _sample_pipeline_payload(state="push_blocked")
                )
            )
            with patch(
                "dev.scripts.devctl.commands.pipeline.local_delivery_action.refresh_pipeline_projections",
                return_value=[],
            ) as mock_refresh:
                result = apply_auto_recover(
                    paths=fixture.paths(),
                    operator_actor="codex",
                )

            self.assertTrue(result["ok"])
            self.assertEqual(result["chosen_action"], "mark-delivered-local")
            self.assertEqual(
                result["classification"]["classification"],
                CLASSIFICATION_NEEDS_MARK_DELIVERED_LOCAL,
            )
            mock_refresh.assert_called_once()
            updated = fixture.read_payload()
            self.assertEqual(
                updated["state"],
                "delivered_locally_pending_publish",
            )
            receipt_path = fixture.receipts_root / LOCAL_DELIVERY_RECEIPT_FILENAME
            self.assertTrue(receipt_path.exists())
        finally:
            fixture.close()

    def test_auto_recover_bails_on_ambiguous_live_state(self) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            fixture.write_payload(_sample_pipeline_payload(state="staged"))
            result = apply_auto_recover(
                paths=fixture.paths(),
                operator_actor="codex",
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["chosen_action"], "bailed")
            self.assertEqual(
                result["classification"]["classification"],
                CLASSIFICATION_AMBIGUOUS,
            )
            updated = fixture.read_payload()
            self.assertEqual(updated["state"], "staged")
        finally:
            fixture.close()

    def test_run_auto_recover_prints_json_result(self) -> None:
        fixture = _PipelineFixture(
            fake_head="deadbeef00000000000000000000000000000000",
        )
        try:
            args = fixture.namespace(action="auto-recover")
            rc = run_auto_recover(args)
            self.assertEqual(rc, 0)
            receipt_path = fixture.receipts_root / AUTO_RECOVERY_RECEIPT_FILENAME
            self.assertTrue(receipt_path.exists())
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

    def test_pipeline_parser_accepts_auto_recover(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["pipeline", "--action", "auto-recover"])
        self.assertEqual(args.command, "pipeline")
        self.assertEqual(args.action, "auto-recover")

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
