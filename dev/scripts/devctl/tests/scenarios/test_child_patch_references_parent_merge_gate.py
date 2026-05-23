"""Scenario: a child actor must not act as if it can independently
land code. If a child actor row exists, the projection must either
name the parent merge coordinator OR the child must have no mutation
capability of its own. Child implementations that bypass the parent
merge gate land code with no integration check.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
_MUTATION_CAPS = frozenset({"repo.commit", "repo.stage", "repo.stage_handoff", "repo.write"})


def _run_sync_status() -> dict:
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    result = subprocess.run(
        [sys.executable, "dev/scripts/devctl.py", "review-channel", "--action", "sync-status", "--terminal", "none", "--format", "json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr[:300]
    return json.loads(result.stdout)


def test_child_actor_either_has_no_mutation_or_a_visible_parent():
    output = _run_sync_status()
    rows = (output.get("work_board") or {}).get("rows") or []
    by_id = {str(r.get("actor_id") or ""): r for r in rows if isinstance(r, dict)}
    children = [
        r
        for r in rows
        if isinstance(r, dict)
        and str(r.get("parent_agent_id") or "").strip()
        and str(r.get("parent_agent_id") or "").strip().lower() != "operator"
    ]
    if not children:
        pytest.skip("no child actor rows present")
    violations: list[dict] = []
    for child in children:
        parent_id = str(child.get("parent_agent_id") or "").strip()
        caps = set(child.get("granted_capabilities") or []) & _MUTATION_CAPS
        if not caps:
            continue
        if parent_id not in by_id:
            violations.append({"actor": child.get("actor_id"), "reason": "parent_not_visible", "parent_id": parent_id})
    assert not violations, (
        "child actor has mutation caps but its parent merge coordinator is "
        "not visible in the projection:\n" + "\n".join(f"  - {v}" for v in violations[:5])
    )
