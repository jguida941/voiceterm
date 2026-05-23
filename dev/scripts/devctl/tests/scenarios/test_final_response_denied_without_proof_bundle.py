"""Scenario: the final-response gate must refuse final response while
the current plan row is still in progress and no FeatureProofReceipt
with real_life_test_status=proven_passed exists for that row.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]


def _run_develop_next() -> dict:
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "develop", "next",
            "--actor", "codex",
            "--enforce-final-response-gate",
            "--format", "json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )
    return json.loads(result.stdout)


def _row_has_proven_passed_fpr(row_id: str) -> bool:
    fpr_dir = REPO_ROOT / "dev" / "reports" / "feature_proof_receipts"
    if not fpr_dir.exists():
        return False
    for path in fpr_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if str(data.get("real_life_test_status") or "") != "proven_passed":
            continue
        # FPR may reference the row via row_id, plan_row_id, or evidence_artifacts
        if str(data.get("row_id") or "") == row_id:
            return True
        if str(data.get("plan_row_id") or "") == row_id:
            return True
    return False


def test_final_response_denied_while_current_row_lacks_proven_passed_fpr():
    output = _run_develop_next()
    cpa = output.get("current_plan_authority") or {}
    plan_row = str(cpa.get("plan_row_id") or "").strip()
    if not plan_row:
        pytest.skip("no current plan-row authority")
    if _row_has_proven_passed_fpr(plan_row):
        pytest.skip(f"row {plan_row!r} already has a proven_passed FPR")
    gate = output.get("final_response_gate") or {}
    allow = bool(gate.get("allow_final_response", True))
    assert not allow, (
        "final-response gate is allowing final response while the current "
        "plan row has no proven_passed FPR.\n"
        f"  plan_row:               {plan_row!r}\n"
        f"  gate.allow_final_response: {allow}\n"
        f"  gate.source:            {gate.get('source')!r}\n"
        f"  gate.reason:            {gate.get('reason')!r}"
    )
