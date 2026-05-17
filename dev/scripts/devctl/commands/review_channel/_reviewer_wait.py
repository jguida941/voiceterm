"""Reviewer-side bounded wait primitive, symmetric with _wait.py (implementer wait).

The reviewer waits for meaningful implementer-side state changes:
- Worktree hash changed vs last reviewed hash (new code to review)
- Implementer ACK/status updated in typed current-session state
- Implementer-state-hash diverged from reviewer-accepted baseline (Slice 2/3)

Wake contract is reviewer-owned: passive heartbeat freshness is NOT
equivalent to a meaningful review-needed state change.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ...review_channel.peer_liveness import AttentionStatus, reviewer_mode_is_active
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths
from ._reviewer_wait_report import build_reviewer_wait_report
from ._reviewer_wait_snapshot import (
    ReviewerWaitSnapshot,
    capture_reviewer_snapshot,
)
from ._wait_shared import WaitDeps, WaitOutcome, resolve_wait_interval, resolve_wait_timeout

DEFAULT_REVIEWER_WAIT_TIMEOUT_SECONDS = 1800

_REVIEWER_WAIT_UNHEALTHY_STATUSES = frozenset(
    {
        AttentionStatus.INACTIVE,
        AttentionStatus.RUNTIME_MISSING,
        AttentionStatus.PUBLISHER_MISSING,
        AttentionStatus.PUBLISHER_FAILED_START,
        AttentionStatus.PUBLISHER_DETACHED_EXIT,
        AttentionStatus.CHECKPOINT_REQUIRED,
    }
)


def run_reviewer_wait_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    deps: WaitDeps,
) -> tuple[dict[str, object], int]:
    """Wait on bounded cadence until implementer-owned or packet-queue state changes."""
    runtime_paths = _coerce_runtime_paths(paths)
    assert runtime_paths.bridge_path is not None

    baseline = capture_reviewer_snapshot(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=deps,
    )
    timeout_seconds = resolve_wait_timeout(
        args, default_seconds=DEFAULT_REVIEWER_WAIT_TIMEOUT_SECONDS
    )
    interval_seconds = resolve_wait_interval(args, default_seconds=120)

    if _reviewer_loop_unhealthy(baseline):
        return _finalize_reviewer_report(
            baseline=baseline,
            current=baseline,
            args=args,
            outcome=WaitOutcome(
                stop_reason="reviewer_loop_unhealthy",
                polls_observed=0,
                wait_timeout_seconds=timeout_seconds,
                wait_interval_seconds=interval_seconds,
                exit_code=1,
            ),
        )

    # If implementer already changed since last review, exit immediately
    if _implementer_update_ready(baseline):
        return _finalize_reviewer_report(
            baseline=baseline,
            current=baseline,
            args=args,
            outcome=WaitOutcome(
                stop_reason="implementer_update_ready",
                polls_observed=0,
                wait_timeout_seconds=timeout_seconds,
                wait_interval_seconds=interval_seconds,
                exit_code=0,
            ),
        )

    deadline = deps.monotonic_fn() + timeout_seconds
    polls_observed = 0
    current = baseline
    while deps.monotonic_fn() < deadline:
        deps.sleep_fn(interval_seconds)
        polls_observed += 1
        current = capture_reviewer_snapshot(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
            deps=deps,
        )
        if _reviewer_loop_unhealthy(current):
            return _finalize_reviewer_report(
                baseline=baseline,
                current=current,
                args=args,
                outcome=WaitOutcome(
                    stop_reason="reviewer_loop_unhealthy",
                    polls_observed=polls_observed,
                    wait_timeout_seconds=timeout_seconds,
                    wait_interval_seconds=interval_seconds,
                    exit_code=1,
                ),
            )
        if _implementer_changed(baseline, current):
            return _finalize_reviewer_report(
                baseline=baseline,
                current=current,
                args=args,
                outcome=WaitOutcome(
                    stop_reason="implementer_update_observed",
                    polls_observed=polls_observed,
                    wait_timeout_seconds=timeout_seconds,
                    wait_interval_seconds=interval_seconds,
                    exit_code=0,
                ),
            )

    return _finalize_reviewer_report(
        baseline=baseline,
        current=current,
        args=args,
        outcome=WaitOutcome(
            stop_reason="timed_out",
            polls_observed=polls_observed,
            wait_timeout_seconds=timeout_seconds,
            wait_interval_seconds=interval_seconds,
            exit_code=1,
        ),
    )


def _reviewer_loop_unhealthy(snapshot: ReviewerWaitSnapshot) -> bool:
    if snapshot.exit_code != 0:
        return True
    if not snapshot.packet_inbox_available:
        return True
    if snapshot.attention_status in _REVIEWER_WAIT_UNHEALTHY_STATUSES:
        return True
    return not reviewer_mode_is_active(snapshot.reviewer_mode)


def _implementer_update_ready(snapshot: ReviewerWaitSnapshot) -> bool:
    """Check if implementer has made changes since last review.

    Uses three signals: pending typed packets for Codex, worktree hash
    divergence (raw tree change), and implementer-state-hash divergence from
    the reviewer-accepted baseline (semantic content change from Slice 2 typed
    state).
    """
    if snapshot.latest_pending_packet_id:
        return True
    if snapshot.latest_finding_packet_id:
        return True
    if snapshot.worktree_hash and snapshot.reviewed_hash:
        if snapshot.worktree_hash != snapshot.reviewed_hash:
            return True
    if _accepted_hash_diverged(snapshot):
        return True
    return False


def _implementer_changed(
    baseline: ReviewerWaitSnapshot,
    current: ReviewerWaitSnapshot,
) -> bool:
    """Detect meaningful implementer-side state change.

    Checks pending typed packets, raw worktree hash, ACK revision/state,
    status excerpt, and the semantic implementer-state-hash vs the reviewer-
    accepted baseline (Slice 2 typed authority).
    """
    if current.latest_pending_packet_id != baseline.latest_pending_packet_id:
        return True
    if current.latest_finding_packet_id != baseline.latest_finding_packet_id:
        return True
    if current.worktree_hash != baseline.worktree_hash:
        return True
    if (
        current.implementer_ack_revision
        and current.implementer_ack_revision != baseline.implementer_ack_revision
    ):
        return True
    if current.implementer_ack_state != baseline.implementer_ack_state:
        return True
    if current.implementer_status_excerpt != baseline.implementer_status_excerpt:
        return True
    # Semantic hash divergence: if the current snapshot's implementer state
    # hash differs from the reviewer-accepted baseline, the implementer has
    # produced new work even if the worktree tree hash stayed the same.
    if _accepted_hash_diverged(current):
        return True
    return False


def _accepted_hash_diverged(snapshot: ReviewerWaitSnapshot) -> bool:
    """True when implementer-state-hash differs from the reviewer-accepted baseline.

    Gracefully returns False when either hash is absent (Slice 2 not yet
    landed or no reviewer checkpoint has been cut).
    """
    if not snapshot.implementer_state_hash:
        return False
    if not snapshot.reviewer_accepted_implementer_state_hash:
        return False
    return (
        snapshot.implementer_state_hash
        != snapshot.reviewer_accepted_implementer_state_hash
    )


def _finalize_reviewer_report(
    *,
    baseline: ReviewerWaitSnapshot,
    current: ReviewerWaitSnapshot,
    args,
    outcome: WaitOutcome,
) -> tuple[dict[str, object], int]:
    report = build_reviewer_wait_report(
        baseline=baseline,
        current=current,
        args=args,
        outcome=outcome,
    )
    return report, outcome.exit_code
