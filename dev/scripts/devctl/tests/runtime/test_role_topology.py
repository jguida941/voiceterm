"""Focused tests for role-based live topology resolution."""

from __future__ import annotations

from dev.scripts.devctl.runtime.role_topology import resolve_role_topology


def test_role_topology_allows_same_provider_multiple_typed_roles() -> None:
    topology = resolve_role_topology(
        {
            "active_conductor_providers": ["codex"],
            "collaboration": {
                "role_assignments": [
                    {
                        "provider": "codex",
                        "role_id": "architecture_review",
                        "live": True,
                    },
                    {
                        "provider": "codex",
                        "role_id": "implementation",
                        "live": True,
                    },
                ]
            },
        }
    )

    assert topology.providers_for_role("architecture_review") == ("codex",)
    assert topology.providers_for_role("implementation") == ("codex",)
    assert topology.live_reviewer_providers == ("codex",)
    assert topology.live_implementer_providers == ("codex",)
    assert topology.missing_required_roles == ()
    assert topology.typed_role_topology_label == (
        "typed_role_topology[architecture_review:codex;implementation:codex]"
    )


def test_role_topology_does_not_promote_capability_fields_to_roles() -> None:
    topology = resolve_role_topology(
        {
            "active_conductor_providers": ["codex"],
            "reviewer_capability": {"provider": "codex"},
            "implementer_capability": {"provider": "codex"},
        }
    )

    assert topology.role_occupancies == ()
    assert topology.live_reviewer_providers == ()
    assert topology.live_implementer_providers == ()
    assert topology.missing_required_roles == ("reviewer", "implementer")


def test_role_topology_uses_typed_role_signals_over_provider_defaults() -> None:
    topology = resolve_role_topology(
        {
            "active_conductor_providers": ["cursor"],
            "session_liveness_signals": [
                {"provider": "cursor", "role": "reviewer", "state": "alive"}
            ],
        }
    )

    assert topology.live_reviewer_providers == ("cursor",)
    assert topology.live_implementer_providers == ()
    assert topology.missing_required_roles == ("implementer",)


def test_role_topology_flip_flops_codex_and_claude_from_typed_state() -> None:
    topology = resolve_role_topology(
        {
            "active_conductor_providers": ["codex", "claude"],
            "session_liveness_signals": [
                {"provider": "codex", "role": "implementer", "state": "alive"},
                {"provider": "claude", "role": "reviewer", "state": "alive"},
            ],
        }
    )

    assert topology.live_reviewer_providers == ("claude",)
    assert topology.live_implementer_providers == ("codex",)
    assert topology.missing_required_roles == ()


def test_role_topology_fails_closed_without_typed_role_evidence() -> None:
    topology = resolve_role_topology(
        {
            "active_conductor_providers": ["codex", "claude"],
            "codex_conductor_active": True,
            "claude_conductor_active": True,
        }
    )

    assert topology.active_providers == ("codex", "claude")
    assert topology.live_reviewer_providers == ()
    assert topology.live_implementer_providers == ()
    assert topology.missing_required_roles == ("reviewer", "implementer")


def test_role_topology_reads_role_assignments_as_authority() -> None:
    topology = resolve_role_topology(
        {
            "active_conductor_providers": ["codex", "claude"],
            "collaboration": {
                "role_assignments": [
                    {"provider": "claude", "role_id": "review_agent", "live": True},
                    {"provider": "codex", "role_id": "coding_agent", "live": True},
                ]
            },
        }
    )

    assert topology.live_reviewer_providers == ("claude",)
    assert topology.live_implementer_providers == ("codex",)
    assert topology.missing_required_roles == ()
    assert topology.providers_for_role("architecture_review") == ("claude",)
    assert topology.providers_for_role("implementation") == ("codex",)
    assert topology.providers_for_role("review_agent") == ()
    assert topology.providers_for_role("coding_agent") == ()
    assert tuple(row.role_id for row in topology.role_occupancies) == (
        "architecture_review",
        "implementation",
    )
    assert topology.migration_debt == (
        "claude:review_agent",
        "codex:coding_agent",
    )
    assert tuple(row.actor_id for row in topology.role_occupancies) == (None, None)
    assert tuple(row.session_id for row in topology.role_occupancies) == (None, None)


def test_role_topology_normalizes_deprecated_role_from_legacy_role_field() -> None:
    topology = resolve_role_topology(
        {
            "session_liveness_signals": [
                {
                    "provider": "claude",
                    "role": "coding_agent",
                    "state": "alive",
                    "agent_id": "claude-1",
                    "session_id": "session-1",
                }
            ]
        }
    )

    assert topology.providers_for_role("implementation") == ("claude",)
    assert topology.providers_for_role("coding_agent") == ()
    assert tuple(row.role_id for row in topology.role_occupancies) == (
        "implementation",
    )
    assert topology.role_occupancies[0].actor_id == "claude-1"
    assert topology.role_occupancies[0].session_id == "session-1"
    assert topology.role_occupancies[0].migration_debt == (
        "deprecated_role_id:coding_agent",
    )
    assert topology.migration_debt == ("claude:coding_agent",)


def test_role_topology_preserves_tdd_and_dogfood_roles() -> None:
    topology = resolve_role_topology(
        {
            "active_conductor_providers": ["codex", "claude"],
            "collaboration": {
                "role_assignments": [
                    {"provider": "codex", "role_id": "TDDFirstRole", "live": True},
                    {"provider": "claude", "role_id": "dogfooder", "live": True},
                ]
            },
        }
    )

    assert topology.providers_for_role("tdd_first_role") == ("codex",)
    assert topology.providers_for_role("dogfood_test") == ("claude",)
    assert tuple(row.role_id for row in topology.role_occupancies) == (
        "tdd_first_role",
        "dogfood_test",
    )
    assert tuple(row.capability_classes for row in topology.role_occupancies) == (
        ("test",),
        ("test",),
    )
