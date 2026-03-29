"""Reviewer-supervisor restart helpers for ensure flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class EnsureStatusSnapshot:
    """Current ensure status payload paired with its typed bridge view."""

    report: dict[str, object]
    bridge_state: object


@dataclass(frozen=True, slots=True)
class ReviewerSupervisorRestartAttempt:
    """Outcome of an ensure-triggered reviewer-supervisor restart attempt."""

    attempted: bool
    restarted: bool
    report: dict[str, object]
    bridge_state: object
    start_status: str = "not_attempted"


def try_restart_reviewer_supervisor(
    *,
    args,
    repo_root,
    paths,
    deps,
    snapshot: EnsureStatusSnapshot,
    read_ensure_status_fn: Callable[..., tuple[dict[str, object], object]],
) -> ReviewerSupervisorRestartAttempt:
    """Attempt reviewer-supervisor auto-restart with verification."""
    report = snapshot.report
    bridge_state = snapshot.bridge_state
    no_restart = ReviewerSupervisorRestartAttempt(
        attempted=False,
        restarted=False,
        report=report,
        bridge_state=bridge_state,
    )
    if (
        bridge_state.reviewer_supervisor_ok
        or not deps.reviewer_mode_is_active_fn(bridge_state.reviewer_mode)
        or not bridge_state.review_needed
        or deps.spawn_reviewer_supervisor_fn is None
    ):
        return no_restart
    try:
        started, sup_pid, _ = deps.spawn_reviewer_supervisor_fn(
            args=args,
            repo_root=repo_root,
            paths=paths,
        )
        if not started:
            return ReviewerSupervisorRestartAttempt(
                attempted=True,
                restarted=False,
                report=report,
                bridge_state=bridge_state,
                start_status="spawn_failed",
            )

        deps.sleep_fn(0.5)
        start_status = "started"
        if deps.verify_reviewer_supervisor_start_fn is not None:
            start_status = deps.verify_reviewer_supervisor_start_fn(
                pid=sup_pid,
                paths=paths,
                reviewer_mode=bridge_state.reviewer_mode,
            )
            if start_status != "started":
                report, bridge_state = read_ensure_status_fn(
                    args=args,
                    repo_root=repo_root,
                    paths=paths,
                    deps=deps,
                )
                return ReviewerSupervisorRestartAttempt(
                    attempted=True,
                    restarted=False,
                    report=report,
                    bridge_state=bridge_state,
                    start_status=start_status,
                )

        deps.sleep_fn(0.5)
        report, bridge_state = read_ensure_status_fn(
            args=args,
            repo_root=repo_root,
            paths=paths,
            deps=deps,
        )
        restarted = bridge_state.reviewer_supervisor_ok
        if not restarted:
            start_status = "state_not_running"
        return ReviewerSupervisorRestartAttempt(
            attempted=True,
            restarted=restarted,
            report=report,
            bridge_state=bridge_state,
            start_status=start_status,
        )
    except (OSError, ValueError):
        return no_restart
