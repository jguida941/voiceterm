"""Scenario: two live actors with mutation capability whose path_scope
sets overlap mean both could write the same file with no coordination.
The work_board row state must not allow that without a typed
coordinator. Without coordination, one writer silently overwrites
the other.
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
_MUTATION_CAPS = frozenset({"repo.commit", "repo.stage", "repo.stage_handoff", "repo.write"})


def _run_sync_status() -> dict:
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "review-channel",
            "--action", "sync-status",
            "--terminal", "none",
            "--format", "json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr[:300]
    return json.loads(result.stdout)


def _is_mutating(row: dict) -> bool:
    if str(row.get("mutation_mode") or "") == "live_tree":
        return True
    caps = row.get("granted_capabilities") or []
    if isinstance(caps, list) and any(c in _MUTATION_CAPS for c in caps):
        return True
    return False


def test_no_two_live_mutating_actors_share_path_scope():
    output = _run_sync_status()
    rows = (output.get("work_board") or {}).get("rows") or []
    mutators = [
        r
        for r in rows
        if isinstance(r, dict)
        and str(r.get("status") or "") in {"working", "polling", "blocked"}
        and _is_mutating(r)
    ]
    if len(mutators) < 2:
        pytest.skip(f"only {len(mutators)} live mutating actor(s); no overlap possible")

    overlaps: list[dict] = []
    for a, b in combinations(mutators, 2):
        scope_a = set(a.get("path_scope") or [])
        scope_b = set(b.get("path_scope") or [])
        if scope_a & scope_b:
            overlaps.append({
                "actor_a": str(a.get("actor_id") or ""),
                "actor_b": str(b.get("actor_id") or ""),
                "shared_paths": sorted(scope_a & scope_b),
            })

    assert not overlaps, (
        "two live mutating actors share path_scope without a typed merge "
        "coordinator:\n"
        + "\n".join(
            f"  - {o['actor_a']!r} and {o['actor_b']!r} share {o['shared_paths']!r}"
            for o in overlaps[:5]
        )
    )
