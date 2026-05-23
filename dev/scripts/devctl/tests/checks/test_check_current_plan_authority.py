"""Tests for the live CurrentPlanAuthority guard."""

from __future__ import annotations

from types import SimpleNamespace

from dev.scripts.checks.current_plan_authority.command import (
    CURRENT_ROW_ID,
    CurrentPlanAuthorityViolation,
    _check_authority_selection,
)
from dev.scripts.devctl.runtime.current_plan_authority import CurrentPlanAuthority


def test_guard_rejects_selection_that_skips_required_active_row() -> None:
    violations: list[CurrentPlanAuthorityViolation] = []

    _check_authority_selection(
        authority=CurrentPlanAuthority(
            plan_row_id="GUARDIR-EXTRACTION-MASTER-PLAN-2026-05-18-S1",
            plan_row_status="in_progress",
        ),
        executable_rows=(
            SimpleNamespace(
                row_id=CURRENT_ROW_ID,
                status="in_progress",
                row_kind="task",
            ),
        ),
        violations=violations,
    )

    assert {violation.reason for violation in violations} == {
        "current_plan_authority_selected_wrong_active_row"
    }
