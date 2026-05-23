"""Scenario: a work_board row that names a parent actor (parent_agent_id
set) must also expose typed delegation evidence -- authority_refs and
role_scope. A child actor without delegation refs is acting on its
own authority instead of through the parent.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
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


def test_child_actor_row_carries_typed_delegation_evidence():
    output = _run_sync_status()
    rows = (output.get("work_board") or {}).get("rows") or []
    if not rows:
        pytest.skip("work_board has no rows")

    # A child sub-agent is one whose parent is another AI agent, not the
    # human operator. parent_agent_id=='operator' means the operator
    # attached this session directly; it is not a sub-agent spawn.
    child_rows = [
        r
        for r in rows
        if isinstance(r, dict)
        and str(r.get("parent_agent_id") or "").strip()
        and str(r.get("parent_agent_id") or "").strip().lower() != "operator"
    ]
    if not child_rows:
        pytest.skip("no AI-child-of-AI sub-agent rows present")

    violations: list[dict] = []
    for r in child_rows:
        authority_refs = r.get("authority_refs") or []
        role_scope = str(r.get("role_scope") or "").strip()
        if isinstance(authority_refs, list) and authority_refs and role_scope:
            continue
        violations.append({
            "actor_id": str(r.get("actor_id") or ""),
            "parent_agent_id": str(r.get("parent_agent_id") or ""),
            "authority_refs": authority_refs,
            "role_scope": role_scope,
        })

    assert not violations, (
        "child actor row lacks typed delegation evidence:\n"
        + "\n".join(
            f"  - actor={v['actor_id']!r} parent={v['parent_agent_id']!r} "
            f"authority_refs={v['authority_refs']!r} role_scope={v['role_scope']!r}"
            for v in violations[:5]
        )
    )
