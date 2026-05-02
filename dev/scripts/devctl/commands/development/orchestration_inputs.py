"""Existing orchestration inputs for the typed `/develop` controller."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .models import DevelopmentOrchestrationSnapshot
from .orchestration_agent_loop import agent_loop_inputs, agent_loop_signals
from .orchestration_system_picture import system_picture_signals


def orchestration_snapshot(
    repo_root: Path,
    review_state: Mapping[str, object],
    *,
    actor: str,
    dashboard: Mapping[str, object] | None = None,
) -> DevelopmentOrchestrationSnapshot:
    """Summarize existing proof/wake/freshness surfaces for `/develop`."""
    picture_signals = system_picture_signals(repo_root)
    loop_decisions = agent_loop_inputs(
        review_state,
        actor=actor,
        dashboard=dashboard,
    )
    loop_signals = agent_loop_signals(loop_decisions)
    signals = (*picture_signals, *loop_signals)
    stale_count = sum(1 for signal in signals if signal.status == "stale")
    missing_count = sum(1 for signal in signals if signal.status == "missing")
    action_count = sum(
        1
        for signal in signals
        if signal.status in {"action_required", "blocked", "stale", "missing"}
    )
    return DevelopmentOrchestrationSnapshot(
        status=_status(
            missing_projection_count=missing_count,
            stale_projection_count=stale_count,
            action_required_count=action_count,
        ),
        signal_count=len(signals),
        stale_projection_count=stale_count,
        missing_projection_count=missing_count,
        action_required_count=action_count,
        agent_loop_decisions=loop_decisions,
        signals=signals,
        summary=_summary(
            signal_count=len(signals),
            missing_projection_count=missing_count,
            stale_projection_count=stale_count,
            action_required_count=action_count,
        ),
    )


def _status(
    *,
    missing_projection_count: int,
    stale_projection_count: int,
    action_required_count: int,
) -> str:
    if missing_projection_count:
        return "missing_inputs"
    if stale_projection_count:
        return "stale_inputs"
    if action_required_count:
        return "action_required"
    return "current"


def _summary(
    *,
    signal_count: int,
    missing_projection_count: int,
    stale_projection_count: int,
    action_required_count: int,
) -> str:
    if not signal_count:
        return "No orchestration signals require attention."
    return (
        f"{signal_count} orchestration signal(s): "
        f"{missing_projection_count} missing, "
        f"{stale_projection_count} stale, "
        f"{action_required_count} action-required."
    )


__all__ = ["orchestration_snapshot"]
