"""Tests for observed review-channel control topology derivation."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from dev.scripts.devctl.commands.governance.startup_context import _render_summary
from dev.scripts.devctl.runtime.control_topology import (
    derive_implementation_permission,
    derive_observed_control_topology,
    derive_startup_control_truth,
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
        ("single_agent", "active"),
        ("dual_implementer", "suspended"),
        ("implementer_without_reviewer", "suspended"),
        ("reviewer_only", "blocked"),
        ("no_live_agents", "blocked"),
    ),
)
def test_derive_implementation_permission(topology: str, expected: str) -> None:
    assert derive_implementation_permission(topology) == expected


def test_derive_startup_control_truth_promotes_local_single_agent_takeover() -> None:
    review_state = SimpleNamespace(
        bridge={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "codex_conductor_active": True,
            "claude_conductor_active": False,
        },
        collaboration={"participants": ()},
        reviewer_runtime=SimpleNamespace(
            reviewer_mode="single_agent",
            effective_reviewer_mode="single_agent",
            remote_control_attachment=SimpleNamespace(status="detached"),
        ),
    )
    reviewer_gate = SimpleNamespace(
        reviewer_mode="single_agent",
        effective_reviewer_mode="single_agent",
        operator_interaction_mode="local_terminal",
    )

    topology, permission = derive_startup_control_truth(
        review_state,
        reviewer_gate=reviewer_gate,
    )

    assert topology == "single_agent"
    assert permission == "active"


def test_derive_startup_control_truth_prefers_single_agent_over_stale_pair_evidence() -> None:
    review_state = SimpleNamespace(
        bridge={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "codex_conductor_active": True,
            "claude_conductor_active": True,
        },
        collaboration={"participants": ()},
        reviewer_runtime=SimpleNamespace(
            reviewer_mode="single_agent",
            effective_reviewer_mode="single_agent",
            remote_control_attachment=SimpleNamespace(status="detached"),
        ),
    )
    reviewer_gate = SimpleNamespace(
        reviewer_mode="single_agent",
        effective_reviewer_mode="single_agent",
        operator_interaction_mode="local_terminal",
    )

    topology, permission = derive_startup_control_truth(
        review_state,
        reviewer_gate=reviewer_gate,
    )

    assert topology == "single_agent"
    assert permission == "active"


def test_derive_startup_control_truth_allows_remote_control_single_agent() -> None:
    review_state = SimpleNamespace(
        bridge={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "codex_conductor_active": True,
            "claude_conductor_active": False,
        },
        collaboration={"participants": ()},
        reviewer_runtime=SimpleNamespace(
            reviewer_mode="single_agent",
            effective_reviewer_mode="single_agent",
            remote_control_attachment=SimpleNamespace(status="attached"),
        ),
    )
    reviewer_gate = SimpleNamespace(
        reviewer_mode="single_agent",
        effective_reviewer_mode="single_agent",
        operator_interaction_mode="remote_control",
    )

    topology, permission = derive_startup_control_truth(
        review_state,
        reviewer_gate=reviewer_gate,
    )

    assert topology == "single_agent"
    assert permission == "active"


def test_derive_startup_control_truth_promotes_remote_single_agent_over_implementer_only(
) -> None:
    review_state = SimpleNamespace(
        bridge={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "codex_conductor_active": False,
            "claude_conductor_active": True,
        },
        collaboration={"participants": ()},
        reviewer_runtime=SimpleNamespace(
            reviewer_mode="single_agent",
            effective_reviewer_mode="single_agent",
            remote_control_attachment=SimpleNamespace(status="attached"),
        ),
    )
    reviewer_gate = SimpleNamespace(
        reviewer_mode="single_agent",
        effective_reviewer_mode="single_agent",
        operator_interaction_mode="remote_control",
    )

    topology, permission = derive_startup_control_truth(
        review_state,
        reviewer_gate=reviewer_gate,
    )

    assert topology == "single_agent"
    assert permission == "active"


def test_derive_startup_control_truth_keeps_typed_live_pair_visible() -> None:
    review_state = SimpleNamespace(
        bridge={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "codex_conductor_active": True,
            "claude_conductor_active": False,
        },
        collaboration={
            "participants": (
                {"provider": "codex", "role": "reviewer", "live": True},
                {"provider": "claude", "role": "implementer", "live": True},
            ),
            "role_assignments": (
                {"role_id": "review_agent", "provider": "codex", "live": True},
                {"role_id": "coding_agent", "provider": "claude", "live": True},
            ),
        },
        reviewer_runtime=SimpleNamespace(
            reviewer_mode="single_agent",
            effective_reviewer_mode="single_agent",
            remote_control_attachment=SimpleNamespace(status="detached"),
        ),
    )
    reviewer_gate = SimpleNamespace(
        reviewer_mode="single_agent",
        effective_reviewer_mode="single_agent",
        operator_interaction_mode="local_terminal",
    )

    topology, permission = derive_startup_control_truth(
        review_state,
        reviewer_gate=reviewer_gate,
    )

    assert topology == "single_implementer_single_reviewer"
    assert permission == "active"


def test_derive_startup_control_truth_ignores_operator_only_implementer_assignment(
) -> None:
    review_state = SimpleNamespace(
        bridge={
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "tools_only",
            "codex_conductor_active": True,
            "claude_conductor_active": True,
        },
        collaboration={
            "participants": (
                {"provider": "codex", "role": "reviewer", "live": True},
                {"provider": "claude", "role": "operator", "live": True},
            ),
            "role_assignments": (
                {"role_id": "review_agent", "provider": "codex", "live": True},
                {"role_id": "coding_agent", "provider": "claude", "live": True},
                {"role_id": "operator_agent", "provider": "claude", "live": True},
            ),
        },
        reviewer_runtime=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            effective_reviewer_mode="tools_only",
            remote_control_attachment=SimpleNamespace(status="attached"),
        ),
    )
    reviewer_gate = SimpleNamespace(
        reviewer_mode="active_dual_agent",
        effective_reviewer_mode="tools_only",
        operator_interaction_mode="remote_control",
    )

    topology, permission = derive_startup_control_truth(
        review_state,
        reviewer_gate=reviewer_gate,
    )

    assert topology == "reviewer_only"
    assert permission == "blocked"


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
