"""Shared current-session helpers for review-channel projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from ..runtime.review_state_semantics import classify_implementer_ack_state
from ..runtime.review_state_models import ReviewCurrentSessionState
from .handoff import BridgeSnapshot
from .handoff_constants import _is_substantive_text
from .session_state_hints import provider_session_state_hint
from .status_projection_helpers import clean_section


def build_bridge_current_session(
    snapshot: BridgeSnapshot,
    bridge_liveness: Mapping[str, object],
) -> ReviewCurrentSessionState:
    """Build typed current-session state from bridge sections."""
    implementer_status = _section_text(snapshot, "Claude Status")
    implementer_ack = _section_text(snapshot, "Claude Ack")
    claude_hint = provider_session_state_hint(dict(bridge_liveness), provider="claude")
    return ReviewCurrentSessionState(
        current_instruction=_section_text(snapshot, "Current Instruction For Claude"),
        current_instruction_revision=str(
            bridge_liveness.get("current_instruction_revision") or ""
        ),
        implementer_status=implementer_status,
        implementer_ack=implementer_ack,
        implementer_ack_revision=str(bridge_liveness.get("claude_ack_revision") or ""),
        implementer_ack_state=classify_implementer_ack_state(
            implementer_status=implementer_status,
            implementer_ack=implementer_ack,
            ack_current=bool(bridge_liveness.get("claude_ack_current")),
            stale_label="stale",
            is_substantive_text=_is_substantive_text,
        ),
        implementer_session_state=str(claude_hint.get("state") or ""),
        implementer_session_hint=str(claude_hint.get("summary") or ""),
        open_findings=_section_text(snapshot, "Open Findings"),
        last_reviewed_scope=_section_text(snapshot, "Last Reviewed Scope"),
    )


def build_event_current_session(
    *,
    review_state: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
) -> ReviewCurrentSessionState:
    """Build typed current-session state from event-backed review state."""
    queue = _mapping(review_state.get("queue"))
    implementer_ack = event_claude_ack(queue)
    implementer_status = event_agent_status(review_state, "claude")
    return ReviewCurrentSessionState(
        current_instruction=event_current_instruction(review_state),
        current_instruction_revision=str(
            bridge_liveness.get("current_instruction_revision") or ""
        ),
        implementer_status=implementer_status,
        implementer_ack=implementer_ack,
        implementer_ack_revision=str(bridge_liveness.get("claude_ack_revision") or ""),
        implementer_ack_state=classify_implementer_ack_state(
            implementer_status=implementer_status,
            implementer_ack=implementer_ack,
            ack_current=bool(bridge_liveness.get("claude_ack_current")),
            stale_label="unknown",
            is_substantive_text=_is_substantive_text,
        ),
        implementer_session_state="",
        implementer_session_hint="",
        open_findings=event_open_findings(queue),
        last_reviewed_scope=str(
            _mapping(review_state.get("review")).get("plan_id") or ""
        ),
    )


def current_session_payload(
    state: ReviewCurrentSessionState,
) -> dict[str, object]:
    """Serialize typed current-session state for JSON projections."""
    return asdict(state)


def current_session_mapping(
    review_state: Mapping[str, object],
) -> Mapping[str, object]:
    """Return the projected current-session mapping when present."""
    return _mapping(review_state.get("current_session"))


def append_current_session_markdown(
    lines: list[str],
    current_session: object,
) -> None:
    """Render the typed current-session summary into latest.md output."""
    if not isinstance(current_session, dict):
        return
    lines.append("")
    lines.append("## Current Session")
    lines.append(
        "- instruction_revision: "
        f"{current_session.get('current_instruction_revision') or 'n/a'}"
    )
    lines.append(
        "- implementer_status: "
        f"{current_session.get('implementer_status') or 'n/a'}"
    )
    lines.append(
        "- implementer_ack_state: "
        f"{current_session.get('implementer_ack_state') or 'n/a'}"
    )
    if current_session.get("implementer_session_state"):
        lines.append(
            "- implementer_session_state: "
            f"{current_session.get('implementer_session_state') or 'n/a'}"
        )
    lines.append(
        "- last_reviewed_scope: "
        f"{current_session.get('last_reviewed_scope') or 'n/a'}"
    )


def current_focus_line(review_state: dict[str, object]) -> str:
    """Return the best current instruction from typed state or fallbacks."""
    current_session = review_state.get("current_session", {})
    if isinstance(current_session, dict):
        current_instruction = str(
            current_session.get("current_instruction") or ""
        ).strip()
        if current_instruction:
            return current_instruction
    bridge = review_state.get("bridge", {})
    if isinstance(bridge, dict):
        current_instruction = str(bridge.get("current_instruction") or "").strip()
        if current_instruction:
            return current_instruction
    queue = review_state.get("queue", {})
    if isinstance(queue, dict):
        derived_next_instruction = str(
            queue.get("derived_next_instruction") or ""
        ).strip()
        if derived_next_instruction:
            return derived_next_instruction
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return "(missing)"
    pending_packet = next(
        (
            packet
            for packet in packets
            if isinstance(packet, dict) and packet.get("status") == "pending"
        ),
        None,
    )
    if isinstance(pending_packet, dict):
        summary = str(pending_packet.get("summary") or "").strip()
        if summary:
            return summary
    latest_packet = packets[0] if packets else None
    if isinstance(latest_packet, dict):
        summary = str(latest_packet.get("summary") or "").strip()
        if summary:
            return summary
    return "(missing)"


def event_current_instruction(review_state: Mapping[str, object]) -> str:
    """Derive the event-backed current instruction from queue or packets."""
    queue = _mapping(review_state.get("queue"))
    derived = str(queue.get("derived_next_instruction") or "").strip()
    if derived:
        return derived
    packets = review_state.get("packets")
    if isinstance(packets, list):
        for packet in packets:
            if not isinstance(packet, dict) or packet.get("status") != "pending":
                continue
            summary = str(packet.get("summary") or "").strip()
            if summary:
                return summary
    return ""


def event_open_findings(queue: Mapping[str, object]) -> str:
    """Summarize pending event-backed findings for the current session."""
    pending_total = int(queue.get("pending_total") or 0)
    if pending_total <= 0:
        return "none"
    return f"{pending_total} pending review packet(s)"


def event_claude_ack(queue: Mapping[str, object]) -> str:
    """Derive the implementer ACK state from event-backed queue counts."""
    pending_claude = int(queue.get("pending_claude") or 0)
    return "pending" if pending_claude else "acknowledged"


def event_agent_status(
    review_state: Mapping[str, object],
    agent_id: str,
) -> str:
    """Read one agent status from typed registry rows before compatibility fallbacks."""
    registry = _mapping(review_state.get("registry"))
    registry_agents = registry.get("agents")
    compat = review_state.get("_compat")
    compat_agents = compat.get("agents") if isinstance(compat, dict) else None
    agents = registry_agents or compat_agents or review_state.get("agents")
    if not isinstance(agents, list):
        return ""
    for agent in agents:
        if not isinstance(agent, dict) or agent.get("agent_id") != agent_id:
            continue
        return str(
            agent.get("job_state")
            or agent.get("job_status")
            or agent.get("status")
            or ""
        )
    return ""


def _section_text(snapshot: BridgeSnapshot, section: str) -> str:
    raw = snapshot.sections.get(section, "")
    return clean_section(raw)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
