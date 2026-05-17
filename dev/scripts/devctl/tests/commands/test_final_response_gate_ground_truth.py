"""Integration tests for ground-truth probe gate wired into final_response_gate.

Slice 3 of R313 A8: verifies that ``enforce_final_response_gate`` denies a
final response when a recent GroundTruthProbeRunReceipt is missing/stale and
allows it when the receipt is fresh and satisfied.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from dev.scripts.devctl.commands.development.final_response_gate import (
    enforce_final_response_gate,
)
from dev.scripts.devctl.commands.development.orchestration_models import (
    DevelopmentContinuationRequiredSignal,
)
from dev.scripts.devctl.runtime.ground_truth_probe_receipt import (
    GroundTruthProbeRunInput,
    append_ground_truth_probe_receipt,
    build_ground_truth_probe_receipt,
)


def _allow_continuation() -> DevelopmentContinuationRequiredSignal:
    return DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )


def _write_receipt(
    repo_root: Path,
    *,
    created_at_utc: str,
    trigger_paths: tuple[str, ...] = ("dev/scripts/devctl/runtime/example.py",),
    verdict: str = "satisfied",
) -> None:
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
    append_ground_truth_probe_receipt(overridden, repo_root=repo_root)


def test_final_response_blocked_when_receipt_missing(tmp_path: Path) -> None:
    result = enforce_final_response_gate(
        _allow_continuation(),
        repo_root=tmp_path,
        next_slice_id="MP-NEW-GROUND-TRUTH-S3",
    )
    assert result.allow_final_response is False
    assert result.source == "ground_truth_probe_receipt"
    assert result.reason == (
        "ground_truth_probe_receipt:ground_truth_probe_receipt_missing"
    )
    assert result.continuation_state == "must_continue"
    assert result.continuation_goal == "MP-NEW-GROUND-TRUTH-S3"
    assert result.gate_failure is not None
    assert result.gate_failure.gate_id == "ground_truth_probe_receipt.recent"
    assert "ground-truth-probe" in result.next_required_command


def test_final_response_allowed_when_receipt_fresh(tmp_path: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
    created = (now - timedelta(seconds=30)).isoformat().replace("+00:00", "Z")
    _write_receipt(tmp_path, created_at_utc=created)
    result = enforce_final_response_gate(
        _allow_continuation(),
        repo_root=tmp_path,
        now_utc=now,
    )
    assert result.allow_final_response is True
    assert result.source == "continuation_signal"


def test_final_response_blocked_when_receipt_stale(tmp_path: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
    created = (now - timedelta(seconds=3600)).isoformat().replace("+00:00", "Z")
    _write_receipt(tmp_path, created_at_utc=created)
    result = enforce_final_response_gate(
        _allow_continuation(),
        repo_root=tmp_path,
        now_utc=now,
    )
    assert result.allow_final_response is False
    assert result.reason == (
        "ground_truth_probe_receipt:ground_truth_probe_receipt_stale"
    )
    assert "stale" in result.why_not_done.lower()


def test_ground_truth_block_not_applied_when_repo_root_absent(tmp_path: Path) -> None:
    # When the caller does not pass repo_root, the new block is skipped so
    # existing callers keep their behavior; final response is allowed.
    result = enforce_final_response_gate(_allow_continuation())
    assert result.allow_final_response is True
    assert result.source == "continuation_signal"
