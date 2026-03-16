"""Helpers for bridge-backed review-state projection payloads."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TypedDict

from ..common import display_path
from ..runtime.role_profile import TandemRole
from .handoff import BridgeSnapshot
from .peer_liveness import OverallLivenessState
from .promotion import PromotionCandidate, promotion_candidate_to_dict


class ReviewMeta(TypedDict):
    """Typed review session metadata."""

    plan_id: str
    controller_run_id: None
    session_id: str
    surface_mode: str
    active_lane: str
    refresh_seq: int
    bridge_path: str
    review_channel_path: str


class AgentEntry(TypedDict):
    """Typed agent roster entry."""

    agent_id: str
    display_name: str
    role: str
    status: str
    capabilities: list[str]
    lane: str


class QueueState(TypedDict):
    """Typed packet queue summary."""

    pending_total: int
    pending_codex: int
    pending_claude: int
    pending_cursor: int
    pending_operator: int
    stale_packet_count: int
    derived_next_instruction: str | None
    derived_next_instruction_source: dict[str, Any] | None


class BridgeState(TypedDict):
    """Typed bridge section snapshot."""

    reviewer_mode: str
    last_codex_poll_utc: str | None
    last_codex_poll_age_seconds: int | None
    last_worktree_hash: str | None
    reviewed_hash_current: bool | None
    implementer_completion_stall: bool
    publisher_running: bool
    open_findings: str
    current_instruction: str
    claude_status: str
    claude_ack: str
    last_reviewed_scope: str


@dataclass(frozen=True)
class ReviewStateContext:
    """Grouped path/identity context for review-state projection."""

    repo_root: Path
    bridge_path: Path
    review_channel_path: Path
    project_id: str
    timestamp: str
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewStateSnapshot:
    """Typed container for one bridge-backed review-state projection."""

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
    attention: dict[str, object]
    warnings: list[str]
    errors: list[str]


def project_id_for_repo(repo_root: Path) -> str:
    """Build the stable repo identity used across review-channel artifacts."""
    digest = hashlib.sha256(str(repo_root.resolve()).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def build_bridge_review_state(
    *,
    context: ReviewStateContext,
    snapshot: BridgeSnapshot,
    bridge_liveness: dict[str, object],
    attention: dict[str, object],
    promotion_candidate: PromotionCandidate | None,
) -> dict[str, object]:
    """Build a typed review-state snapshot and return it as a plain dict."""
    warnings = list(context.warnings)
    errors = list(context.errors)
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    projection_ok = overall_state == OverallLivenessState.FRESH and not errors
    if overall_state == OverallLivenessState.INACTIVE and not errors:
        projection_ok = True
    claude_status_present = bool(bridge_liveness.get("claude_status_present"))
    claude_status = _clean_section(snapshot.sections.get("Claude Status", ""))
    claude_ack = _clean_section(snapshot.sections.get("Claude Ack", ""))
    current_instruction = _clean_section(
        snapshot.sections.get("Current Instruction For Claude", "")
    )
    open_findings = _clean_section(snapshot.sections.get("Open Findings", ""))
    operator_status = (
        "waiting"
        if overall_state == OverallLivenessState.WAITING_ON_PEER
        else "warning"
        if overall_state == OverallLivenessState.STALE
        else "idle"
        if overall_state == OverallLivenessState.INACTIVE
        else "active"
    )
    state = ReviewStateSnapshot(
        schema_version=1,
        command="review-channel",
        project_id=context.project_id,
        timestamp=context.timestamp,
        ok=projection_ok,
        review=ReviewMeta(
            plan_id="MP-355",
            controller_run_id=None,
            session_id="markdown-bridge",
            surface_mode="markdown-bridge",
            active_lane="review",
            refresh_seq=1,
            bridge_path=display_path(context.bridge_path, repo_root=context.repo_root),
            review_channel_path=display_path(context.review_channel_path, repo_root=context.repo_root),
        ),
        agents=[
            AgentEntry(
                agent_id="codex",
                display_name="Codex",
                role=TandemRole.REVIEWER,
                status=overall_state,
                capabilities=["review", "planning", "coordination"],
                lane="codex",
            ),
            AgentEntry(
                agent_id="claude",
                display_name="Claude",
                role=TandemRole.IMPLEMENTER,
                status=(
                    "active"
                    if claude_status_present
                    and bool(bridge_liveness.get("claude_ack_present"))
                    else "waiting"
                ),
                capabilities=["implementation", "fixes", "handoff"],
                lane="claude",
            ),
            AgentEntry(
                agent_id="cursor",
                display_name="Cursor",
                role=TandemRole.IMPLEMENTER,
                status="idle",
                capabilities=["implementation", "fixes", "handoff"],
                lane="cursor",
            ),
            AgentEntry(
                agent_id="operator",
                display_name="Operator",
                role="approver",
                status=operator_status,
                capabilities=["approval", "launch", "rollover"],
                lane="operator",
            ),
        ],
        packets=[],
        queue=QueueState(
            pending_total=0,
            pending_codex=0,
            pending_claude=0,
            pending_cursor=0,
            pending_operator=0,
            stale_packet_count=0,
            derived_next_instruction=(
                promotion_candidate.instruction if promotion_candidate is not None else None
            ),
            derived_next_instruction_source=promotion_candidate_to_dict(
                promotion_candidate
            ),
        ),
        bridge=BridgeState(
            reviewer_mode=str(bridge_liveness.get("reviewer_mode") or "active_dual_agent"),
            last_codex_poll_utc=snapshot.metadata.get("last_codex_poll_utc"),
            last_codex_poll_age_seconds=bridge_liveness.get(
                "last_codex_poll_age_seconds"
            ),
            last_worktree_hash=snapshot.metadata.get("last_non_audit_worktree_hash"),
            reviewed_hash_current=bridge_liveness.get("reviewed_hash_current"),
            implementer_completion_stall=bool(bridge_liveness.get("implementer_completion_stall")),
            publisher_running=bool(bridge_liveness.get("publisher_running")),
            open_findings=open_findings,
            current_instruction=current_instruction,
            claude_status=claude_status,
            claude_ack=claude_ack,
            last_reviewed_scope=_clean_section(
                snapshot.sections.get("Last Reviewed Scope", "")
            ),
        ),
        attention=attention,
        warnings=warnings,
        errors=errors,
    )
    return asdict(state)


def _clean_section(raw: str) -> str:
    return raw.strip() or "(missing)"
