"""Repo-owned stop helpers for detached review-channel daemons."""

from __future__ import annotations

import os
import signal
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass

from ...review_channel.lifecycle_state import (
    read_publisher_state,
    read_reviewer_supervisor_state,
)
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths


@dataclass(frozen=True, slots=True)
class StopTarget:
    """Typed daemon stop target."""

    daemon_kind: str
    read_state_fn: Callable[[object], dict[str, object]]


@dataclass(frozen=True, slots=True)
class StopActionDeps:
    """Side-effect boundary for daemon stop orchestration."""

    kill_fn: Callable[[int, int], None]
    monotonic_fn: Callable[[], float]
    sleep_fn: Callable[[float], None]


@dataclass(frozen=True, slots=True)
class DaemonStopResult:
    """One daemon stop attempt rendered as a stable report row."""

    daemon_kind: str
    attempted: bool
    stopped: bool
    ok: bool
    reason: str
    pid: int = 0
    signal: str = ""
    state: dict[str, object] | None = None
    detail: str = ""

    def to_report(self) -> dict[str, object]:
        report = asdict(self)
        if not self.signal:
            report.pop("signal")
        if self.state is None:
            report.pop("state")
        if not self.detail:
            report.pop("detail")
        if self.pid <= 0:
            report.pop("pid")
        return report


STOP_ACTION_DEPS = StopActionDeps(
    kill_fn=os.kill,
    monotonic_fn=time.monotonic,
    sleep_fn=time.sleep,
)

STOP_TARGETS = {
    "publisher": StopTarget(
        daemon_kind="publisher",
        read_state_fn=read_publisher_state,
    ),
    "reviewer_supervisor": StopTarget(
        daemon_kind="reviewer_supervisor",
        read_state_fn=read_reviewer_supervisor_state,
    ),
}


def run_stop_action(
    *,
    args,
    repo_root,
    paths: RuntimePaths | Mapping[str, object],
    deps: StopActionDeps = STOP_ACTION_DEPS,
) -> tuple[dict[str, object], int]:
    """Stop one or more detached review-channel daemons via repo-owned tooling."""
    del repo_root
    runtime_paths = _coerce_runtime_paths(paths)
    daemon_kind = str(getattr(args, "daemon_kind", "all") or "all")
    grace_seconds = max(0.0, float(getattr(args, "stop_grace_seconds", 5.0)))
    targets = _resolve_stop_targets(daemon_kind)

    result_rows = [
        _stop_target(
            target=target,
            runtime_paths=runtime_paths,
            grace_seconds=grace_seconds,
            deps=deps,
        )
        for target in targets
    ]
    results = [row.to_report() for row in result_rows]
    errors = [
        row.detail
        for row in result_rows
        if not row.ok and row.detail.strip()
    ]
    report: dict[str, object] = {}
    report["command"] = "review-channel"
    report["action"] = "stop"
    report["ok"] = not errors
    report["daemon_kind"] = daemon_kind
    report["grace_seconds"] = grace_seconds
    report["results"] = results
    report["stopped_daemons"] = [
        row.daemon_kind for row in result_rows if row.stopped
    ]
    report["errors"] = errors
    return report, 0 if not errors else 1


def _resolve_stop_targets(daemon_kind: str) -> list[StopTarget]:
    if daemon_kind == "all":
        return [
            STOP_TARGETS["reviewer_supervisor"],
            STOP_TARGETS["publisher"],
        ]
    target = STOP_TARGETS.get(daemon_kind)
    if target is None:
        raise ValueError(f"Unsupported daemon stop target: {daemon_kind}")
    return [target]


def _stop_target(
    *,
    target: StopTarget,
    runtime_paths: RuntimePaths,
    grace_seconds: float,
    deps: StopActionDeps,
) -> DaemonStopResult:
    if runtime_paths.status_dir is None:
        return DaemonStopResult(
            daemon_kind=target.daemon_kind,
            attempted=False,
            stopped=False,
            ok=False,
            reason="status_dir_not_resolved",
            detail="status_dir not resolved",
        )

    initial_state = target.read_state_fn(runtime_paths.status_dir)
    pid = int(initial_state.get("pid", 0) or 0)
    if not bool(initial_state.get("running")) or pid <= 0:
        return DaemonStopResult(
            daemon_kind=target.daemon_kind,
            attempted=False,
            stopped=False,
            ok=True,
            reason="not_running",
            pid=pid,
            state=initial_state,
            detail=f"{target.daemon_kind} is not running",
        )

    try:
        deps.kill_fn(pid, signal.SIGINT)
    except PermissionError:
        return DaemonStopResult(
            daemon_kind=target.daemon_kind,
            attempted=True,
            stopped=False,
            ok=False,
            reason="permission_denied",
            pid=pid,
            state=initial_state,
            detail=f"Permission denied while stopping {target.daemon_kind} pid {pid}",
        )
    except ProcessLookupError:
        refreshed_state = target.read_state_fn(runtime_paths.status_dir)
        stopped = not bool(refreshed_state.get("running"))
        return DaemonStopResult(
            daemon_kind=target.daemon_kind,
            attempted=True,
            stopped=stopped,
            ok=stopped,
            reason="already_exited",
            pid=pid,
            state=refreshed_state,
            detail=f"{target.daemon_kind} pid {pid} was already gone",
        )
    except OSError as exc:
        return DaemonStopResult(
            daemon_kind=target.daemon_kind,
            attempted=True,
            stopped=False,
            ok=False,
            reason="signal_failed",
            pid=pid,
            state=initial_state,
            detail=f"Failed to stop {target.daemon_kind} pid {pid}: {exc}",
        )

    refreshed_state = _wait_for_stop(
        target=target,
        status_dir=runtime_paths.status_dir,
        grace_seconds=grace_seconds,
        deps=deps,
    )
    stopped = not bool(refreshed_state.get("running"))
    stop_reason = str(refreshed_state.get("stop_reason") or "")
    reason = stop_reason or ("stopped" if stopped else "timeout")
    return DaemonStopResult(
        daemon_kind=target.daemon_kind,
        attempted=True,
        stopped=stopped,
        ok=stopped,
        reason=reason,
        pid=pid,
        signal="SIGINT",
        state=refreshed_state,
        detail=(
            f"Stopped {target.daemon_kind} pid {pid}"
            if stopped
            else f"Timed out waiting for {target.daemon_kind} pid {pid} to stop"
        ),
    )


def _wait_for_stop(
    *,
    target: StopTarget,
    status_dir,
    grace_seconds: float,
    deps: StopActionDeps,
) -> dict[str, object]:
    if grace_seconds <= 0:
        return target.read_state_fn(status_dir)
    deadline = deps.monotonic_fn() + grace_seconds
    while deps.monotonic_fn() < deadline:
        state = target.read_state_fn(status_dir)
        if not bool(state.get("running")):
            return state
        deps.sleep_fn(0.1)
    return target.read_state_fn(status_dir)
