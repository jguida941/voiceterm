"""Scenario: a child actor (a row with parent_agent_id set) must not
have a path_scope wider than its parent's path_scope, and must not
carry repo-mutation capabilities the parent didn't have.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
_MUTATION_CAPS = frozenset({"repo.commit", "repo.stage", "repo.stage_handoff", "repo.write", "repo.push"})


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


def test_child_scope_within_parent_scope():
    output = _run_sync_status()
    rows = (output.get("work_board") or {}).get("rows") or []
    if not rows:
        pytest.skip("work_board has no rows")
    by_actor = {str(r.get("actor_id") or ""): r for r in rows if isinstance(r, dict)}
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
        parent = by_actor.get(str(child.get("parent_agent_id") or ""))
        if not parent:
            violations.append({"reason": "parent_actor_not_visible", "child": child.get("actor_id"), "parent_ref": child.get("parent_agent_id")})
            continue
        c_scope = set(child.get("path_scope") or [])
        p_scope = set(parent.get("path_scope") or [])
        if not c_scope.issubset(p_scope):
            violations.append({"reason": "scope_exceeds_parent", "child": child.get("actor_id"), "extra": sorted(c_scope - p_scope)})
        c_caps = set(child.get("granted_capabilities") or []) & _MUTATION_CAPS
        p_caps = set(parent.get("granted_capabilities") or []) & _MUTATION_CAPS
        if not c_caps.issubset(p_caps):
            violations.append({"reason": "caps_exceed_parent", "child": child.get("actor_id"), "extra": sorted(c_caps - p_caps)})
    assert not violations, (
        "child actor scope or caps exceed parent:\n" + "\n".join(f"  - {v}" for v in violations[:5])
    )
