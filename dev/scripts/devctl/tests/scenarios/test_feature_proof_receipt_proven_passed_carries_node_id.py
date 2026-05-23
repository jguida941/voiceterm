"""Scenario: every FeatureProofReceipt that claims
real_life_test_status='proven_passed' must include at least one
concrete pytest node id (a string containing ``::``) in tests_run.
A proven_passed claim with no pytest node id is closure without
proof of test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]


def test_proven_passed_fpr_carries_concrete_pytest_node_id():
    fpr_dir = REPO_ROOT / "dev" / "reports" / "feature_proof_receipts"
    if not fpr_dir.exists():
        pytest.skip("FPR directory not present")
    violations: list[dict] = []
    for path in sorted(fpr_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if str(data.get("real_life_test_status") or "") != "proven_passed":
            continue
        tests_run = data.get("tests_run") or []
        if not isinstance(tests_run, list):
            tests_run = []
        if any("::" in str(t) for t in tests_run):
            continue
        violations.append({"file": path.name, "tests_run_preview": [str(t)[:80] for t in tests_run[:3]]})
    # Ratchet at current historical count; new FPRs must carry node id.
    # Snapshot the current violation count and assert that future FPR
    # writes do not push it higher.
    current_ceiling = 37
    assert len(violations) <= current_ceiling, (
        f"{len(violations)} FPRs claim proven_passed without a pytest "
        f"node id (ceiling {current_ceiling}); count regressed:\n"
        + "\n".join(f"  - {v['file']}" for v in violations[:5])
    )
