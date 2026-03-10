"""Projection helpers for bridge-backed and event-backed review-channel state."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

from ..common import display_path
from .core import LaneAssignment, ensure_launcher_prereqs
from .handoff import (
    BridgeSnapshot,
    bridge_liveness_to_dict,
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from .projection_bundle import (
    ReviewChannelProjectionPaths,
    build_agent_registry_from_lanes,
    projection_paths_to_dict,
    write_projection_bundle,
)
from .promotion import (
    DEFAULT_PROMOTION_PLAN_REL,
    PromotionCandidate,
    derive_promotion_candidate,
    promotion_candidate_to_dict,
)
from ..time_utils import utc_timestamp

DEFAULT_REVIEW_STATUS_DIR_REL = "dev/reports/review_channel/latest"


@dataclass(frozen=True)
class ReviewStateSnapshot:
    """Typed container for one bridge-backed review-state projection.

    Replaces the raw dict previously built by ``_build_bridge_review_state``.
    Convert to a plain dict via ``dataclasses.asdict`` when the downstream
    consumer expects untyped mapping access.
    """

    schema_version: int
    command: str
    project_id: str
    timestamp: str
    ok: bool
    review: dict[str, object]
    agents: list[dict[str, object]]
    packets: list[dict[str, object]]
    queue: dict[str, object]
    bridge: dict[str, object]
    warnings: list[str]
    errors: list[str]


@dataclass(frozen=True)
class ReviewChannelStatusSnapshot:
    """Shared status-refresh result for read-only review consumers."""

    lanes: list[LaneAssignment]
    bridge_liveness: dict[str, object]
    warnings: list[str]
    errors: list[str]
    projection_paths: ReviewChannelProjectionPaths


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
    bridge_liveness = bridge_liveness_to_dict(summarize_bridge_liveness(snapshot))
    merged_warnings = list(warnings or [])
    merged_errors = list(errors or [])
    codex_poll_state = str(bridge_liveness.get("codex_poll_state") or "unknown")
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    if codex_poll_state == "missing":
        merged_warnings.append(
            "Bridge liveness is missing: the bridge header does not expose a "
            "usable `Last Codex poll` timestamp yet."
        )
    elif codex_poll_state == "stale":
        merged_warnings.append(
            "Bridge liveness is stale: the latest Codex poll timestamp is "
            "older than the five-minute heartbeat contract."
        )
    elif codex_poll_state == "poll_due":
        merged_warnings.append(
            "Bridge liveness is due for refresh: the latest Codex poll "
            "timestamp is older than the 2-3 minute reviewer cadence but "
            "still within the five-minute heartbeat window."
        )
    elif overall_state == "waiting_on_peer":
        merged_warnings.append(
            "Bridge liveness is waiting_on_peer: the current bridge state "
            "still needs a fresh reviewer poll or complete Claude status/ACK "
            "state before the next cycle."
        )
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
        warnings=merged_warnings,
        errors=merged_errors,
    )
    return ReviewChannelStatusSnapshot(
        lanes=lanes,
        bridge_liveness=bridge_liveness,
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
    review_state = _build_bridge_review_state(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        snapshot=snapshot,
        bridge_liveness=bridge_liveness,
        promotion_candidate=promotion_candidate,
        timestamp=timestamp,
        project_id=project_id_for_repo(repo_root),
        warnings=warnings,
        errors=errors,
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
                    == "waiting_on_peer"
                    else None
                ),
            },
            "claude": {"job_state": "assigned"},
        },
    )
    return write_projection_bundle(
        output_root=output_root,
        review_state=review_state,
        agent_registry=agent_registry,
        action="status",
        trace_events=[],
        full_extras={"bridge_liveness": bridge_liveness},
    )


def project_id_for_repo(repo_root: Path) -> str:
    """Build the stable repo identity used across review-channel artifacts."""
    digest = hashlib.sha256(str(repo_root.resolve()).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _build_bridge_review_state(
    *,
    repo_root: Path,
    bridge_path: Path,
    review_channel_path: Path,
    snapshot: BridgeSnapshot,
    bridge_liveness: dict[str, object],
    promotion_candidate: PromotionCandidate | None,
    timestamp: str,
    project_id: str,
    warnings: list[str],
    errors: list[str],
) -> dict[str, object]:
    """Build a typed review-state snapshot and return it as a plain dict."""
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    projection_ok = overall_state == "fresh" and not errors
    claude_status_present = bool(bridge_liveness.get("claude_status_present"))
    claude_status = _clean_section(snapshot.sections.get("Claude Status", ""))
    claude_ack = _clean_section(snapshot.sections.get("Claude Ack", ""))
    current_instruction = _clean_section(
        snapshot.sections.get("Current Instruction For Claude", "")
    )
    open_findings = _clean_section(snapshot.sections.get("Open Findings", ""))
    operator_status = (
        "waiting"
        if overall_state == "waiting_on_peer"
        else "warning"
        if overall_state == "stale"
        else "active"
    )
    state = ReviewStateSnapshot(
        schema_version=1,
        command="review-channel",
        project_id=project_id,
        timestamp=timestamp,
        ok=projection_ok,
        review={
            "plan_id": "MP-355",
            "controller_run_id": None,
            "session_id": "markdown-bridge",
            "surface_mode": "markdown-bridge",
            "active_lane": "review",
            "refresh_seq": 1,
            "bridge_path": display_path(bridge_path, repo_root=repo_root),
            "review_channel_path": display_path(review_channel_path, repo_root=repo_root),
        },
        agents=[
            {
                "agent_id": "codex",
                "display_name": "Codex",
                "role": "reviewer",
                "status": overall_state,
                "capabilities": ["review", "planning", "coordination"],
                "lane": "codex",
            },
            {
                "agent_id": "claude",
                "display_name": "Claude",
                "role": "implementer",
                "status": "active" if claude_status_present else "waiting",
                "capabilities": ["implementation", "fixes", "handoff"],
                "lane": "claude",
            },
            {
                "agent_id": "operator",
                "display_name": "Operator",
                "role": "approver",
                "status": operator_status,
                "capabilities": ["approval", "launch", "rollover"],
                "lane": "operator",
            },
        ],
        packets=[],
        queue={
            "pending_total": 0,
            "pending_codex": 0,
            "pending_claude": 0,
            "pending_operator": 0,
            "stale_packet_count": 0,
            "derived_next_instruction": (
                promotion_candidate.instruction if promotion_candidate is not None else None
            ),
            "derived_next_instruction_source": promotion_candidate_to_dict(
                promotion_candidate
            ),
        },
        bridge={
            "last_codex_poll_utc": snapshot.metadata.get("last_codex_poll_utc"),
            "last_codex_poll_age_seconds": bridge_liveness.get(
                "last_codex_poll_age_seconds"
            ),
            "last_worktree_hash": snapshot.metadata.get("last_non_audit_worktree_hash"),
            "open_findings": open_findings,
            "current_instruction": current_instruction,
            "claude_status": claude_status,
            "claude_ack": claude_ack,
            "last_reviewed_scope": _clean_section(
                snapshot.sections.get("Last Reviewed Scope", "")
            ),
        },
        warnings=warnings,
        errors=errors,
    )
    return asdict(state)


def _clean_section(raw: str) -> str:
    return raw.strip() or "(missing)"
