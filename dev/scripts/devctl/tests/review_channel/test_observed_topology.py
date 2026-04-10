"""Tests for observed review-channel control topology derivation."""

from __future__ import annotations

import pytest

from dev.scripts.devctl.commands.governance.startup_context import _render_summary
from dev.scripts.devctl.runtime.control_topology import (
    derive_implementation_permission,
    derive_observed_control_topology,
)


@pytest.mark.parametrize(
    (
        "live_reviewer_count",
        "live_implementer_count",
        "supervised_conductor_count",
        "expected",
    ),
    (
        (1, 1, 2, "single_implementer_single_reviewer"),
        (1, 2, 3, "dual_implementer"),
        (0, 1, 1, "implementer_without_reviewer"),
        (1, 1, 0, "implementer_without_reviewer"),
        (1, 0, 1, "reviewer_only"),
        (0, 0, 0, "no_live_agents"),
        (0, 0, 2, "no_live_agents"),
    ),
)
def test_derive_observed_control_topology_from_counts(
    live_reviewer_count: int,
    live_implementer_count: int,
    supervised_conductor_count: int,
    expected: str,
) -> None:
    assert (
        derive_observed_control_topology(
            live_reviewer_count,
            live_implementer_count,
            supervised_conductor_count,
        )
        == expected
    )


def test_derive_observed_control_topology_uses_bridge_runtime_evidence() -> None:
    topology = derive_observed_control_topology(
        supervised_conductor_count=2,
        bridge_liveness={
            "codex_conductor_active": True,
            "claude_conductor_active": True,
        },
        runtime_counts={
            "live_reviewer_count": 1,
            "live_implementer_count": 1,
        },
    )

    assert topology == "single_implementer_single_reviewer"


@pytest.mark.parametrize(
    ("topology", "expected"),
    (
        ("single_implementer_single_reviewer", "active"),
        ("dual_implementer", "suspended"),
        ("implementer_without_reviewer", "suspended"),
        ("reviewer_only", "blocked"),
        ("no_live_agents", "blocked"),
    ),
)
def test_derive_implementation_permission(topology: str, expected: str) -> None:
    assert derive_implementation_permission(topology) == expected


def test_startup_summary_includes_observed_control_topology() -> None:
    rendered = _render_summary(
        {
            "advisory_action": "repair_reviewer_loop",
            "advisory_reason": "reviewer_overdue",
            "observed_control_topology": "implementer_without_reviewer",
            "implementation_permission": "suspended",
            "reviewer_gate": {
                "implementation_blocked": True,
                "implementation_block_reason": "reviewer_overdue",
                "review_gate_allows_push": False,
            },
            "startup_authority": {"ok": False},
            "governance": {
                "push_enforcement": {
                    "checkpoint_required": False,
                    "safe_to_continue_editing": True,
                },
            },
            "push_decision": {
                "action": "await_review",
                "next_step_command": "",
            },
        }
    )

    assert "observed_control_topology=implementer_without_reviewer" in rendered
    assert "implementation_permission=suspended" in rendered
