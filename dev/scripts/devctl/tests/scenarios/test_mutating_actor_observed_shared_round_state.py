"""Scenario: a live mutating actor must have observed the shared round
state -- the actor's row must reference the current plan_row, name a
source event id, and carry a recent last_active_utc. Otherwise the
actor is mutating without peer awareness.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
_MUTATION_CAPS = frozenset({"repo.commit", "repo.stage", "repo.stage_handoff", "repo.write"})
_OBSERVATION_MAX_AGE_SECONDS = 24 * 60 * 60


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


def test_live_mutating_actor_carries_shared_round_evidence():
    output = _run_sync_status()
    rows = (output.get("work_board") or {}).get("rows") or []
    mutators = [r for r in rows if isinstance(r, dict) and _is_mutating(r) and str(r.get("status") or "") in {"working", "polling", "blocked"}]
    if not mutators:
        pytest.skip("no live mutating actors")
    now = datetime.now(tz=timezone.utc)
    violations: list[dict] = []
    for r in mutators:
        plan_row = str(r.get("plan_row_id") or "").strip()
        source_event = str(r.get("source_event_id") or "").strip()
        last_active = str(r.get("last_active_utc") or "").strip()
        if not (plan_row and source_event and last_active):
            violations.append({"actor": r.get("actor_id"), "missing": [k for k, v in (("plan_row_id", plan_row), ("source_event_id", source_event), ("last_active_utc", last_active)) if not v]})
            continue
        try:
            ts = datetime.fromisoformat(last_active.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except ValueError:
            violations.append({"actor": r.get("actor_id"), "reason": "last_active_utc unparseable", "value": last_active})
            continue
        age = (now - ts).total_seconds()
        if age > _OBSERVATION_MAX_AGE_SECONDS:
            violations.append({"actor": r.get("actor_id"), "reason": "last_active too old", "age_seconds": int(age)})
    assert not violations, (
        "live mutating actor missing shared-round evidence:\n" + "\n".join(f"  - {v}" for v in violations[:5])
    )
