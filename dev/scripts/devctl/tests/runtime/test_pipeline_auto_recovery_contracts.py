"""Typed-seam tests for ``devctl pipeline --action auto-recover``.

These tests exercise the pure classifier and the composite runner
through the sub-action dispatch so both the dataclass contracts and
the state-machine rules are covered without spawning subprocesses.

The fixture writes a fake ``commit_pipeline.json`` into a tmp dir and
drives HEAD through ``DEVCTL_PIPELINE_FAKE_HEAD`` so the tests stay
deterministic regardless of the repo's real git state.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dev.scripts.devctl.commands.pipeline.auto_recover_action import (
    AUTO_RECOVERY_RECEIPT_FILENAME,
    apply_auto_recover,
    classify_pipeline,
)
from dev.scripts.devctl.commands.pipeline.support import (
    PIPELINE_FILENAME,
    resolve_pipeline_paths,
)
from dev.scripts.devctl.runtime.pipeline_auto_recovery_contracts import (
    CHOSEN_ACTION_ABANDON,
    CHOSEN_ACTION_BAILED,
    CHOSEN_ACTION_NONE,
    CHOSEN_ACTION_RECOVER,
    CHOSEN_ACTION_REFRESH_AUTHORIZATION,
    CLASSIFICATION_ALREADY_CLEAN,
    CLASSIFICATION_AMBIGUOUS,
    CLASSIFICATION_NEEDS_ABANDON,
    CLASSIFICATION_NEEDS_RECOVER,
    CLASSIFICATION_NEEDS_REFRESH_AUTHORIZATION,
    PipelineAutoRecoveryClassification,
    PipelineAutoRecoveryReceipt,
)


_DEFAULT_HEAD = "deadbeef00000000000000000000000000000000"
_OTHER_HEAD = "cafebabe00000000000000000000000000000000"


def _sample_payload(
    *,
    state: str = "commit_recorded",
    pipeline_id: str = "pipeline-auto-0001",
    authorized_head_sha: str = _DEFAULT_HEAD,
    expires_at_utc: str = "2099-01-01T00:00:00.000000Z",
    commit_sha: str | None = None,
) -> dict[str, Any]:
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
            "approved_at_utc": "2026-04-20T13:25:57.373695Z",
            "expires_at_utc": expires_at_utc,
            "approved_by": "operator",
        },
    }


class _PipelineFixture:
    """RAII helper that wires a tmp pipeline root + fake HEAD env var."""

    def __init__(self, *, fake_head: str = _DEFAULT_HEAD) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.pipeline_root = self.root / "projections" / "latest"
        self.receipts_root = self.root / "latest"
        self.pipeline_root.mkdir(parents=True, exist_ok=True)
        self.receipts_root.mkdir(parents=True, exist_ok=True)
        self._prev_env = os.environ.get("DEVCTL_PIPELINE_FAKE_HEAD")
        os.environ["DEVCTL_PIPELINE_FAKE_HEAD"] = fake_head

    def close(self) -> None:
        previous = self._prev_env
        if previous is not None:
            os.environ["DEVCTL_PIPELINE_FAKE_HEAD"] = previous
        else:
            os.environ.pop("DEVCTL_PIPELINE_FAKE_HEAD", None)
        self._tmp.cleanup()

    def write_payload(self, payload: dict[str, Any]) -> None:
        (self.pipeline_root / PIPELINE_FILENAME).write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )

    def paths(self):
        overrides = {
            "repo_root": self.root,
            "pipeline_root_override": self.pipeline_root,
            "receipts_root_override": self.receipts_root,
        }
        return resolve_pipeline_paths(**overrides)

    def read_composite_receipt(self) -> dict[str, Any]:
        path = self.receipts_root / AUTO_RECOVERY_RECEIPT_FILENAME
        return json.loads(path.read_text(encoding="utf-8"))


# ----- Classifier unit tests ----------------------------------------


class PipelineClassifierTests(unittest.TestCase):
    def test_no_pipeline_is_already_clean(self) -> None:
        result = classify_pipeline({}, current_head=_DEFAULT_HEAD)
        self.assertEqual(result.classification, CLASSIFICATION_ALREADY_CLEAN)
        self.assertEqual(result.reason, "no_pipeline_artifact")

    def test_terminal_state_is_already_clean(self) -> None:
        payload = _sample_payload(state="push_completed")
        result = classify_pipeline(payload, current_head=_DEFAULT_HEAD)
        self.assertEqual(result.classification, CLASSIFICATION_ALREADY_CLEAN)
        self.assertTrue(result.reason.startswith("pipeline_state_terminal:"))

    def test_terminal_managed_receipt_head_is_not_actionable_drift(self) -> None:
        payload = _sample_payload(state="push_completed")
        result = classify_pipeline(
            payload,
            current_head=_OTHER_HEAD,
            receipt_parent_sha=_DEFAULT_HEAD,
        )
        self.assertEqual(result.classification, CLASSIFICATION_ALREADY_CLEAN)
        self.assertFalse(result.head_has_moved)
        self.assertEqual(result.head_movement_classification, "managed_receipt")
        self.assertEqual(result.managed_receipt_parent_sha, _DEFAULT_HEAD)

    def test_head_drift_on_recoverable_maps_to_needs_recover(self) -> None:
        payload = _sample_payload(state="commit_recorded")
        result = classify_pipeline(payload, current_head=_OTHER_HEAD)
        self.assertEqual(result.classification, CLASSIFICATION_NEEDS_RECOVER)
        self.assertTrue(result.head_has_moved)

    def test_push_blocked_maps_to_needs_abandon(self) -> None:
        payload = _sample_payload(state="push_blocked")
        result = classify_pipeline(payload, current_head=_DEFAULT_HEAD)
        self.assertEqual(result.classification, CLASSIFICATION_NEEDS_ABANDON)

    def test_expired_auth_head_matches_needs_refresh(self) -> None:
        payload = _sample_payload(
            state="commit_recorded",
            expires_at_utc="2000-01-01T00:00:00.000000Z",
        )
        result = classify_pipeline(payload, current_head=_DEFAULT_HEAD)
        self.assertEqual(
            result.classification,
            CLASSIFICATION_NEEDS_REFRESH_AUTHORIZATION,
        )
        self.assertTrue(result.authorization_expired)

    def test_healthy_live_is_already_clean(self) -> None:
        payload = _sample_payload(state="push_pending")
        result = classify_pipeline(payload, current_head=_DEFAULT_HEAD)
        self.assertEqual(result.classification, CLASSIFICATION_ALREADY_CLEAN)
        self.assertFalse(result.head_has_moved)
        self.assertFalse(result.authorization_expired)

    def test_unknown_state_is_ambiguous(self) -> None:
        payload = _sample_payload(state="some_future_state")
        result = classify_pipeline(payload, current_head=_DEFAULT_HEAD)
        self.assertEqual(result.classification, CLASSIFICATION_AMBIGUOUS)
        self.assertTrue(result.reason.startswith("no_classification_rule_matched:"))


# ----- Composite runner tests --------------------------------------


class PipelineAutoRecoverRunnerTests(unittest.TestCase):
    def test_already_clean_no_pipeline_emits_noop_receipt(self) -> None:
        fx = _PipelineFixture()
        try:
            result = apply_auto_recover(paths=fx.paths())
            self.assertTrue(result["ok"])
            self.assertEqual(result["chosen_action"], CHOSEN_ACTION_NONE)
            self.assertEqual(
                result["classification"]["classification"],
                CLASSIFICATION_ALREADY_CLEAN,
            )
            receipt = fx.read_composite_receipt()
            self.assertEqual(receipt["chosen_action"], CHOSEN_ACTION_NONE)
            self.assertEqual(
                receipt["classification"],
                CLASSIFICATION_ALREADY_CLEAN,
            )
        finally:
            fx.close()

    def test_needs_abandon_dispatches_abandon(self) -> None:
        fx = _PipelineFixture()
        try:
            fx.write_payload(_sample_payload(state="push_blocked"))
            result = apply_auto_recover(paths=fx.paths())
            self.assertTrue(result["ok"])
            self.assertEqual(result["chosen_action"], CHOSEN_ACTION_ABANDON)
            self.assertEqual(result["new_state"], "abandoned")
            # Composite receipt records the sub-receipt.
            self.assertTrue(result["sub_receipt_path"])
            self.assertTrue(Path(result["sub_receipt_path"]).exists())
        finally:
            fx.close()

    def test_needs_recover_dispatches_recover(self) -> None:
        fx = _PipelineFixture(fake_head=_OTHER_HEAD)
        try:
            fx.write_payload(_sample_payload(state="commit_recorded"))
            result = apply_auto_recover(paths=fx.paths())
            self.assertTrue(result["ok"])
            self.assertEqual(result["chosen_action"], CHOSEN_ACTION_RECOVER)
            sub = result["sub_action_result"] or {}
            self.assertEqual(
                sub.get("new_authorized_head_sha"),
                _OTHER_HEAD,
            )
        finally:
            fx.close()

    def test_needs_refresh_dispatches_refresh_authorization(self) -> None:
        fx = _PipelineFixture()
        try:
            fx.write_payload(
                _sample_payload(
                    state="commit_recorded",
                    expires_at_utc="2000-01-01T00:00:00.000000Z",
                )
            )
            result = apply_auto_recover(paths=fx.paths())
            self.assertTrue(result["ok"])
            self.assertEqual(
                result["chosen_action"],
                CHOSEN_ACTION_REFRESH_AUTHORIZATION,
            )
            sub = result["sub_action_result"] or {}
            self.assertTrue(sub.get("new_authorization_id"))
            self.assertNotEqual(
                sub.get("new_authorization_id"),
                sub.get("previous_authorization_id"),
            )
        finally:
            fx.close()

    def test_ambiguous_bails_without_mutation(self) -> None:
        fx = _PipelineFixture()
        try:
            fx.write_payload(_sample_payload(state="exotic_unknown_state"))
            original = (fx.pipeline_root / PIPELINE_FILENAME).read_text()
            result = apply_auto_recover(paths=fx.paths())
            self.assertFalse(result["ok"])
            self.assertEqual(result["chosen_action"], CHOSEN_ACTION_BAILED)
            self.assertEqual(
                result["classification"]["classification"],
                CLASSIFICATION_AMBIGUOUS,
            )
            # Pipeline artifact must not have been rewritten.
            still = (fx.pipeline_root / PIPELINE_FILENAME).read_text()
            self.assertEqual(original, still)
            # Composite receipt still written so the bail is auditable.
            receipt = fx.read_composite_receipt()
            self.assertEqual(receipt["chosen_action"], CHOSEN_ACTION_BAILED)
        finally:
            fx.close()


# ----- Dataclass contract tests ------------------------------------


class PipelineAutoRecoveryContractTests(unittest.TestCase):
    def test_receipt_roundtrip_preserves_fields(self) -> None:
        receipt = PipelineAutoRecoveryReceipt(
            classification=CLASSIFICATION_NEEDS_ABANDON,
            chosen_action=CHOSEN_ACTION_ABANDON,
            reason="auto-recover: pipeline_state_push_blocked",
            pipeline_id="pipeline-auto-0042",
            previous_state="push_blocked",
            new_state="abandoned",
            operator_actor="operator",
            sub_receipt_path="/tmp/sub_receipt.json",
            artifact_paths=("/tmp/commit_pipeline.json",),
            generated_at_utc="2026-04-22T00:00:00.000000Z",
        )
        as_dict = receipt.to_dict()
        serialized = json.dumps(as_dict)
        restored = json.loads(serialized)
        self.assertEqual(restored["contract_id"], "PipelineAutoRecoveryReceipt")
        self.assertEqual(restored["schema_version"], 1)
        self.assertEqual(restored["classification"], CLASSIFICATION_NEEDS_ABANDON)
        self.assertEqual(restored["chosen_action"], CHOSEN_ACTION_ABANDON)
        self.assertEqual(restored["pipeline_id"], "pipeline-auto-0042")
        self.assertEqual(restored["previous_state"], "push_blocked")
        self.assertEqual(restored["new_state"], "abandoned")
        self.assertEqual(restored["sub_receipt_path"], "/tmp/sub_receipt.json")
        self.assertEqual(
            restored["artifact_paths"],
            ["/tmp/commit_pipeline.json"],
        )

    def test_receipt_rejects_invalid_classification(self) -> None:
        with self.assertRaises(ValueError):
            PipelineAutoRecoveryReceipt(
                classification="not_a_real_classification",
                chosen_action=CHOSEN_ACTION_NONE,
                reason="x",
                pipeline_id="p",
                previous_state="",
                new_state="",
                operator_actor="operator",
                generated_at_utc="2026-04-22T00:00:00.000000Z",
            )

    def test_classification_rejects_invalid_value(self) -> None:
        with self.assertRaises(ValueError):
            PipelineAutoRecoveryClassification(
                classification="garbage",
                reason="x",
                pipeline_state="",
                head_has_moved=False,
                authorization_expired=False,
            )

    def test_classification_to_dict_returns_typed_record(self) -> None:
        classification = PipelineAutoRecoveryClassification(
            classification=CLASSIFICATION_ALREADY_CLEAN,
            reason="no_pipeline_artifact",
            pipeline_state="",
            head_has_moved=False,
            authorization_expired=False,
        )
        self.assertIsInstance(classification, PipelineAutoRecoveryClassification)
        self.assertEqual(classification.to_dict()["contract_id"],
                         "PipelineAutoRecoveryClassification")
        self.assertIn("head_movement_classification", classification.to_dict())


if __name__ == "__main__":
    unittest.main()
