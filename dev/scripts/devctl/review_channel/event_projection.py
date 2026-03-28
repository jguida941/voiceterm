"""Projection helpers shared by event-backed review-channel outputs."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from ..runtime.review_state_models import ReviewQueueState
from .attention import derive_bridge_attention
from .attach_auth_policy import build_attach_auth_policy
from .attach_auth_projection import (
    build_attach_auth_policy_state,
    build_service_identity_state,
)
from .core import DEFAULT_BRIDGE_REL
from .current_session_projection import (
    build_event_current_session,
    current_session_mapping,
    current_session_payload,
    event_agent_status,
    event_claude_ack,
    event_current_instruction,
    event_open_findings,
)
from .event_projection_context import (
    append_event_instruction_context,
    build_event_context_packet,
    build_instruction_source,
)
from .peer_liveness import (
    IMPLEMENTER_STALL_MARKERS,
    REVIEWER_WAIT_STATE_MARKERS,
)
from .service_identity import build_service_identity


def build_event_queue_summary(
    pending_counts: dict[str, int],
    stale_packet_count: int,
    *,
    packets: list[dict[str, object]],
) -> dict[str, object]:
    """Build the event-backed queue summary plus derived next-step hint."""
    derived_instruction, derived_source = _derived_next_instruction_bundle(packets)
    summary: dict[str, object] = {
        "pending_total": sum(pending_counts.values()),
        "derived_next_instruction": derived_instruction,
        "derived_next_instruction_source": derived_source,
    }
    for provider, count in pending_counts.items():
        summary[f"pending_{provider}"] = count
    summary["stale_packet_count"] = stale_packet_count
    return summary


def build_event_queue_state(
    pending_counts: dict[str, int],
    stale_packet_count: int,
    packet_rows: list[dict[str, object]],
) -> ReviewQueueState:
    """Build a typed ReviewQueueState from event reduction outputs."""
    derived_instruction, derived_source = _derived_next_instruction_bundle(packet_rows)
    return ReviewQueueState(
        pending_total=sum(pending_counts.values()),
        pending_codex=pending_counts.get("codex", 0),
        pending_claude=pending_counts.get("claude", 0),
        pending_cursor=pending_counts.get("cursor", 0),
        pending_operator=pending_counts.get("operator", 0),
        stale_packet_count=stale_packet_count,
        derived_next_instruction=derived_instruction,
        derived_next_instruction_source=derived_source,
    )


def enrich_event_review_state(
    *,
    review_state: dict[str, object],
    repo_root: Path,
    review_channel_path: Path,
    projections_root: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    """Attach parity fields needed by event-backed review-state projections."""
    review_state = dict(review_state)
    raw_service_identity = build_service_identity(
        repo_root=repo_root,
        bridge_path=repo_root / DEFAULT_BRIDGE_REL,
        review_channel_path=review_channel_path,
        output_root=projections_root,
    )
    raw_attach_auth_policy = build_attach_auth_policy(
        service_identity=raw_service_identity
    )
    bridge_liveness = _build_event_bridge_liveness(review_state)
    current_session = build_event_current_session(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
    )
    review_state["current_session"] = current_session_payload(current_session)
    attention = derive_bridge_attention(bridge_liveness)
    review_state["bridge"] = _build_event_bridge_state(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
    )
    review_state["attention"] = attention
    existing_compat = review_state.get("_compat")
    merged_compat = dict(existing_compat) if isinstance(existing_compat, dict) else {}
    merged_compat["service_identity"] = build_service_identity_state(raw_service_identity)
    merged_compat["attach_auth_policy"] = build_attach_auth_policy_state(
        raw_attach_auth_policy
    )
    review_state["_compat"] = merged_compat
    return review_state, {
        "bridge_liveness": bridge_liveness,
        "attention": attention,
        "service_identity": raw_service_identity,
        "attach_auth_policy": raw_attach_auth_policy,
    }


def _build_event_bridge_liveness(review_state: Mapping[str, object]) -> dict[str, object]:
    compat = _mapping(review_state.get("_compat"))
    runtime = _mapping(compat.get("runtime"))
    daemons = _mapping(runtime.get("daemons"))
    publisher = _mapping(daemons.get("publisher"))
    queue = _mapping(review_state.get("queue"))
    claude_status = event_agent_status(review_state, "claude")
    claude_ack = event_claude_ack(queue)
    reviewer_mode = _event_reviewer_mode(runtime)
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
    bridge_liveness["last_codex_poll_age_seconds"] = 0
    bridge_liveness["claude_status_present"] = bool(claude_status)
    bridge_liveness["claude_ack_present"] = bool(claude_ack)
    bridge_liveness["open_findings_present"] = bool(event_open_findings(queue))
    bridge_liveness["reviewed_hash_current"] = None
    bridge_liveness["implementer_completion_stall"] = _detect_implementer_stall(
        claude_status=claude_status,
        claude_ack=claude_ack,
        instruction=event_current_instruction(review_state),
        poll_status=str(queue.get("derived_next_instruction") or ""),
        reviewer_mode=reviewer_mode,
    )
    bridge_liveness["publisher_running"] = bool(publisher.get("running"))
    bridge_liveness["publisher_stop_reason"] = str(publisher.get("stop_reason") or "")
    instruction_text = event_current_instruction(review_state)
    instruction_rev = (
        sha256(instruction_text.strip().encode("utf-8")).hexdigest()[:12]
        if instruction_text.strip()
        else ""
    )
    # The event-backed path cannot verify the real Claude ACK revision token
    # (it lives in bridge markdown, not in structured events). Report the
    # instruction revision for reference, but mark ACK freshness as unknown
    # so consumers don't false-green on queue-derived shortcuts.
    bridge_liveness["current_instruction_revision"] = instruction_rev
    bridge_liveness["claude_ack_revision"] = ""
    bridge_liveness["claude_ack_current"] = False
    return bridge_liveness


def _build_event_bridge_state(
    *,
    review_state: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
) -> dict[str, object]:
    current_session = current_session_mapping(review_state)
    bridge_state: dict[str, object] = {}
    bridge_state["overall_state"] = str(bridge_liveness.get("overall_state") or "unknown")
    bridge_state["codex_poll_state"] = str(bridge_liveness.get("codex_poll_state") or "missing")
    bridge_state["reviewer_freshness"] = str(
        bridge_liveness.get("reviewer_freshness") or "missing"
    )
    bridge_state["reviewer_mode"] = str(
        bridge_liveness.get("reviewer_mode") or "tools_only"
    )
    bridge_state["last_codex_poll_utc"] = str(review_state.get("timestamp") or "")
    bridge_state["last_codex_poll_age_seconds"] = int(
        bridge_liveness.get("last_codex_poll_age_seconds") or 0
    )
    bridge_state["last_worktree_hash"] = ""
    bridge_state["implementer_completion_stall"] = bool(
        bridge_liveness.get("implementer_completion_stall")
    )
    bridge_state["publisher_running"] = bool(bridge_liveness.get("publisher_running"))
    bridge_state["open_findings"] = str(current_session.get("open_findings") or "")
    bridge_state["current_instruction"] = str(
        current_session.get("current_instruction") or ""
    )
    bridge_state["claude_status"] = str(
        current_session.get("implementer_status") or ""
    )
    bridge_state["claude_ack"] = str(current_session.get("implementer_ack") or "")
    bridge_state["claude_ack_current"] = bool(
        bridge_liveness.get("claude_ack_current")
    )
    bridge_state["current_instruction_revision"] = str(
        current_session.get("current_instruction_revision") or ""
    )
    bridge_state["claude_ack_revision"] = str(
        current_session.get("implementer_ack_revision") or ""
    )
    bridge_state["last_reviewed_scope"] = str(
        current_session.get("last_reviewed_scope") or ""
    )
    # Event-backed projections do not yet carry reviewer verdict semantics, so
    # keep the transitional acceptance gate fail-closed instead of inventing a
    # non-reviewer-owned proxy signal.
    bridge_state["review_accepted"] = False
    return bridge_state


def _event_reviewer_mode(runtime: Mapping[str, object]) -> str:
    daemons = _mapping(runtime.get("daemons"))
    for daemon_name in ("publisher", "reviewer_supervisor"):
        daemon_state = _mapping(daemons.get(daemon_name))
        reviewer_mode = str(daemon_state.get("reviewer_mode") or "").strip()
        if reviewer_mode:
            return reviewer_mode
    return "tools_only"


def _derived_next_instruction(packets: list[dict[str, object]]) -> str:
    return _derived_next_instruction_bundle(packets)[0]


def _derived_next_instruction_bundle(
    packets: list[dict[str, object]],
) -> tuple[str, dict[str, object]]:
    now_utc = datetime.now(timezone.utc)
    for packet in packets:
        if packet.get("status") != "pending":
            continue
        if _is_expired(packet, now_utc):
            continue
        summary = str(packet.get("summary") or "").strip()
        if summary:
            context_packet = build_event_context_packet(packet)
            instruction = append_event_instruction_context(summary, context_packet)
            return instruction, build_instruction_source(packet, context_packet)
    return "", {}


def _derived_next_instruction_source(
    packets: list[dict[str, object]],
) -> dict[str, object]:
    return _derived_next_instruction_bundle(packets)[1]


def _is_expired(packet: dict[str, object], now_utc: datetime) -> bool:
    """Return True if the packet's expires_at_utc is in the past."""
    from .event_store import parse_utc

    expires_at = parse_utc(packet.get("expires_at_utc"))
    return expires_at is not None and expires_at <= now_utc


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


