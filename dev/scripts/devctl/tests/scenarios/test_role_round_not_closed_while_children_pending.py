"""Scenario: a current plan-row whose status indicates closure
(applied / completed / closed) must not have any live child actors
still working on it. Closure with pending children is silent
incompleteness.
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
_CLOSURE_STATUSES = {"applied", "completed", "closed", "archived"}


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


def _live_plan_rows() -> dict[str, str]:
    """Return {plan_row_id: status} for every row in the typed plan ledger."""
    path = REPO_ROOT / "dev" / "state" / "plan_index.jsonl"
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid = str(row.get("row_id") or "").strip()
        if rid:
            out[rid] = str(row.get("status") or "").strip().lower()
    return out


def test_closed_plan_row_has_no_live_child_actors():
    sync = _run_sync_status()
    rows = (sync.get("work_board") or {}).get("rows") or []
    if not rows:
        pytest.skip("work_board has no rows")
    plan_status = _live_plan_rows()
    children = [
        r
        for r in rows
        if isinstance(r, dict)
        and str(r.get("parent_agent_id") or "").strip()
        and str(r.get("parent_agent_id") or "").strip().lower() != "operator"
        and str(r.get("status") or "") in {"working", "polling", "blocked"}
    ]
    if not children:
        pytest.skip("no live child actors")
    violations: list[dict] = []
    for child in children:
        plan_row = str(child.get("plan_row_id") or "").strip()
        status = plan_status.get(plan_row, "")
        if status in _CLOSURE_STATUSES:
            violations.append({"child": child.get("actor_id"), "plan_row": plan_row, "plan_status": status})
    assert not violations, (
        "live child actor is still working on a plan row that is already "
        "marked closed:\n" + "\n".join(f"  - {v}" for v in violations[:5])
    )
