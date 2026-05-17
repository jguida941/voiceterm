"""Tests for the ground-truth probe gate."""

from dev.scripts.checks.ground_truth_probe_gate.command import _violations
from dev.scripts.devctl.runtime.ground_truth_probe_receipt import (
    GroundTruthProbeRunInput,
    build_ground_truth_probe_receipt,
)


def test_ground_truth_probe_gate_passes_matching_receipt() -> None:
    receipt = build_ground_truth_probe_receipt(
        GroundTruthProbeRunInput(
            trigger_paths=("dev/scripts/devctl/runtime/new_contract.py",),
            design_ids=("demo",),
            required_probe_ids=("runtime_truth_snapshot",),
            observed_probe_ids=("runtime_truth_snapshot",),
        )
    )

    assert (
        _violations(
            trigger_paths=("dev/scripts/devctl/runtime/new_contract.py",),
            receipt=receipt,
        )
        == []
    )


def test_ground_truth_probe_gate_rejects_stale_receipt() -> None:
    receipt = build_ground_truth_probe_receipt(
        GroundTruthProbeRunInput(
            trigger_paths=("dev/scripts/devctl/runtime/old_contract.py",),
            design_ids=("demo",),
            required_probe_ids=("runtime_truth_snapshot",),
            observed_probe_ids=("runtime_truth_snapshot",),
        )
    )

    assert "stale_ground_truth_probe_receipt" in _violations(
        trigger_paths=("dev/scripts/devctl/runtime/new_contract.py",),
        receipt=receipt,
    )


def test_ground_truth_probe_gate_rejects_missing_required_probe() -> None:
    receipt = build_ground_truth_probe_receipt(
        GroundTruthProbeRunInput(
            trigger_paths=("dev/scripts/devctl/runtime/new_contract.py",),
            design_ids=("demo",),
            required_probe_ids=("runtime_truth_snapshot", "agent_mind"),
            observed_probe_ids=("runtime_truth_snapshot",),
        )
    )

    violations = _violations(
        trigger_paths=("dev/scripts/devctl/runtime/new_contract.py",),
        receipt=receipt,
    )

    assert "receipt_not_satisfied:missing" in violations
    assert "missing_required_probe:agent_mind" in violations
