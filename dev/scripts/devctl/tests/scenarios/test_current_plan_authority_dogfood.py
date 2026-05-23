"""Dogfood scenario for the CurrentPlanAuthority scheduler seam."""

from __future__ import annotations

import json
import subprocess
import sys

from dev.scripts.checks.current_plan_authority.command import (
    evaluate_current_plan_authority,
)
from dev.scripts.devctl.config import REPO_ROOT


def test_current_plan_authority_guard_passes_live_repo_state() -> None:
    report = evaluate_current_plan_authority(repo_root=REPO_ROOT)

    assert report.ok, report.violations
    assert report.current_plan_row_id
    assert not report.current_plan_row_id.startswith("PKT-BIND-")
    assert report.check_router_registered is True
    assert report.bundle_registered is True


def test_develop_next_exposes_current_plan_authority_live() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "develop",
            "next",
            "--actor",
            "codex",
            "--format",
            "json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr[-2000:]
    payload = json.loads(completed.stdout)
    authority = payload.get("current_plan_authority")
    assert isinstance(authority, dict)
    row_id = str(authority.get("plan_row_id") or "")
    assert row_id
    assert not row_id.startswith("PKT-BIND-")
    next_slice = payload.get("next_slice")
    assert isinstance(next_slice, dict)
    slice_id = str(next_slice.get("slice_id") or "")
    assert not slice_id.startswith("PKT-BIND-")
    assert not (
        row_id
        and slice_id.startswith(("rev_pkt_", "pkt_", "packet:"))
    )
    campaign = payload.get("campaign")
    assert isinstance(campaign, dict)
    roles = campaign.get("roles")
    assert isinstance(roles, list)
    role_pairs = {
        (
            str(role.get("actor_id") or ""),
            str(role.get("role") or ""),
        )
        for role in roles
        if isinstance(role, dict)
    }
    assert ("codex", "reviewer") in role_pairs
    assert ("claude", "implementer") in role_pairs
    assert str(campaign.get("coordination_topology") or "")
    proof_requirements = campaign.get("proof_requirements")
    assert isinstance(proof_requirements, list)
    assert any("role" in str(item).lower() for item in proof_requirements)
