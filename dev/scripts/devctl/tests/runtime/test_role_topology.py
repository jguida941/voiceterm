"""Focused tests for role-based live topology resolution."""

from __future__ import annotations

from dev.scripts.devctl.runtime.role_topology import resolve_role_topology


def test_role_topology_allows_same_provider_multiple_typed_roles() -> None:
    topology = resolve_role_topology(
        {
            "active_conductor_providers": ["codex"],
            "reviewer_capability": {"provider": "codex"},
            "implementer_capability": {"provider": "codex"},
        }
    )

    assert topology.live_reviewer_providers == ("codex",)
    assert topology.live_implementer_providers == ("codex",)
    assert topology.missing_required_roles == ()


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
