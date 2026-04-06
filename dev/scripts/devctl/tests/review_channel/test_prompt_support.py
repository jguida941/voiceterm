"""Focused tests for review-channel prompt_support helpers."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.prompt_support import (
    resolve_conductor_capability,
)


def test_resolve_conductor_capability_prefers_effective_reviewer_mode() -> None:
    """When bridge_liveness has effective_reviewer_mode, it wins over reviewer_mode."""
    cap = resolve_conductor_capability(
        provider="codex",
        role="reviewer",
        bridge_liveness={
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "tools_only",
        },
    )

    assert cap.queue_policy == "inactive"
    assert cap.status_summary.startswith("Reviewer loop is not in an active")


def test_resolve_conductor_capability_falls_back_to_reviewer_mode() -> None:
    """When effective_reviewer_mode is absent, fall back to reviewer_mode."""
    cap = resolve_conductor_capability(
        provider="claude",
        role="implementer",
        bridge_liveness={
            "reviewer_mode": "active_dual_agent",
        },
    )

    assert cap.may_edit_repo is True
    assert cap.queue_policy == "implement_assigned_work"
