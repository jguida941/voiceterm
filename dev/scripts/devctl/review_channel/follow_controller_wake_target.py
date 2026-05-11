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
    """Select one pending codex attention packet for dispatch, or None."""
    if not _reviewer_wake_allowed(
        report=report,
        operator_interaction_mode=operator_interaction_mode,
    ):
        return None, None

    bridge_liveness = report.get("bridge_liveness")
    if not isinstance(bridge_liveness, dict):
        return None, None

    # Prefer the typed loop decision when sync-status provides it. It already
    # combines packet focus, actor/session routing, lifecycle, and blocker
    # policy, so the follow loop does not have to rediscover that state from
    # packet prose.
    packet = _selected_codex_wake_packet_from_agent_loop_decision(report)
    if packet is None:
        packet = _selected_codex_wake_packet_typed(report)
    if packet is None:
        packet = _selected_codex_wake_packet(report)
    if packet is None:
        return None, None
    if _waiting_session_hint_required(report=report, packet=packet):
        if _codex_session_hint_state(bridge_liveness) not in _WAITING_REVIEWER_SESSION_STATES:
            return None, None
    if _coordination_blocks_packet_wake(report=report, packet=packet):
        return None, None
    if str(packet.get("delivery_observed_at_utc") or "").strip():
        return None, None
    return packet, None


def _selected_codex_wake_packet_from_agent_loop_decision(
    report: dict[str, object],
) -> dict[str, object] | None:
    decisions = report.get("agent_loop_decisions")
    packets = report.get("packets")
    if not isinstance(decisions, list) or not isinstance(packets, list):
        return None
    packets_by_id = {
        str(packet.get("packet_id") or "").strip(): packet
        for packet in packets
        if isinstance(packet, dict)
    }
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        if str(decision.get("actor_id") or "").strip() != "codex":
            continue
        if str(decision.get("actor_role") or "").strip() != "reviewer":
            continue
        if not _agent_loop_decision_wants_reviewer_wake(decision):
            continue
        packet_id = _agent_loop_decision_packet_id(decision)
        if not packet_id:
            continue
        packet = packets_by_id.get(packet_id)
        if not isinstance(packet, dict):
            continue
        if str(packet.get("to_agent") or "").strip() != "codex":
            continue
        if str(packet.get("status") or "").strip() != "pending":
            continue
        return packet
    return None


def _agent_loop_decision_wants_reviewer_wake(
    decision: dict[str, object],
) -> bool:
    loop_mode = str(decision.get("loop_mode") or "").strip()
    if loop_mode not in {
        "continue_to_goal",
        "pivot_to_packet",
        "continue_current_execution",
        "recover_or_relaunch",
    }:
        return False
    if bool(decision.get("wake_required")) or bool(decision.get("pivot_required")):
        return True
    return bool(_agent_loop_decision_packet_id(decision))


def _agent_loop_decision_packet_id(decision: dict[str, object]) -> str:
    for key in ("attention_packet_id", "active_packet_id", "executing_packet_id"):
        value = str(decision.get(key) or "").strip()
        if value:
            return value
    return ""


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


def _selected_codex_wake_packet_typed(
    report: dict[str, object],
) -> dict[str, object] | None:
    """Select a codex attention packet from typed packet_inbox when present."""
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
    attention_status = str(codex_record.get("attention_status") or "").strip()
    wake_reason = str(codex_record.get("wake_reason") or "").strip()
    target_packet_id = ""
    expected_kind = ""
    if attention_status == "wake_required":
        target_packet_id = str(
            codex_record.get("current_instruction_packet_id") or ""
        ).strip()
        expected_kind = "action_request"
    elif attention_status == "review_needed" and wake_reason == "finding_pending":
        target_packet_id = str(
            codex_record.get("latest_finding_packet_id") or ""
        ).strip()
        expected_kind = "finding"
    else:
        return None
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
        if str(packet.get("kind") or "").strip() != expected_kind:
            return None
        return packet
    return None


def _selected_codex_wake_packet(
    report: dict[str, object],
) -> dict[str, object] | None:
    """Legacy codex wake-packet selection from report dicts."""
    packet_inbox = report.get("packet_inbox")
    packets = report.get("packets")
    if not isinstance(packet_inbox, dict) or not isinstance(packets, list):
        return None

    current_packet_id = ""
    expected_kind = ""
    for agent in packet_inbox.get("agents", ()):
        if not isinstance(agent, dict):
            continue
        if str(agent.get("agent") or "").strip() != "codex":
            continue
        attention_status = str(agent.get("attention_status") or "").strip()
        wake_reason = str(agent.get("wake_reason") or "").strip()
        if attention_status == "wake_required":
            current_packet_id = str(
                agent.get("current_instruction_packet_id") or ""
            ).strip()
            expected_kind = "action_request"
        elif attention_status == "review_needed" and wake_reason == "finding_pending":
            current_packet_id = str(agent.get("latest_finding_packet_id") or "").strip()
            expected_kind = "finding"
        else:
            return None
        break
    if not current_packet_id:
        return None

    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if str(packet.get("packet_id") or "").strip() != current_packet_id:
            continue
        if str(packet.get("kind") or "").strip() != expected_kind:
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


def _reviewer_wake_allowed(
    *,
    report: dict[str, object],
    operator_interaction_mode: str,
) -> bool:
    mode = operator_interaction_mode.strip()
    if mode == "remote_control":
        return True
    authority_snapshot = report.get("authority_snapshot")
    if not isinstance(authority_snapshot, dict):
        return False
    return _typed_collaboration_wake_allowed(authority_snapshot)


def _typed_collaboration_wake_allowed(
    authority_snapshot: dict[str, object],
) -> bool:
    verification_owner = str(authority_snapshot.get("verification_owner") or "").strip()
    verification_status = str(
        authority_snapshot.get("verification_status") or ""
    ).strip()
    mutation_owner = str(authority_snapshot.get("mutation_owner") or "").strip()
    watcher_owner = str(authority_snapshot.get("watcher_owner") or "").strip()
    watcher_status = str(authority_snapshot.get("watcher_status") or "").strip()
    if verification_owner != "codex":
        return False
    if verification_status and verification_status not in {
        "active",
        "configured",
        "declared",
        "live",
    }:
        return False
    if watcher_owner == "claude" and watcher_status == "live":
        return True
    return mutation_owner == "claude"


def _coordination_blocks_packet_wake(
    *,
    report: dict[str, object],
    packet: dict[str, object],
) -> bool:
    coordination = report.get("coordination")
    if not isinstance(coordination, dict):
        return False
    if not coordination.get("resync_required"):
        return False
    return str(packet.get("kind") or "").strip() == "action_request"


def _waiting_session_hint_required(
    *,
    report: dict[str, object],
    packet: dict[str, object],
) -> bool:
    if str(packet.get("kind") or "").strip() != "finding":
        return True
    authority_snapshot = report.get("authority_snapshot")
    if not isinstance(authority_snapshot, dict):
        return True
    return not _typed_collaboration_wake_allowed(authority_snapshot)
