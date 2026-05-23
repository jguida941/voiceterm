"""Scenario: when more than one mutation-capable actor is live, the
work_board projection must surface each peer's path_scope so an actor
can see what its peers are holding before it tries to write. If the
projection drops peer lease info, an actor edits over its peer
without knowing.
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


def _is_mutating(row: dict) -> bool:
    if str(row.get("mutation_mode") or "") == "live_tree":
        return True
    caps = row.get("granted_capabilities") or []
    return isinstance(caps, list) and any(c in _MUTATION_CAPS for c in caps)


def test_peer_mutating_actors_carry_path_scope_for_visibility():
    output = _run_sync_status()
    rows = (output.get("work_board") or {}).get("rows") or []
    mutators = [r for r in rows if isinstance(r, dict) and _is_mutating(r) and str(r.get("status") or "") in {"working", "polling", "blocked"}]
    if len(mutators) < 2:
        pytest.skip(f"only {len(mutators)} live mutator(s); peer visibility scope not exercised")
    missing_scope = [r for r in mutators if not (r.get("path_scope") or [])]
    assert not missing_scope, (
        "live mutating actor has empty path_scope, so peers cannot see "
        "what it holds:\n" + "\n".join(f"  - actor={r.get('actor_id')!r}" for r in missing_scope[:5])
    )
