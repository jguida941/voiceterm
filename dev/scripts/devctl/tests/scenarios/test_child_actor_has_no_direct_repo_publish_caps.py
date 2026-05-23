"""Scenario: a child actor (row with parent_agent_id set) must not
carry repo.push or repo.commit capability directly. Publish travels
through the parent's transport/approval lane. A child that can
commit/push bypasses the parent merge gate.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
_PUBLISH_CAPS = frozenset({"repo.commit", "repo.push"})


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


def test_child_actor_must_not_hold_publish_capability_directly():
    output = _run_sync_status()
    rows = (output.get("work_board") or {}).get("rows") or []
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
        caps = set(child.get("granted_capabilities") or []) & _PUBLISH_CAPS
        if caps:
            violations.append({"child": child.get("actor_id"), "leaked_publish_caps": sorted(caps)})
    assert not violations, (
        "child actor holds publish capability directly:\n"
        + "\n".join(f"  - {v}" for v in violations[:5])
    )
