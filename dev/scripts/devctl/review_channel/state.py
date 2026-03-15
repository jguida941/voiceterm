"""Projection helpers for bridge-backed and event-backed review-channel state."""

from __future__ import annotations

from pathlib import Path

from ..repo_packs.voiceterm import VOICETERM_PATH_CONFIG

DEFAULT_REVIEW_STATUS_DIR_REL = VOICETERM_PATH_CONFIG.review_status_dir_rel
from .attention import derive_bridge_attention
from .core import LaneAssignment, ensure_launcher_prereqs
from .handoff import (
    bridge_liveness_to_dict,
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from .heartbeat import compute_non_audit_worktree_hash
from .peer_liveness import CodexPollState, OverallLivenessState
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
    if codex_poll_state == CodexPollState.MISSING:
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
