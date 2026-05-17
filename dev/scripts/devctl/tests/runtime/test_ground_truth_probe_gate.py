"""Tests for the typed ground-truth probe receipt gate (Slice 3, R313 A8)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from dev.scripts.devctl.runtime.ground_truth_probe_gate import (
    DEFAULT_MAX_RECEIPT_AGE_SECONDS,
    GroundTruthProbeReceiptCheck,
    GroundTruthProbeReceiptFailureCode,
    require_recent_ground_truth_receipt,
)
from dev.scripts.devctl.runtime.ground_truth_probe_receipt import (
    DEFAULT_GROUND_TRUTH_RECEIPT_REL,
    GroundTruthProbeRunInput,
    append_ground_truth_probe_receipt,
    build_ground_truth_probe_receipt,
    trigger_paths_digest,
)


def _write_receipt(
    repo_root: Path,
    *,
    trigger_paths: tuple[str, ...],
    created_at_utc: str,
    verdict: str = "satisfied",
) -> Path:
    """Write one receipt row at a deterministic timestamp/verdict."""
    receipt = build_ground_truth_probe_receipt(
        GroundTruthProbeRunInput(
            trigger_paths=trigger_paths,
            required_probe_ids=("runtime_truth_snapshot",),
            observed_probe_ids=("runtime_truth_snapshot",),
        ),
    )
    overridden = type(receipt)(
        schema_version=receipt.schema_version,
        contract_id=receipt.contract_id,
        created_at_utc=created_at_utc,
        base_ref=receipt.base_ref,
        head_ref=receipt.head_ref,
        changed_paths_digest=receipt.changed_paths_digest,
        trigger_kind=receipt.trigger_kind,
        trigger_paths=receipt.trigger_paths,
        design_ids=receipt.design_ids,
        required_probe_ids=receipt.required_probe_ids,
        observed_probe_ids=receipt.observed_probe_ids,
        probe_report_path=receipt.probe_report_path,
        probe_report_sha256=receipt.probe_report_sha256,
        verdict=verdict,
        warnings=receipt.warnings,
    )
    return append_ground_truth_probe_receipt(overridden, repo_root=repo_root)


def test_missing_receipt_returns_missing_failure(tmp_path: Path) -> None:
    check = require_recent_ground_truth_receipt(
        repo_root=tmp_path,
        slice_id="MP-NEW-GROUND-TRUTH-S3",
    )
    assert check.ok is False
    assert check.failure_code == (
        GroundTruthProbeReceiptFailureCode.GROUND_TRUTH_PROBE_RECEIPT_MISSING
    )
    assert check.receipt is None
    assert check.slice_id == "MP-NEW-GROUND-TRUTH-S3"
    assert check.age_seconds == -1


def test_fresh_satisfied_receipt_passes(tmp_path: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
    created = (now - timedelta(seconds=60)).isoformat().replace("+00:00", "Z")
    _write_receipt(
        tmp_path,
        trigger_paths=("dev/scripts/devctl/runtime/example.py",),
        created_at_utc=created,
        verdict="satisfied",
    )
    check = require_recent_ground_truth_receipt(
        repo_root=tmp_path,
        slice_id="s",
        now_utc=now,
    )
    assert check.ok is True
    assert check.failure_code == GroundTruthProbeReceiptFailureCode.OK
    assert check.age_seconds == 60
    assert check.receipt is not None


def test_stale_receipt_returns_stale(tmp_path: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
    created = (now - timedelta(seconds=DEFAULT_MAX_RECEIPT_AGE_SECONDS + 60)).isoformat().replace(
        "+00:00", "Z"
    )
    _write_receipt(
        tmp_path,
        trigger_paths=("dev/scripts/devctl/runtime/example.py",),
        created_at_utc=created,
        verdict="satisfied",
    )
    check = require_recent_ground_truth_receipt(
        repo_root=tmp_path,
        now_utc=now,
    )
    assert check.ok is False
    assert check.failure_code == (
        GroundTruthProbeReceiptFailureCode.GROUND_TRUTH_PROBE_RECEIPT_STALE
    )
    assert check.age_seconds > DEFAULT_MAX_RECEIPT_AGE_SECONDS


def test_unsatisfied_verdict_returns_verdict_unsatisfied(tmp_path: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
    created = now.isoformat().replace("+00:00", "Z")
    _write_receipt(
        tmp_path,
        trigger_paths=("dev/scripts/devctl/runtime/example.py",),
        created_at_utc=created,
        verdict="missing",
    )
    check = require_recent_ground_truth_receipt(
        repo_root=tmp_path,
        now_utc=now,
    )
    assert check.ok is False
    assert check.failure_code == (
        GroundTruthProbeReceiptFailureCode.GROUND_TRUTH_PROBE_VERDICT_UNSATISFIED
    )
    assert check.receipt is not None
    assert check.receipt.verdict == "missing"


def test_trigger_mismatch_returns_mismatch(tmp_path: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
    created = now.isoformat().replace("+00:00", "Z")
    _write_receipt(
        tmp_path,
        trigger_paths=("dev/scripts/devctl/runtime/observed.py",),
        created_at_utc=created,
        verdict="satisfied",
    )
    check = require_recent_ground_truth_receipt(
        repo_root=tmp_path,
        now_utc=now,
        expected_trigger_paths=("dev/scripts/devctl/runtime/expected_other.py",),
    )
    assert check.ok is False
    assert check.failure_code == (
        GroundTruthProbeReceiptFailureCode.GROUND_TRUTH_PROBE_TRIGGER_MISMATCH
    )
    assert check.expected_digest != check.observed_digest


def test_matching_trigger_paths_pass(tmp_path: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
    created = now.isoformat().replace("+00:00", "Z")
    expected = ("dev/scripts/devctl/runtime/match.py",)
    _write_receipt(
        tmp_path,
        trigger_paths=expected,
        created_at_utc=created,
        verdict="satisfied",
    )
    check = require_recent_ground_truth_receipt(
        repo_root=tmp_path,
        now_utc=now,
        expected_trigger_paths=expected,
    )
    assert check.ok is True
    assert check.expected_digest == check.observed_digest
    assert check.expected_digest == trigger_paths_digest(expected)


def test_check_to_dict_serializes_failure_code(tmp_path: Path) -> None:
    check = require_recent_ground_truth_receipt(repo_root=tmp_path)
    payload = check.to_dict()
    assert payload["contract_id"] == "GroundTruthProbeReceiptCheck"
    assert payload["ok"] is False
    assert payload["failure_code"] == "ground_truth_probe_receipt_missing"
    assert payload["receipt"] is None
