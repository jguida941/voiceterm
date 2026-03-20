"""Implementer-side bounded bridge wait helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from ...review_channel.peer_liveness import AttentionStatus, reviewer_mode_is_active
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths
from ._bridge_poll import BridgePollResult, build_bridge_poll_result
from ._wait_support import (
    build_typed_reviewer_token,
    latest_pending_packet_id,
    load_pending_claude_packets,
    validate_wait_bridge_content,
)

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
class ImplementerWaitState:
    """Rendered wait-state payload."""

    mode: str
    stop_reason: str
    polls_observed: int
    wait_interval_seconds: int
    wait_timeout_seconds: int
    baseline_instruction_revision: str
    current_instruction_revision: str
    baseline_attention_status: str
    current_attention_status: str
    reviewer_update_observed: bool

    def to_report(self) -> dict[str, object]:
        """Return the stable report payload."""
        return asdict(self)


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

    baseline = _capture_wait_snapshot(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=deps,
    )
    timeout_seconds = _wait_timeout_seconds(args)
    interval_seconds = max(1, int(getattr(args, "follow_interval_seconds", 150)))

    if _reviewer_unhealthy(baseline):
        return _finalize_wait_report(
            baseline=baseline,
            current=baseline,
            args=args,
            outcome=ImplementerWaitOutcome(
                stop_reason="reviewer_unhealthy",
                polls_observed=0,
                wait_timeout_seconds=timeout_seconds,
                wait_interval_seconds=interval_seconds,
                exit_code=1,
            ),
        )

    if _reviewer_update_ready(baseline):
        return _finalize_wait_report(
            baseline=baseline,
            current=baseline,
            args=args,
            outcome=ImplementerWaitOutcome(
                stop_reason="reviewer_update_ready",
                polls_observed=0,
                wait_timeout_seconds=timeout_seconds,
                wait_interval_seconds=interval_seconds,
                exit_code=0,
            ),
        )

    if not baseline.review_needed:
        return _finalize_wait_report(
            baseline=baseline,
            current=baseline,
            args=args,
            outcome=ImplementerWaitOutcome(
                stop_reason="not_waiting",
                polls_observed=0,
                wait_timeout_seconds=timeout_seconds,
                wait_interval_seconds=interval_seconds,
                exit_code=1,
            ),
        )

    deadline = deps.monotonic_fn() + timeout_seconds
    polls_observed = 0
    current = baseline
    while deps.monotonic_fn() < deadline:
        deps.sleep_fn(interval_seconds)
        polls_observed += 1
        current = _capture_wait_snapshot(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
            deps=deps,
        )
        if _reviewer_unhealthy(current):
            return _finalize_wait_report(
                baseline=baseline,
                current=current,
                args=args,
                outcome=ImplementerWaitOutcome(
                    stop_reason="reviewer_unhealthy",
                    polls_observed=polls_observed,
                    wait_timeout_seconds=timeout_seconds,
                    wait_interval_seconds=interval_seconds,
                    exit_code=1,
                ),
            )
        if _reviewer_update_ready(current) or current.reviewer_token != baseline.reviewer_token:
            return _finalize_wait_report(
                baseline=baseline,
                current=current,
                args=args,
                outcome=ImplementerWaitOutcome(
                    stop_reason="reviewer_update_observed",
                    polls_observed=polls_observed,
                    wait_timeout_seconds=timeout_seconds,
                    wait_interval_seconds=interval_seconds,
                    exit_code=0,
                ),
            )

    return _finalize_wait_report(
        baseline=baseline,
        current=current,
        args=args,
        outcome=ImplementerWaitOutcome(
            stop_reason="timed_out",
            polls_observed=polls_observed,
            wait_timeout_seconds=timeout_seconds,
            wait_interval_seconds=interval_seconds,
            exit_code=1,
        ),
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
    bridge_text = deps.read_bridge_text_fn(paths.bridge_path)

    # Route fully through typed bridge-poll for revision, ACK, and update
    # detection. Raw markdown parsing is no longer used in the normal path.
    poll_fn = deps.bridge_poll_fn or build_bridge_poll_result
    poll_result = poll_fn(bridge_text)
    pending_packets_fn = deps.pending_packets_fn or load_pending_claude_packets
    pending_packets = pending_packets_fn(repo_root, paths)
    pending_packet_id = latest_pending_packet_id(pending_packets)

    # Fail closed: if bridge content is malformed (not just ACK-stale),
    # force exit_code=1 so _reviewer_unhealthy treats this as broken.
    bridge_validation_errors = validate_wait_bridge_content(bridge_text)
    if bridge_validation_errors:
        exit_code = 1

    attention = report.get("attention")
    return ImplementerWaitSnapshot(
        report=dict(report),
        exit_code=exit_code,
        reviewer_token=build_typed_reviewer_token(
            poll_result,
            latest_pending_packet_id=pending_packet_id,
        ),
        review_needed=bool(report.get("review_needed")),
        claude_ack_current=poll_result.claude_ack_current,
        current_instruction_revision=poll_result.current_instruction_revision,
        attention_status=str(
            attention.get("status")
            if isinstance(attention, dict)
            else ""
        ),
        latest_pending_packet_id=pending_packet_id,
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
    timeout_minutes = int(getattr(args, "timeout_minutes", 0) or 0)
    if timeout_minutes > 0:
        return timeout_minutes * 60
    return DEFAULT_IMPLEMENTER_WAIT_TIMEOUT_SECONDS


def _finalize_wait_report(
    *,
    baseline: ImplementerWaitSnapshot,
    current: ImplementerWaitSnapshot,
    args,
    outcome: ImplementerWaitOutcome,
) -> tuple[dict[str, object], int]:
    report = dict(current.report)
    report["action"] = getattr(args, "action", "implementer-wait")
    report["ok"] = outcome.exit_code == 0
    report["exit_ok"] = outcome.exit_code == 0
    report["exit_code"] = outcome.exit_code
    report["wait_state"] = ImplementerWaitState(
        mode="implementer_wait",
        stop_reason=outcome.stop_reason,
        polls_observed=outcome.polls_observed,
        wait_interval_seconds=outcome.wait_interval_seconds,
        wait_timeout_seconds=outcome.wait_timeout_seconds,
        baseline_instruction_revision=baseline.current_instruction_revision,
        current_instruction_revision=current.current_instruction_revision,
        baseline_attention_status=baseline.attention_status,
        current_attention_status=current.attention_status,
        reviewer_update_observed=outcome.stop_reason in {
            "reviewer_update_observed",
            "reviewer_update_ready",
        },
    ).to_report()
    _append_wait_message(report, stop_reason=outcome.stop_reason)
    return report, outcome.exit_code


def _append_wait_message(report: dict[str, object], *, stop_reason: str) -> None:
    warnings = report.setdefault("warnings", [])
    errors = report.setdefault("errors", [])
    if not isinstance(warnings, list) or not isinstance(errors, list):
        return
    if stop_reason == "reviewer_update_observed":
        warnings.append(
            "Reviewer-owned bridge content or a fresh Claude-targeted review packet changed. Re-read `code_audit.md`, poll the review-channel inbox, and resume from the new reviewer state."
        )
    elif stop_reason == "reviewer_update_ready":
        warnings.append(
            "Reviewer state is already ahead of the current Claude ACK. Re-read `code_audit.md` and poll the review-channel inbox instead of waiting."
        )
    elif stop_reason == "not_waiting":
        errors.append(
            "Implementer wait requires pending review work. The current tree already matches the reviewed hash and Claude ACK is current."
        )
    elif stop_reason == "reviewer_unhealthy":
        errors.append(
            "Implementer wait stopped because the reviewer loop is unhealthy. Restore the reviewer heartbeat/supervisor instead of waiting silently."
        )
    elif stop_reason == "timed_out":
        errors.append(
            "Timed out waiting for a meaningful reviewer-owned bridge or packet update."
        )