# Stall detection markers (shared contract with tandem_consistency checks).
_STALL_MARKERS = IMPLEMENTER_STALL_MARKERS
_REVIEWER_WAIT_MARKERS = REVIEWER_WAIT_STATE_MARKERS


def _detect_implementer_stall(
    *,
    claude_status: str,
    claude_ack: str,
    instruction: str,
    poll_status: str,
    reviewer_mode: str,
) -> bool:
    """Detect implementer completion stall from event-backed state.

    Returns True when the implementer appears parked on reviewer promotion
    while the current instruction is still active and no reviewer-owned
    wait-state marker is present in the instruction content.

    The event-backed path does not own a separate ``Poll Status`` bridge
    section, so wait-state detection uses only the instruction text and
    reviewer mode — evidence the event path actually owns.
    """
    from .peer_liveness import reviewer_mode_is_active

    combined = f"{claude_status}\n{claude_ack}".lower()
    if not any(marker in combined for marker in _STALL_MARKERS):
        return False
    # Only check instruction for wait markers — event path does not own Poll Status
    instruction_lower = instruction.lower()
    if any(m in instruction_lower for m in _REVIEWER_WAIT_MARKERS):
        return False
    # If reviewer mode is not active but implementer claims waiting → stalled
    if not reviewer_mode_is_active(reviewer_mode):
        return True
    # Active mode, no wait marker in instruction, stall markers in status/ack → stalled
    return True
