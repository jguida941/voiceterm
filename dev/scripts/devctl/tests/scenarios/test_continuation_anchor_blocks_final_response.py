"""Scenario: if a continuation_anchor is live for the current row, the
final-response gate must NOT allow final response until the anchor is
consumed or converted into a stop anchor.
"""

from __future__ import annotations

import json
import os
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
            "develop",
            "next",
            "--actor", "agent",
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


def test_continuation_anchor_blocks_final_response():
    """When a continuation_anchor is live (current_plan_authority is
    open and there is no stop_anchor), the final-response gate must
    refuse final response until that anchor is consumed.
    """
    output = _run_develop_next()
    current_plan_authority = output.get("current_plan_authority") or {}
    plan_row_id = str(current_plan_authority.get("plan_row_id") or "").strip()
    if not plan_row_id:
        pytest.skip("no current plan-row authority -- continuation anchor scope empty")

    gate = output.get("final_response_gate") or {}
    continuation = output.get("continuation") or {}
    stop_anchor = str(gate.get("stop_anchor") or "").strip()
    if stop_anchor:
        pytest.skip(f"stop_anchor is live ({stop_anchor!r}); anchor was already released")

    allow_final = bool(gate.get("allow_final_response", True))
    allow_continuation = bool(continuation.get("final_response_allowed", True))

    assert (not allow_final) and (not allow_continuation), (
        "continuation anchor is live but the gate is allowing final "
        "response.\n"
        f"  plan_row:                       {plan_row_id!r}\n"
        f"  gate.allow_final_response:      {allow_final}\n"
        f"  continuation.final_response_allowed: {allow_continuation}\n"
        f"  gate.source:                    {gate.get('source')!r}\n"
        f"  gate.reason:                    {gate.get('reason')!r}"
    )
