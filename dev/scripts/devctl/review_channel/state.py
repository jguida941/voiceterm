"""Projection helpers for bridge-backed and event-backed review-channel state."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..repo_packs import active_path_config

DEFAULT_REVIEW_STATUS_DIR_REL = active_path_config().review_status_dir_rel
PUBLISHER_HEARTBEAT_FILENAME = "publisher_heartbeat.json"
PUBLISHER_STALE_AFTER_SECONDS = 300

from .attention import derive_bridge_attention
from .core import LaneAssignment, ensure_launcher_prereqs
from .handoff import (
    bridge_liveness_to_dict,
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from .heartbeat import compute_non_audit_worktree_hash
from .peer_liveness import CodexPollState, OverallLivenessState, reviewer_mode_is_active
from .projection_bundle import (
    ReviewChannelProjectionPaths,
    build_agent_registry_from_lanes,
    projection_paths_to_dict as projection_paths_to_dict,
    write_projection_bundle,
)
from .promotion import DEFAULT_PROMOTION_PLAN_REL, derive_promotion_candidate
from .status_models import ReviewChannelStatusSnapshot
from .status_projection import (
    ReviewStateContext,
    build_bridge_review_state,
    project_id_for_repo,
)
from ..time_utils import utc_timestamp


def refresh_status_snapshot(
    *,
    repo_root: Path,
    bridge_path: Path,
    review_channel_path: Path,
    output_root: Path,
    promotion_plan_path: Path | None = None,
    execution_mode: str = "markdown-bridge",
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    reviewer_overdue_threshold_seconds: int | None = None,
) -> ReviewChannelStatusSnapshot:
    """Refresh the latest review-channel projections for read-only consumers."""
    _, lanes = ensure_launcher_prereqs(
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        execution_mode=execution_mode,
    )
    snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
    try:
        current_hash = compute_non_audit_worktree_hash(
            repo_root=repo_root, excluded_rel_paths=("code_audit.md",)
        )
    except (ValueError, OSError):
        current_hash = None
    bridge_liveness = bridge_liveness_to_dict(
        summarize_bridge_liveness(snapshot, current_worktree_hash=current_hash)
    )
    merged_warnings = list(warnings or [])
    merged_errors = list(errors or [])
    codex_poll_state = str(bridge_liveness.get("codex_poll_state") or "unknown")
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    if not reviewer_mode_is_active(reviewer_mode):
        merged_warnings.append(
            "Bridge reviewer mode is inactive; live heartbeat freshness is not enforced until the reviewer resumes active_dual_agent mode."
        )
    elif codex_poll_state == CodexPollState.MISSING:
        merged_warnings.append(
            "Bridge liveness is missing: the bridge header does not expose a "
            "usable `Last Codex poll` timestamp yet."
        )
    elif codex_poll_state == CodexPollState.STALE:
        merged_warnings.append(
            "Bridge liveness is stale: the latest Codex poll timestamp is "
            "older than the five-minute heartbeat contract."
        )
    elif codex_poll_state == CodexPollState.POLL_DUE:
        merged_warnings.append(
            "Bridge liveness is due for refresh: the latest Codex poll "
            "timestamp is older than the 2-3 minute reviewer cadence but "
            "still within the five-minute heartbeat window."
        )
    elif overall_state == OverallLivenessState.WAITING_ON_PEER:
        merged_warnings.append(
            "Bridge liveness is waiting_on_peer: the current bridge state "
            "still needs a fresh reviewer poll or complete Claude status/ACK "
            "state before the next cycle."
        )
    if bridge_liveness.get("reviewed_hash_current") is False:
        merged_warnings.append(
            "Bridge review content is stale: the worktree has changed since "
            "the last reviewed hash. Current Verdict, Open Findings, and "
            "Current Instruction may not reflect the current tree state."
        )
    publisher_state = read_publisher_state(output_root)
    bridge_liveness["publisher_running"] = bool(publisher_state.get("running"))
    if reviewer_overdue_threshold_seconds is not None:
        bridge_liveness["reviewer_overdue_threshold_seconds"] = reviewer_overdue_threshold_seconds
    attention = derive_bridge_attention(bridge_liveness)
    projection_paths = write_status_projection_bundle(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=output_root,
        promotion_plan_path=(
            promotion_plan_path
            if promotion_plan_path is not None
            else repo_root / DEFAULT_PROMOTION_PLAN_REL
        ),
        lanes=lanes,
        bridge_liveness=bridge_liveness,
        attention=attention,
        warnings=merged_warnings,
        errors=merged_errors,
    )
    return ReviewChannelStatusSnapshot(
        lanes=lanes,
        bridge_liveness=bridge_liveness,
        attention=attention,
        warnings=merged_warnings,
        errors=merged_errors,
        projection_paths=projection_paths,
    )


def write_status_projection_bundle(
    *,
    repo_root: Path,
    bridge_path: Path,
    review_channel_path: Path,
    output_root: Path,
    promotion_plan_path: Path,
    lanes: list[LaneAssignment],
    bridge_liveness: dict[str, object],
    attention: dict[str, object],
    warnings: list[str],
    errors: list[str],
) -> ReviewChannelProjectionPaths:
    """Write bridge-backed status projections for operator/read-only consumers."""
    snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
    timestamp = utc_timestamp()
    promotion_candidate = derive_promotion_candidate(
        repo_root=repo_root,
        promotion_plan_path=promotion_plan_path,
        require_exists=False,
    )
    review_state = build_bridge_review_state(
        context=ReviewStateContext(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            project_id=project_id_for_repo(repo_root),
            timestamp=timestamp,
            warnings=tuple(warnings),
            errors=tuple(errors),
        ),
        snapshot=snapshot,
        bridge_liveness=bridge_liveness,
        attention=attention,
        promotion_candidate=promotion_candidate,
    )
    agent_registry = build_agent_registry_from_lanes(
        lanes,
        timestamp=timestamp,
        provider_state={
            "codex": {
                "job_state": str(bridge_liveness.get("overall_state") or "unknown"),
                "waiting_on": (
                    "peer"
                    if str(bridge_liveness.get("overall_state") or "unknown")
                    == OverallLivenessState.WAITING_ON_PEER
                    else None
                ),
            },
            "claude": {
                "job_state": (
                    "assigned"
                    if bool(bridge_liveness.get("claude_status_present"))
                    and bool(bridge_liveness.get("claude_ack_present"))
                    else "waiting"
                ),
            },
        },
    )
    return write_projection_bundle(
        output_root=output_root,
        review_state=review_state,
        agent_registry=agent_registry,
        action="status",
        trace_events=[],
        full_extras={"bridge_liveness": bridge_liveness, "attention": attention},
    )


@dataclass(frozen=True)
class PublisherHeartbeat:
    """One heartbeat tick from the persistent ensure-follow publisher."""

    pid: int
    started_at_utc: str
    last_heartbeat_utc: str
    snapshots_emitted: int
    reviewer_mode: str
    stop_reason: str = ""
    stopped_at_utc: str = ""


def write_publisher_heartbeat(
    output_root: Path,
    heartbeat: PublisherHeartbeat,
) -> Path:
    """Write the publisher heartbeat file for lifecycle consumers."""
    path = output_root / PUBLISHER_HEARTBEAT_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(heartbeat), indent=2),
        encoding="utf-8",
    )
    return path


def read_publisher_state(output_root: Path) -> dict[str, object]:
    """Read publisher lifecycle state from the heartbeat file.

    Returns a dict with ``running``, ``pid``, ``stale``, and heartbeat
    metadata.  ``running`` is True only when the recorded PID is alive
    AND the heartbeat is fresh (within ``PUBLISHER_STALE_AFTER_SECONDS``).
    """
    path = output_root / PUBLISHER_HEARTBEAT_FILENAME
    if not path.exists():
        return {"running": False, "detail": "No publisher heartbeat file found"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"running": False, "detail": "Publisher heartbeat file is corrupt"}
    pid = data.get("pid", 0)
    pid_alive = _pid_is_alive(pid)
    last_hb = data.get("last_heartbeat_utc", "")
    age_seconds = _heartbeat_age_seconds(last_hb)
    stale = age_seconds is None or age_seconds > PUBLISHER_STALE_AFTER_SECONDS
    running = pid_alive and not stale
    publisher_state: dict[str, object] = {}
    publisher_state["running"] = running
    publisher_state["pid"] = pid
    publisher_state["pid_alive"] = pid_alive
    publisher_state["stale"] = stale
    publisher_state["heartbeat_age_seconds"] = age_seconds
    publisher_state["started_at_utc"] = data.get("started_at_utc")
    publisher_state["last_heartbeat_utc"] = last_hb
    publisher_state["snapshots_emitted"] = data.get("snapshots_emitted", 0)
    publisher_state["reviewer_mode"] = data.get("reviewer_mode", "unknown")
    publisher_state["stop_reason"] = data.get("stop_reason", "")
    publisher_state["stopped_at_utc"] = data.get("stopped_at_utc", "")
    return publisher_state


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _heartbeat_age_seconds(timestamp_str: str) -> float | None:
    if not timestamp_str:
        return None
    try:
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - ts).total_seconds()
    except (ValueError, TypeError):
        return None
