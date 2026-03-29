"""Implementer-side bounded bridge wait helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ...review_channel.peer_liveness import AttentionStatus, reviewer_mode_is_active
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths
from ._wait_reporting import finalize_implementer_wait_report
from ._wait_runtime_state import read_wait_runtime_state
from ._wait_support import build_typed_reviewer_token
from ._wait_shared import resolve_wait_timeout

DEFAULT_IMPLEMENTER_WAIT_TIMEOUT_SECONDS = 3600
_REVIEWER_WAIT_FAILURE_STATUSES = frozenset(
    {
        AttentionStatus.INACTIVE,
        AttentionStatus.REVIEWER_HEARTBEAT_MISSING,
        AttentionStatus.REVIEWER_HEARTBEAT_STALE,
        AttentionStatus.REVIEWER_OVERDUE,
        AttentionStatus.REVIEWER_SUPERVISOR_REQUIRED,
        AttentionStatus.PUBLISHER_MISSING,
        AttentionStatus.PUBLISHER_FAILED_START,
        AttentionStatus.PUBLISHER_DETACHED_EXIT,
        AttentionStatus.CHECKPOINT_REQUIRED,
        AttentionStatus.BRIDGE_CONTRACT_ERROR,
    }
)


@dataclass(frozen=True, slots=True)
class ImplementerWaitSnapshot:
    """One bridge/status snapshot observed by the bounded wait loop."""

    report: dict[str, object]
    exit_code: int
    reviewer_token: str
    review_needed: bool
    claude_ack_current: bool
    current_instruction_revision: str
    attention_status: str
    attention_summary: str
    attention_recommended_action: str
    latest_pending_packet_id: str


@dataclass(frozen=True, slots=True)
class ImplementerWaitDeps:
    """Injectable side effects for implementer wait tests."""

    run_status_action_fn: Callable[..., tuple[dict[str, object], int]]
    read_bridge_text_fn: Callable[[Path], str]
    monotonic_fn: Callable[[], float]
    sleep_fn: Callable[[float], None]
    bridge_poll_fn: Callable[[str], BridgePollResult] | None = None
    pending_packets_fn: Callable[[Path, RuntimePaths], list[dict[str, object]]] | None = None


@dataclass(frozen=True, slots=True)
class ImplementerWaitOutcome:
    """Final wait-loop outcome."""

    stop_reason: str
    polls_observed: int
    wait_timeout_seconds: int
    wait_interval_seconds: int
    exit_code: int


@dataclass(frozen=True, slots=True)
class WaitLoopConfig:
    """Time budget and poll cadence for one bounded wait run."""

    timeout_seconds: int
    interval_seconds: int


def run_implementer_wait_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    deps: ImplementerWaitDeps,
) -> tuple[dict[str, object], int]:
    """Wait on bounded cadence until reviewer-owned bridge state changes."""
    runtime_paths = _coerce_runtime_paths(paths)
    assert runtime_paths.bridge_path is not None

    wait_config = _build_wait_config(args)
    baseline = _capture_wait_snapshot(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=deps,
    )
    immediate_outcome = _baseline_wait_outcome(baseline, wait_config)
    if immediate_outcome is not None:
        return _finish_wait(
            baseline=baseline,
            current=baseline,
            args=args,
            outcome=immediate_outcome,
        )

    return _poll_for_wait_change(
        baseline=baseline,
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=deps,
        wait_config=wait_config,
    )


def _capture_wait_snapshot(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
    deps: ImplementerWaitDeps,
) -> ImplementerWaitSnapshot:
    report, exit_code = deps.run_status_action_fn(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    runtime_state = read_wait_runtime_state(
        report=report,
        exit_code=exit_code,
        repo_root=repo_root,
        paths=paths,
        deps=deps,
    )

    return ImplementerWaitSnapshot(
        report=dict(report),
        exit_code=runtime_state.exit_code,
        reviewer_token=build_typed_reviewer_token(
            runtime_state.poll_result,
            latest_pending_packet_id=runtime_state.pending_packet_id,
        ),
        review_needed=bool(report.get("review_needed")),
        claude_ack_current=runtime_state.poll_result.claude_ack_current,
        current_instruction_revision=runtime_state.poll_result.current_instruction_revision,
        attention_status=runtime_state.attention.status,
        attention_summary=runtime_state.attention.summary,
        attention_recommended_action=runtime_state.attention.recommended_action,
        latest_pending_packet_id=runtime_state.pending_packet_id,
    )


def _reviewer_unhealthy(snapshot: ImplementerWaitSnapshot) -> bool:
    if snapshot.exit_code != 0:
        return True
    if snapshot.attention_status in _REVIEWER_WAIT_FAILURE_STATUSES:
        return True
    bridge_liveness = snapshot.report.get("bridge_liveness")
    if not isinstance(bridge_liveness, dict):
        return True
    return not reviewer_mode_is_active(str(bridge_liveness.get("reviewer_mode") or ""))


def _reviewer_update_ready(snapshot: ImplementerWaitSnapshot) -> bool:
    return (not snapshot.review_needed) and (not snapshot.claude_ack_current)


def _wait_timeout_seconds(args) -> int:
    timeout_seconds = resolve_wait_timeout(
        args,
        default_seconds=DEFAULT_IMPLEMENTER_WAIT_TIMEOUT_SECONDS,
    )
    return timeout_seconds


def _build_wait_config(args) -> WaitLoopConfig:
    timeout_seconds = _wait_timeout_seconds(args)
    interval_seconds = max(1, int(getattr(args, "follow_interval_seconds", 150)))

    return WaitLoopConfig(
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
    )


def _baseline_wait_outcome(
    snapshot: ImplementerWaitSnapshot,
    wait_config: WaitLoopConfig,
) -> ImplementerWaitOutcome | None:
    if _reviewer_unhealthy(snapshot):
        return _wait_outcome(
            stop_reason="reviewer_unhealthy",
            polls_observed=0,
            exit_code=1,
            wait_config=wait_config,
        )

    if _reviewer_update_ready(snapshot):
        return _wait_outcome(
            stop_reason="reviewer_update_ready",
            polls_observed=0,
            exit_code=0,
            wait_config=wait_config,
        )

    if not snapshot.review_needed:
        return _wait_outcome(
            stop_reason="not_waiting",
            polls_observed=0,
            exit_code=1,
            wait_config=wait_config,
        )

    return None


def _poll_for_wait_change(
    *,
    baseline: ImplementerWaitSnapshot,
    args,
    repo_root: Path,
    paths: RuntimePaths,
    deps: ImplementerWaitDeps,
    wait_config: WaitLoopConfig,
) -> tuple[dict[str, object], int]:
    deadline = deps.monotonic_fn() + wait_config.timeout_seconds
    polls_observed = 0
    current = baseline

    while deps.monotonic_fn() < deadline:
        deps.sleep_fn(wait_config.interval_seconds)
        polls_observed += 1
        current = _capture_wait_snapshot(
            args=args,
            repo_root=repo_root,
            paths=paths,
            deps=deps,
        )

        poll_outcome = _poll_wait_outcome(
            baseline=baseline,
            current=current,
            polls_observed=polls_observed,
            wait_config=wait_config,
        )
        if poll_outcome is not None:
            return _finish_wait(
                baseline=baseline,
                current=current,
                args=args,
                outcome=poll_outcome,
            )

    return _finish_wait(
        baseline=baseline,
        current=current,
        args=args,
        outcome=_wait_outcome(
            stop_reason="timed_out",
            polls_observed=polls_observed,
            exit_code=1,
            wait_config=wait_config,
        ),
    )


def _poll_wait_outcome(
    *,
    baseline: ImplementerWaitSnapshot,
    current: ImplementerWaitSnapshot,
    polls_observed: int,
    wait_config: WaitLoopConfig,
) -> ImplementerWaitOutcome | None:
    if _reviewer_unhealthy(current):
        return _wait_outcome(
            stop_reason="reviewer_unhealthy",
            polls_observed=polls_observed,
            exit_code=1,
            wait_config=wait_config,
        )

    if (
        _reviewer_update_ready(current)
        or current.reviewer_token != baseline.reviewer_token
    ):
        return _wait_outcome(
            stop_reason="reviewer_update_observed",
            polls_observed=polls_observed,
            exit_code=0,
            wait_config=wait_config,
        )

    return None


def _wait_outcome(
    *,
    stop_reason: str,
    polls_observed: int,
    exit_code: int,
    wait_config: WaitLoopConfig,
) -> ImplementerWaitOutcome:
    timeout_seconds = wait_config.timeout_seconds
    interval_seconds = wait_config.interval_seconds

    return ImplementerWaitOutcome(
        stop_reason=stop_reason,
        polls_observed=polls_observed,
        wait_timeout_seconds=timeout_seconds,
        wait_interval_seconds=interval_seconds,
        exit_code=exit_code,
    )


def _finish_wait(
    *,
    baseline: ImplementerWaitSnapshot,
    current: ImplementerWaitSnapshot,
    args,
    outcome: ImplementerWaitOutcome,
) -> tuple[dict[str, object], int]:
    report, exit_code = finalize_implementer_wait_report(
        baseline=baseline,
        current=current,
        args=args,
        outcome=outcome,
    )
    return report, exit_code
