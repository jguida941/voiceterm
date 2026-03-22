"""Reviewer-side bounded wait primitive, symmetric with _wait.py (implementer wait).

The reviewer waits for meaningful implementer-side state changes:
- Worktree hash changed vs last reviewed hash (new code to review)
- Implementer ACK/status updated in typed current-session state

Wake contract is reviewer-owned: passive heartbeat freshness is NOT
equivalent to a meaningful review-needed state change.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from ...review_channel.peer_liveness import AttentionStatus, reviewer_mode_is_active
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths
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


@dataclass(frozen=True, slots=True)
class ReviewerWaitSnapshot:
    """One status snapshot observed by the reviewer wait loop."""

    report: dict[str, object]
    exit_code: int
    worktree_hash: str
    reviewed_hash: str
    implementer_ack_revision: str
    implementer_ack_state: str
    implementer_status_excerpt: str
    attention_status: str
    reviewer_mode: str


@dataclass(frozen=True, slots=True)
class ReviewerWaitState:
    """Rendered reviewer wait-state payload."""

    mode: str
    stop_reason: str
    polls_observed: int
    wait_interval_seconds: int
    wait_timeout_seconds: int
    baseline_worktree_hash: str
    current_worktree_hash: str
    baseline_reviewed_hash: str
    baseline_implementer_ack_revision: str
    current_implementer_ack_revision: str
    implementer_update_observed: bool

    def to_report(self) -> dict[str, object]:
        return asdict(self)


def run_reviewer_wait_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    deps: WaitDeps,
) -> tuple[dict[str, object], int]:
    """Wait on bounded cadence until implementer-owned state changes."""
    runtime_paths = _coerce_runtime_paths(paths)
    assert runtime_paths.bridge_path is not None

    baseline = _capture_reviewer_snapshot(
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
        current = _capture_reviewer_snapshot(
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


def _capture_reviewer_snapshot(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
    deps: WaitDeps,
) -> ReviewerWaitSnapshot:
    report, exit_code = deps.run_status_action_fn(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    reviewer_worker = _mapping(report.get("reviewer_worker"))
    bridge_liveness = _mapping(report.get("bridge_liveness"))
    current_session = _load_current_session(report)
    attention = _mapping(report.get("attention"))

    return ReviewerWaitSnapshot(
        report=dict(report),
        exit_code=exit_code,
        worktree_hash=str(reviewer_worker.get("current_hash") or ""),
        reviewed_hash=str(reviewer_worker.get("reviewed_hash") or ""),
        implementer_ack_revision=str(
            current_session.get("implementer_ack_revision")
            or bridge_liveness.get("claude_ack_revision")
            or ""
        ),
        implementer_ack_state=str(
            current_session.get("implementer_ack_state")
            or _bridge_ack_state(bridge_liveness)
        ),
        implementer_status_excerpt=str(
            current_session.get("implementer_status") or ""
        )[:200],
        attention_status=str(attention.get("status") or ""),
        reviewer_mode=str(
            bridge_liveness.get("reviewer_mode")
            or reviewer_worker.get("reviewer_mode")
            or ""
        ),
    )


def _load_current_session(report: Mapping[str, object]) -> Mapping[str, object]:
    """Load typed current-session state from the generated status projections."""
    inline_session = _mapping(report.get("current_session"))
    if inline_session:
        return inline_session
    projection_paths = _mapping(report.get("projection_paths"))
    for key in ("review_state_path", "compact_path"):
        raw_path = projection_paths.get(key)
        if not raw_path:
            continue
        try:
            payload = json.loads(Path(str(raw_path)).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        current_session = payload.get("current_session")
        if isinstance(current_session, Mapping):
            return current_session
    return {}


def _bridge_ack_state(bridge_liveness: Mapping[str, object]) -> str:
    """Derive a coarse ACK state from bridge-liveness when projections are unavailable."""
    if bool(bridge_liveness.get("claude_ack_current")):
        return "current"
    if bridge_liveness.get("claude_ack_present"):
        return "stale"
    return "missing"


def _mapping(value: object) -> Mapping[str, object]:
    """Return a mapping view or an empty mapping."""
    return value if isinstance(value, Mapping) else {}


def _reviewer_loop_unhealthy(snapshot: ReviewerWaitSnapshot) -> bool:
    if snapshot.exit_code != 0:
        return True
    if snapshot.attention_status in _REVIEWER_WAIT_UNHEALTHY_STATUSES:
        return True
    return not reviewer_mode_is_active(snapshot.reviewer_mode)


def _implementer_update_ready(snapshot: ReviewerWaitSnapshot) -> bool:
    """Check if implementer has made changes since last review."""
    if not snapshot.worktree_hash or not snapshot.reviewed_hash:
        return False
    return snapshot.worktree_hash != snapshot.reviewed_hash


def _implementer_changed(
    baseline: ReviewerWaitSnapshot,
    current: ReviewerWaitSnapshot,
) -> bool:
    """Detect meaningful implementer-side state change."""
    if current.worktree_hash != baseline.worktree_hash:
        return True
    if (
        current.implementer_ack_revision
        and current.implementer_ack_revision != baseline.implementer_ack_revision
    ):
        return True
    if current.implementer_ack_state != baseline.implementer_ack_state:
        return True
    return current.implementer_status_excerpt != baseline.implementer_status_excerpt


def _finalize_reviewer_report(
    *,
    baseline: ReviewerWaitSnapshot,
    current: ReviewerWaitSnapshot,
    args,
    outcome: WaitOutcome,
) -> tuple[dict[str, object], int]:
    report = dict(current.report)
    report["action"] = getattr(args, "action", "reviewer-wait")
    report["ok"] = outcome.exit_code == 0
    report["exit_ok"] = outcome.exit_code == 0
    report["exit_code"] = outcome.exit_code
    report["wait_state"] = ReviewerWaitState(
        mode="reviewer_wait",
        stop_reason=outcome.stop_reason,
        polls_observed=outcome.polls_observed,
        wait_interval_seconds=outcome.wait_interval_seconds,
        wait_timeout_seconds=outcome.wait_timeout_seconds,
        baseline_worktree_hash=baseline.worktree_hash,
        current_worktree_hash=current.worktree_hash,
        baseline_reviewed_hash=baseline.reviewed_hash,
        baseline_implementer_ack_revision=baseline.implementer_ack_revision,
        current_implementer_ack_revision=current.implementer_ack_revision,
        implementer_update_observed=outcome.stop_reason in {
            "implementer_update_observed",
            "implementer_update_ready",
        },
    ).to_report()
    _append_reviewer_wait_message(report, stop_reason=outcome.stop_reason)
    return report, outcome.exit_code


def _append_reviewer_wait_message(
    report: dict[str, object],
    *,
    stop_reason: str,
) -> None:
    warnings = report.setdefault("warnings", [])
    errors = report.setdefault("errors", [])
    if not isinstance(warnings, list) or not isinstance(errors, list):
        return
    if stop_reason == "implementer_update_observed":
        warnings.append(
            "Implementer-owned state changed (worktree hash or typed ACK/status state). "
            "Re-read the worktree diff and review the new work."
        )
    elif stop_reason == "implementer_update_ready":
        warnings.append(
            "Implementer has already changed the worktree since last review. "
            "Review the current diff instead of waiting."
        )
    elif stop_reason == "reviewer_loop_unhealthy":
        errors.append(
            "Reviewer wait stopped because the review loop is unhealthy. "
            "Check reviewer mode and runtime state."
        )
    elif stop_reason == "timed_out":
        errors.append(
            "Timed out waiting for implementer-owned state change."
        )
