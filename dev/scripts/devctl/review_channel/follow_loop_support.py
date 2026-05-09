"""Shared support helpers for review-channel follow-loop sessions."""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Callable

from .daemon_events import DaemonEventContext
from .follow_lifecycle import FollowLifecycleContext
from .handoff import extract_bridge_snapshot
from .heartbeat import bridge_excluded_rel_paths, compute_non_audit_worktree_hash
from .pending_packets import load_pending_reviewer_packets


@dataclass(frozen=True)
class FollowLoopSettings:
    """Derived cadence settings for one follow-loop session."""

    interval_seconds: int
    max_snapshots: int
    deadline: float
    inactivity_timeout_seconds: int


@dataclass(frozen=True)
class FollowLoopContext:
    """Runtime state shared across loop iterations."""

    args: object
    status_dir: object
    started_at: str
    daemon_context: DaemonEventContext
    lifecycle_context: FollowLifecycleContext
    invocation_provenance: dict[str, object]


@dataclass(frozen=True)
class FollowLoopContextInputs:
    """Bundle of inputs required to build one follow-loop context."""

    args: object
    repo_root: Path
    artifact_paths: object
    status_dir: object
    daemon_kind: str
    write_heartbeat_fn: Callable[..., Path]
    heartbeat_factory: Callable[..., object]
    utc_timestamp_fn: Callable[[], str]


def build_follow_loop_settings(args) -> FollowLoopSettings:
    interval_seconds = max(1, int(getattr(args, "follow_interval_seconds", 150)))
    max_snapshots = getattr(args, "max_follow_snapshots", 0) or 0
    timeout_minutes = getattr(args, "timeout_minutes", 0) or 0
    inactivity_timeout_seconds = max(
        0,
        int(getattr(args, "follow_inactivity_timeout_seconds", 3600)),
    )
    deadline = (time.monotonic() + timeout_minutes * 60) if timeout_minutes > 0 else 0
    return FollowLoopSettings(
        interval_seconds=interval_seconds,
        max_snapshots=max_snapshots,
        deadline=deadline,
        inactivity_timeout_seconds=inactivity_timeout_seconds,
    )


def build_follow_loop_context(
    inputs: FollowLoopContextInputs,
) -> FollowLoopContext:
    started_at = inputs.utc_timestamp_fn()
    invocation_provenance = build_invocation_provenance()
    daemon_context = DaemonEventContext(
        repo_root=inputs.repo_root,
        artifact_paths=inputs.artifact_paths,
        daemon_kind=inputs.daemon_kind,
        pid=os.getpid(),
        invocation_provenance=invocation_provenance,
    )
    lifecycle_context = FollowLifecycleContext(
        output_root=inputs.status_dir,
        write_heartbeat_fn=inputs.write_heartbeat_fn,
        heartbeat_factory=inputs.heartbeat_factory,
        daemon_context=daemon_context,
        utc_timestamp_fn=inputs.utc_timestamp_fn,
        invocation_provenance=invocation_provenance,
    )
    return FollowLoopContext(
        args=inputs.args,
        status_dir=inputs.status_dir,
        started_at=started_at,
        daemon_context=daemon_context,
        lifecycle_context=lifecycle_context,
        invocation_provenance=invocation_provenance,
    )


def build_invocation_provenance() -> dict[str, object]:
    """Return process/supervisor provenance for daemon lifecycle receipts."""
    return dict(
        (
            ("contract_id", "InvocationProvenance"),
            ("schema_version", 1),
            ("parent_pid", os.getppid()),
            ("process_pid", os.getpid()),
            ("launchd_label", os.environ.get("DEVCTL_LAUNCHD_LABEL", "")),
            ("daemon_supervisor", os.environ.get("DEVCTL_DAEMON_SUPERVISOR", "")),
            ("trigger_reason", os.environ.get("DEVCTL_TRIGGER_REASON", "")),
            ("command_line", list(sys.argv)),
        )
    )


def build_claude_progress_token(
    *,
    repo_root: Path,
    bridge_path: Path,
) -> str:
    """Build the token used to detect Claude-side follow progress."""
    try:
        bridge_text = bridge_path.read_text(encoding="utf-8")
    except OSError:
        return ""

    snapshot = extract_bridge_snapshot(bridge_text)
    claude_status = snapshot.sections.get("Implementer Status", "").strip()
    claude_ack = snapshot.sections.get("Implementer Ack", "").strip()
    try:
        current_worktree_hash = compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=bridge_excluded_rel_paths(
                repo_root=repo_root,
                bridge_path=bridge_path,
            ),
        )
    except (OSError, ValueError):
        current_worktree_hash = ""
    pending_packet_ids = "\n".join(
        sorted(
            str(packet.get("packet_id") or "").strip()
            for packet in load_pending_reviewer_packets(repo_root)
            if isinstance(packet, dict) and str(packet.get("packet_id") or "").strip()
        )
    )

    payload = "\0".join(
        (
            claude_status,
            claude_ack,
            current_worktree_hash,
            pending_packet_ids,
        )
    ).strip("\0")
    if not payload:
        return ""
    return sha256(payload.encode("utf-8")).hexdigest()
