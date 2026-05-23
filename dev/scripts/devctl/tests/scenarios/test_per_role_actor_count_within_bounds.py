"""Scenario: live actor counts per role must be reasonable -- at most
one live implementer per plan row, at most one live reviewer per plan
row. More than one live actor for the same (role, plan_row) without
a typed coordinator is the silent drift the cardinality guard exists
to catch.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]


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


def test_each_role_per_plan_row_has_at_most_one_live_actor():
    output = _run_sync_status()
    rows = (output.get("work_board") or {}).get("rows") or []
    if not rows:
        pytest.skip("work_board has no rows")

    counts: Counter[tuple[str, str]] = Counter()
    actors_seen: dict[tuple[str, str], list[str]] = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        if str(r.get("status") or "") not in {"working", "polling", "blocked"}:
            continue
        role = str(r.get("role") or "").strip().lower()
        plan_row = str(r.get("plan_row_id") or "").strip()
        if not role or not plan_row:
            continue
        key = (role, plan_row)
        counts[key] += 1
        actors_seen.setdefault(key, []).append(str(r.get("actor_id") or "?"))

    violations = [(role, row, n, actors_seen[(role, row)]) for (role, row), n in counts.items() if n > 1]
    assert not violations, (
        "more than one live actor for the same (role, plan_row) without "
        "typed coordinator:\n"
        + "\n".join(
            f"  - role={role!r} plan_row={row!r} count={n} actors={actors!r}"
            for role, row, n, actors in violations[:5]
        )
    )
