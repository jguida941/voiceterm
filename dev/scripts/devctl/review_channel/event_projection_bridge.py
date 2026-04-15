"""Bridge-state derivation helpers for event-backed review-state projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from hashlib import sha256

from ..runtime.conductor_capability import build_conductor_capability_state
from ..runtime.review_state_models import ReviewerRuntimeContract
from .current_session_projection import (
    current_session_mapping,
    event_agent_status,
    event_claude_ack,
    event_current_instruction,
    event_open_findings,
)
from .launch_truth import classify_launch_truth, effective_reviewer_mode
from .peer_liveness import (
    IMPLEMENTER_STALL_MARKERS,
    REVIEWER_WAIT_STATE_MARKERS,
    normalize_reviewer_mode,
)


def build_event_bridge_liveness_projection(
    review_state: Mapping[str, object],
    *,
    bridge_snapshot: object | None = None,
) -> dict[str, object]:
    """Build a fail-closed compatibility projection for event-backed liveness."""
    compat = _mapping(review_state.get("_compat"))
    runtime = _mapping(compat.get("runtime"))
    daemons = _mapping(runtime.get("daemons"))
    publisher = _mapping(daemons.get("publisher"))
    reviewer_supervisor = _mapping(daemons.get("reviewer_supervisor"))
    queue = _mapping(review_state.get("queue"))
    current_session = current_session_mapping(review_state)
    claude_status = event_agent_status(review_state, "claude")
    claude_ack = event_claude_ack(queue)
    open_findings = event_open_findings(review_state)
    reviewer_mode = (
        _bridge_snapshot_reviewer_mode(bridge_snapshot)
        or _event_reviewer_mode(runtime)
    )
    bridge_liveness: dict[str, object] = {}
    bridge_liveness["overall_state"] = (
        "stale" if review_state.get("errors") else "fresh"
    )
    bridge_liveness["codex_poll_state"] = (
        "fresh" if review_state.get("timestamp") else "missing"
    )
    bridge_liveness["reviewer_freshness"] = (
        "fresh" if review_state.get("timestamp") else "missing"
    )
    bridge_liveness["reviewer_mode"] = reviewer_mode
    bridge_liveness["last_codex_poll_utc"] = str(review_state.get("timestamp") or "")
    bridge_liveness["last_codex_poll_age_seconds"] = 0
    bridge_liveness["claude_status_present"] = bool(claude_status)
    bridge_liveness["claude_ack_present"] = bool(claude_ack)
    bridge_liveness["open_findings_present"] = bool(
        open_findings and open_findings != "none"
    )
    bridge_liveness["reviewed_hash_current"] = None
    bridge_liveness["implementer_completion_stall"] = detect_event_implementer_stall(
        claude_status=claude_status,
        claude_ack=claude_ack,
        instruction=event_current_instruction(review_state),
        poll_status=str(queue.get("derived_next_instruction") or ""),
        reviewer_mode=reviewer_mode,
    )
    bridge_liveness["publisher_running"] = bool(publisher.get("running"))
    bridge_liveness["reviewer_supervisor_running"] = bool(
        reviewer_supervisor.get("running")
    )
    bridge_liveness["publisher_stop_reason"] = str(publisher.get("stop_reason") or "")
    instruction_text = event_current_instruction(review_state)
    instruction_rev = (
        sha256(instruction_text.strip().encode("utf-8")).hexdigest()[:12]
        if instruction_text.strip()
        else ""
    )
    # Compatibility projection only: the event-backed reducer does not observe
    # reviewer-owned ACK/worktree truth, so these fields stay synthetic or
    # fail-closed instead of pretending to be authoritative runtime facts.
    bridge_liveness["current_instruction_revision"] = instruction_rev
    bridge_liveness["claude_ack_revision"] = ""
    bridge_liveness["claude_ack_current"] = False
    bridge_liveness["reviewer_poll_state"] = bridge_liveness["codex_poll_state"]
    bridge_liveness["last_reviewer_poll_utc"] = bridge_liveness["last_codex_poll_utc"]
    bridge_liveness["last_reviewer_poll_age_seconds"] = bridge_liveness[
        "last_codex_poll_age_seconds"
    ]
    bridge_liveness["implementer_status"] = str(
        current_session.get("implementer_status") or claude_status or ""
    )
    bridge_liveness["implementer_ack"] = str(
        current_session.get("implementer_ack") or claude_ack or ""
    )
    bridge_liveness["implementer_ack_revision"] = str(
        current_session.get("implementer_ack_revision") or ""
    )
    bridge_liveness["implementer_ack_current"] = (
        str(current_session.get("implementer_ack_state") or "").strip() == "current"
    )
    bridge_liveness["launch_truth"] = classify_launch_truth(bridge_liveness).value
    bridge_liveness["effective_reviewer_mode"] = effective_reviewer_mode(
        bridge_liveness
    )
    return bridge_liveness


def build_event_bridge_state_projection(
    *,
    review_state: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
    reviewer_runtime: ReviewerRuntimeContract | None = None,
) -> dict[str, object]:
    """Build the compatibility bridge-state projection for event-backed flows."""
    current_session = current_session_mapping(review_state)
    collaboration = _mapping(review_state.get("collaboration"))
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "tools_only")
    effective_mode = str(
        bridge_liveness.get("effective_reviewer_mode") or reviewer_mode
    )
    reviewer_poll_state = str(
        bridge_liveness.get("reviewer_poll_state")
        or bridge_liveness.get("codex_poll_state")
        or "missing"
    )
    reviewer_poll_utc = str(
        bridge_liveness.get("last_reviewer_poll_utc")
        or review_state.get("timestamp")
        or ""
    )
    reviewer_poll_age = int(
        bridge_liveness.get("last_reviewer_poll_age_seconds")
        or bridge_liveness.get("last_codex_poll_age_seconds")
        or 0
    )
    implementer_status = str(
        current_session.get("implementer_status")
        or bridge_liveness.get("implementer_status")
        or ""
    )
    implementer_ack = str(
        current_session.get("implementer_ack")
        or bridge_liveness.get("implementer_ack")
        or ""
    )
    implementer_ack_revision = str(
        current_session.get("implementer_ack_revision")
        or bridge_liveness.get("implementer_ack_revision")
        or ""
    )
    implementer_ack_current = (
        str(current_session.get("implementer_ack_state") or "").strip() == "current"
        or bool(bridge_liveness.get("implementer_ack_current"))
        or bool(bridge_liveness.get("claude_ack_current"))
    )
    reviewer_provider = _collaboration_provider(
        collaboration,
        role_id="review_agent",
        default="codex",
    )
    implementer_provider = _collaboration_provider(
        collaboration,
        role_id="coding_agent",
        default="claude",
    )
    bridge_state: dict[str, object] = {}
    bridge_state["overall_state"] = str(
        bridge_liveness.get("overall_state") or "unknown"
    )
    bridge_state["codex_poll_state"] = str(
        bridge_liveness.get("codex_poll_state") or "missing"
    )
    bridge_state["reviewer_freshness"] = str(
        bridge_liveness.get("reviewer_freshness") or "missing"
    )
    bridge_state["reviewer_mode"] = reviewer_mode
    bridge_state["last_codex_poll_utc"] = str(review_state.get("timestamp") or "")
    bridge_state["last_codex_poll_age_seconds"] = int(
        bridge_liveness.get("last_codex_poll_age_seconds") or 0
    )
    # Event-backed projections cannot observe reviewer-owned worktree truth yet.
    bridge_state["last_worktree_hash"] = ""
    bridge_state["implementer_completion_stall"] = bool(
        bridge_liveness.get("implementer_completion_stall")
    )
    bridge_state["publisher_running"] = bool(bridge_liveness.get("publisher_running"))
    bridge_state["open_findings"] = str(current_session.get("open_findings") or "")
    bridge_state["current_instruction"] = str(
        current_session.get("current_instruction") or ""
    )
    bridge_state["claude_status"] = implementer_status
    bridge_state["claude_ack"] = implementer_ack
    bridge_state["claude_ack_current"] = implementer_ack_current
    bridge_state["current_instruction_revision"] = str(
        current_session.get("current_instruction_revision") or ""
    )
    bridge_state["claude_ack_revision"] = implementer_ack_revision
    bridge_state["last_reviewed_scope"] = str(
        current_session.get("last_reviewed_scope") or ""
    )
    bridge_state["reviewer_poll_state"] = reviewer_poll_state
    bridge_state["last_reviewer_poll_utc"] = reviewer_poll_utc
    bridge_state["last_reviewer_poll_age_seconds"] = reviewer_poll_age
    bridge_state["implementer_status"] = implementer_status
    bridge_state["implementer_ack"] = implementer_ack
    bridge_state["implementer_ack_current"] = implementer_ack_current
    bridge_state["implementer_ack_revision"] = implementer_ack_revision
    bridge_state["launch_truth"] = str(bridge_liveness.get("launch_truth") or "")
    bridge_state["effective_reviewer_mode"] = effective_mode
    bridge_state["implementer_state_hash"] = str(
        current_session.get("implementer_state_hash") or ""
    )
    bridge_state["reviewed_hash_current"] = bridge_liveness.get("reviewed_hash_current")
    bridge_state["review_needed"] = bridge_liveness.get("review_needed")
    bridge_state["head_at_push_time"] = str(
        bridge_liveness.get("head_at_push_time") or ""
    )
    bridge_state["review_accepted"] = bool(
        reviewer_runtime.review_acceptance.review_accepted
        if reviewer_runtime is not None
        else False
    )
    bridge_state["codex_conductor_active"] = bool(
        bridge_liveness.get("codex_conductor_active")
    )
    bridge_state["claude_conductor_active"] = bool(
        bridge_liveness.get("claude_conductor_active")
    )
    bridge_state["reviewer_capability"] = asdict(
        build_conductor_capability_state(
            provider=reviewer_provider,
            reviewer_mode=effective_mode,
        )
    )
    bridge_state["implementer_capability"] = asdict(
        build_conductor_capability_state(
            provider=implementer_provider,
            reviewer_mode=effective_mode,
        )
    )
    return bridge_state


def _collaboration_provider(
    collaboration: Mapping[str, object],
    *,
    role_id: str,
    default: str,
) -> str:
    assignments = collaboration.get("role_assignments")
    if not isinstance(assignments, list):
        return default
    for row in assignments:
        assignment = _mapping(row)
        if str(assignment.get("role_id") or "").strip() != role_id:
            continue
        provider = str(assignment.get("provider") or "").strip()
        if provider:
            return provider
    return default


def _event_reviewer_mode(runtime: Mapping[str, object]) -> str:
    daemons = _mapping(runtime.get("daemons"))
    for daemon_name in ("publisher", "reviewer_supervisor"):
        daemon_state = _mapping(daemons.get(daemon_name))
        reviewer_mode = str(daemon_state.get("reviewer_mode") or "").strip()
        if reviewer_mode:
            return reviewer_mode
    return "tools_only"


def _bridge_snapshot_reviewer_mode(snapshot: object | None) -> str:
    metadata = getattr(snapshot, "metadata", None)
    if not isinstance(metadata, Mapping):
        metadata = _mapping(snapshot).get("metadata")
    if not isinstance(metadata, Mapping):
        return ""
    return str(normalize_reviewer_mode(metadata.get("reviewer_mode")) or "").strip()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def detect_event_implementer_stall(
    *,
    claude_status: str,
    claude_ack: str,
    instruction: str,
    poll_status: str,
    reviewer_mode: str,
) -> bool:
    """Detect implementer completion stall from event-backed state."""
    from .peer_liveness import reviewer_mode_is_active

    combined = f"{claude_status}\n{claude_ack}".lower()
    if not any(marker in combined for marker in IMPLEMENTER_STALL_MARKERS):
        return False
    instruction_lower = instruction.lower()
    if any(marker in instruction_lower for marker in REVIEWER_WAIT_STATE_MARKERS):
        return False
    if not reviewer_mode_is_active(reviewer_mode):
        return True
    return True
