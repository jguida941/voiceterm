"""Wake-target resolution helpers for reviewer follow loops.

Extracted from follow_controller.py to keep both modules under the
code-shape soft limit. Contains the typed and legacy codex action-request
selection logic plus session-hint gating.
"""

from __future__ import annotations

from pathlib import Path

from .reviewer_follow_guard import (
    ReviewerWakePaths,
    as_path,
)

_WAITING_REVIEWER_SESSION_STATES = frozenset(
    {"interrupt_prompt", "waiting_for_user_input"}
)


def resolve_reviewer_wake_target(
    *,
    report: dict[str, object],
    operator_interaction_mode: str,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    """Select one pending codex action-request packet for wake, or None."""
    if operator_interaction_mode.strip() != "remote_control":
        return None, None

    # Typed coordination gate: refuse auto-wake when resync is required.
    coordination = report.get("coordination")
    if isinstance(coordination, dict) and coordination.get("resync_required"):
        return None, None

    bridge_liveness = report.get("bridge_liveness")
    if not isinstance(bridge_liveness, dict):
        return None, None

    # Session hint is kept as the final confirmation that Codex is waiting.
    if _codex_session_hint_state(bridge_liveness) not in _WAITING_REVIEWER_SESSION_STATES:
        return None, None

    # Prefer typed packet_inbox for packet selection when present.
    packet = _selected_codex_action_request_typed(report)
    if packet is None:
        packet = _selected_codex_action_request(report)
    if packet is None:
        return None, None
    if str(packet.get("delivery_observed_at_utc") or "").strip():
        return None, None
    return packet, None


def resolve_reviewer_wake_paths(
    paths: dict[str, object],
) -> ReviewerWakePaths | None:
    """Resolve the three runtime paths needed for a reviewer wake."""
    status_dir = as_path(paths.get("status_dir"))
    review_channel_path = as_path(paths.get("review_channel_path"))
    bridge_path = as_path(paths.get("bridge_path"))
    if status_dir is None or review_channel_path is None or bridge_path is None:
        return None
    return ReviewerWakePaths(
        status_dir=status_dir,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
    )


def _selected_codex_action_request_typed(
    report: dict[str, object],
) -> dict[str, object] | None:
    """Select a codex wake packet from typed packet_inbox when present."""
    packet_inbox = report.get("packet_inbox")
    if not isinstance(packet_inbox, dict):
        return None
    agents = packet_inbox.get("agents")
    if not isinstance(agents, (list, tuple)):
        return None
    codex_record = None
    for agent in agents:
        if not isinstance(agent, dict):
            continue
        if str(agent.get("agent") or "").strip() != "codex":
            continue
        codex_record = agent
        break
    if codex_record is None:
        return None
    if str(codex_record.get("attention_status") or "").strip() != "wake_required":
        return None
    target_packet_id = str(
        codex_record.get("current_instruction_packet_id") or ""
    ).strip()
    if not target_packet_id:
        return None
    packets = report.get("packets")
    if not isinstance(packets, list):
        return None
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if str(packet.get("packet_id") or "").strip() != target_packet_id:
            continue
        if str(packet.get("kind") or "").strip() != "action_request":
            return None
        return packet
    return None


def _selected_codex_action_request(
    report: dict[str, object],
) -> dict[str, object] | None:
    """Legacy codex action-request selection from report dicts."""
    packet_inbox = report.get("packet_inbox")
    packets = report.get("packets")
    if not isinstance(packet_inbox, dict) or not isinstance(packets, list):
        return None

    current_packet_id = ""
    for agent in packet_inbox.get("agents", ()):
        if not isinstance(agent, dict):
            continue
        if str(agent.get("agent") or "").strip() != "codex":
            continue
        if str(agent.get("attention_status") or "").strip() != "wake_required":
            return None
        current_packet_id = str(agent.get("current_instruction_packet_id") or "").strip()
        break
    if not current_packet_id:
        return None

    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if str(packet.get("packet_id") or "").strip() != current_packet_id:
            continue
        if str(packet.get("kind") or "").strip() != "action_request":
            return None
        return packet
    return None


def _codex_session_hint_state(bridge_liveness: dict[str, object]) -> str:
    hints = bridge_liveness.get("session_state_hints")
    if not isinstance(hints, dict):
        return ""
    codex = hints.get("codex")
    if not isinstance(codex, dict):
        return ""
    return str(codex.get("state") or "").strip()
