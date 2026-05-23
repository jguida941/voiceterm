"""Scenario: when two child actors hold overlapping path_scope, the
projection must surface a typed conflict marker -- a shared
authority_refs entry or a typed conflict_disposition field. Otherwise
the conflict is invisible and one child silently overwrites the
other.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from itertools import combinations
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]


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


def test_overlapping_child_scopes_carry_typed_conflict_authority():
    output = _run_sync_status()
    rows = (output.get("work_board") or {}).get("rows") or []
    children = [
        r
        for r in rows
        if isinstance(r, dict)
        and str(r.get("parent_agent_id") or "").strip()
        and str(r.get("parent_agent_id") or "").strip().lower() != "operator"
    ]
    if len(children) < 2:
        pytest.skip(f"only {len(children)} child actor(s); no overlap possible")
    violations: list[dict] = []
    for a, b in combinations(children, 2):
        scope_a = set(a.get("path_scope") or [])
        scope_b = set(b.get("path_scope") or [])
        shared = scope_a & scope_b
        if not shared:
            continue
        refs_a = set(a.get("authority_refs") or [])
        refs_b = set(b.get("authority_refs") or [])
        if refs_a & refs_b:
            continue
        violations.append({
            "actor_a": a.get("actor_id"),
            "actor_b": b.get("actor_id"),
            "shared_paths": sorted(shared),
        })
    assert not violations, (
        "two children overlap in path_scope with no shared authority refs:\n"
        + "\n".join(f"  - {v}" for v in violations[:5])
    )
