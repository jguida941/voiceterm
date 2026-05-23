"""Packet attention reader for the typed develop controller."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ...runtime.peer_attention_window import _BLOCKING_KINDS
from ...runtime.master_plan_contract import PlanRow
from ...runtime.inbox_command_template import inbox_command_for_agent
from ...runtime.development_packet_failure_owner import class_owner_by_packet_failure
from ...runtime.current_plan_authority import resolve_current_plan_authority
from ...runtime.packet_carry_forward_sources import (
    durable_packet_ids_from_plan_rows,
)
from ...runtime.plan_packet_routing import packet_can_drive_current_plan
from ...runtime.review_packet_inbox import packet_inbox_from_review_state
from ...runtime.review_packet_inbox_liveness import is_live_pending
from .models import DevelopmentPacketAttention
from .packet_attention_body_followup import (
    PacketBodyFollowup,
    packet_body_followup_for_selection,
)
from .packet_attention_support import (
    PacketAttentionSummaryInput,
    PacketExitContext,
    durable_row_id_for_packet,
    expired_unresolved_packet_ids,
    latest_attention_packet_id,
    live_finding_packet_id,
    live_pending_packet_ids,
    packet_matches_fresh_route,
    packet_attention_satisfied_by_ingestion,
    packet_attention_summary,
    pending_actionable_packet_ids,
    required_command_for_record,
    wake_reason_for_packet,
)
from .packet_attention_lifecycle import packet_by_id, packet_rows

_ATTENTION_REQUIRED_STATUSES = {
    "wake_required",
    "review_needed",
    "blocked",
    "checkpoint_required",
}

# Lane-barrier coherence fix (Operator-asserted contradiction May 22, 2026):
# the typed work-board emits ``awaiting_reviewer_ack`` lane barriers from
# ``agent_sync.agents[actor].awaiting_packet_id`` /
# ``awaiting_from_agent`` (see
# ``review_channel/agent_work_board_barriers.py::build_lane_barriers``).
# Until this fix the develop-controller's attention reducer only consulted
# the actor's INBOUND ``packet_inbox`` record, so an actor blocked on an
# OUTBOUND ack (their own packet awaiting peer ack) saw the lane barrier
# in ``sync-status`` but ``attention_required=False`` in ``develop next``.
# Reading the awaiting fields here folds the lane-barrier signal into the
# typed attention reducer so the two surfaces cannot disagree at the same
# ``source_latest_event_id``.
_AWAITING_REVIEWER_ACK_WAKE_REASON = "awaiting_reviewer_ack"


def packet_attention_from_review_state(
    review_state: Mapping[str, object],
    *,
    rows: tuple[PlanRow, ...],
    agent: str = "codex",
    terminal_receipt_by_packet: Mapping[str, str] | None = None,
    durable_row_id_by_packet: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
) -> DevelopmentPacketAttention:
    """Return packet-driven wake state for a development controller actor."""
    terminal_receipts = terminal_receipt_by_packet or {}
    inbox = packet_inbox_from_review_state(review_state)
    record = inbox.for_agent(agent) if inbox is not None else None
    awaiting_barrier = _awaiting_reviewer_ack_barrier(review_state, agent=agent)
    if record is None:
        if awaiting_barrier is not None:
            return _awaiting_barrier_only_attention(
                agent=agent,
                barrier=awaiting_barrier,
            )
        return DevelopmentPacketAttention(agent=agent)
    exit_context = PacketExitContext(
        review_state=review_state,
        durable_packet_ids=frozenset(durable_packet_ids_from_plan_rows(rows)),
        class_owner_by_failure=class_owner_by_packet_failure(rows),
        terminal_receipt_by_packet=terminal_receipts,
    )
    expired_unresolved_ids = expired_unresolved_packet_ids(
        record.expired_unresolved_packet_ids,
        exit_context=exit_context,
    )
    packet_id = live_finding_packet_id(
        record,
        exit_context=exit_context,
    )
    delivery_packet_ids = live_pending_packet_ids(
        agent=agent,
        exit_context=exit_context,
    )
    current_plan_authority = resolve_current_plan_authority(
        rows,
        pending_packets=packet_rows(review_state.get("packets")),
    )
    status = record.attention_status
    wake_reason = record.wake_reason
    required_command = str(record.required_command or "").strip()
    if status == "none" and delivery_packet_ids:
        status = "wake_required"
        wake_reason = wake_reason_for_packet(
            review_state,
            packet_id=delivery_packet_ids[0],
        )
        required_command = inbox_command_for_agent(agent)
    pending_packet_ids = pending_actionable_packet_ids(
        record.pending_actionable_packet_ids,
        exit_context=exit_context,
        latest_finding_packet_id=packet_id,
        wake_reason=wake_reason,
        attention_required=True,
    )
    pending_packet_ids = tuple(
        packet_id
        for packet_id in pending_packet_ids
        if packet_matches_fresh_route(
            packet_by_id(review_state, packet_id),
            actor=agent,
            review_state=review_state,
        )
    )
    packet_id = _current_plan_attention_packet_id(
        packet_id,
        rows=rows,
        review_state=review_state,
        durable_row_id_by_packet=durable_row_id_by_packet,
        current_plan_authority=current_plan_authority,
    )
    pending_packet_ids = _current_plan_attention_packet_ids(
        pending_packet_ids,
        rows=rows,
        review_state=review_state,
        durable_row_id_by_packet=durable_row_id_by_packet,
        current_plan_authority=current_plan_authority,
    )
    delivery_packet_ids = _current_plan_attention_packet_ids(
        delivery_packet_ids,
        rows=rows,
        review_state=review_state,
        durable_row_id_by_packet=durable_row_id_by_packet,
        current_plan_authority=current_plan_authority,
    )
    latest_packet_id = latest_attention_packet_id(
        latest_finding_packet_id=packet_id,
        pending_actionable_packet_ids=pending_packet_ids,
        pending_delivery_packet_ids=delivery_packet_ids,
    )
    body_followup = packet_body_followup_for_selection(
        review_state,
        agent=agent,
        packet_id=latest_packet_id,
        exit_context=exit_context,
    )
    if body_followup.required and body_followup.packet_id:
        body_packet = packet_by_id(review_state, body_followup.packet_id)
        if not packet_matches_fresh_route(
            body_packet,
            actor=agent,
            review_state=review_state,
        ) or not _packet_id_can_drive_attention(
            body_followup.packet_id,
            rows=rows,
            review_state=review_state,
            durable_row_id_by_packet=durable_row_id_by_packet,
            current_plan_authority=current_plan_authority,
        ):
            body_followup = PacketBodyFollowup(body_followup.route)
    if body_followup.required and body_followup.packet_id:
        latest_packet_id = body_followup.packet_id
    attention_packet = packet_by_id(review_state, latest_packet_id)
    durable_row_id = durable_row_id_for_packet(
        rows,
        latest_packet_id,
        durable_row_id_by_packet=durable_row_id_by_packet,
        packet=attention_packet,
    )
    authority_affecting = _authority_affecting_packet(
        attention_packet,
        durable_row_id=durable_row_id,
        rows=rows,
    )
    packet_can_drive_attention = _packet_can_drive_attention(
        attention_packet,
        rows=rows,
        current_plan_authority=current_plan_authority,
        durable_row_id=durable_row_id,
        authority_affecting=authority_affecting,
    )
    attention_required = (
        bool(pending_packet_ids)
        or bool(delivery_packet_ids)
        or bool(expired_unresolved_ids)
        or (
            status in _ATTENTION_REQUIRED_STATUSES
            and not _packet_specific_attention_without_packet(
                status=status,
                wake_reason=wake_reason,
                latest_finding_packet_id=packet_id,
                pending_packet_ids=pending_packet_ids,
                pending_delivery_packet_ids=delivery_packet_ids,
                expired_unresolved_packet_ids=expired_unresolved_ids,
            )
            and not (
                wake_reason == "expired_unresolved_packet"
                and not expired_unresolved_ids
            )
            and not packet_attention_satisfied_by_ingestion(
                record,
                exit_context=exit_context,
            )
        )
        or body_followup.required
    )
    if attention_required and not packet_can_drive_attention:
        attention_required = False
        pending_packet_ids = ()
        delivery_packet_ids = ()
        expired_unresolved_ids = ()
        latest_packet_id = ""
        packet_id = ""
        durable_row_id = ""
        attention_packet = {}
    # Lane-barrier coherence: if the inbox path produced no attention but
    # ``agent_sync`` reports the actor is awaiting a reviewer ack on a
    # still-live packet, surface that as ``attention_required=True`` so
    # the typed controller cannot disagree with the work-board's typed
    # lane-barrier rows at the same source_latest_event_id.
    if (
        not attention_required
        and awaiting_barrier is not None
        and _awaiting_packet_live(review_state, awaiting_barrier.packet_id)
    ):
        attention_required = True
        latest_packet_id = awaiting_barrier.packet_id
        pending_packet_ids = (awaiting_barrier.packet_id,)
        status = "blocked"
        wake_reason = _AWAITING_REVIEWER_ACK_WAKE_REASON
        required_command = inbox_command_for_agent(awaiting_barrier.target_actor or agent)
        attention_packet = packet_by_id(review_state, awaiting_barrier.packet_id)
    if not attention_required:
        status = "none"
        wake_reason = ""
        required_command = ""
    elif body_followup.required and body_followup.command:
        status = "wake_required"
        wake_reason = body_followup.reason
        required_command = body_followup.command
    else:
        required_command = required_command_for_record(
            record,
            pending_packet_ids=pending_packet_ids,
            latest_finding_packet_id=packet_id,
            fallback_command=required_command,
            packet=attention_packet,
            route=body_followup.route,
        )
    required_command = _bind_packet_lifecycle_decision(
        required_command,
        repo_root=repo_root,
        review_state=review_state,
        agent=agent,
        route=body_followup.route,
        reason=wake_reason,
        packet_id=latest_packet_id,
    )
    return DevelopmentPacketAttention(
        attention_required=attention_required,
        agent=agent,
        attention_status=status,
        attention_reason=wake_reason,
        wake_reason=wake_reason,
        latest_attention_packet_id=latest_packet_id,
        latest_finding_packet_id=packet_id,
        pending_delivery_packet_ids=delivery_packet_ids,
        pending_actionable_packet_ids=pending_packet_ids,
        expired_unresolved_count=len(expired_unresolved_ids),
        required_command=required_command,
        durable_plan_row_id=durable_row_id,
        packet_kind=_packet_text(attention_packet, "kind"),
        requested_action=_packet_text(attention_packet, "requested_action"),
        authority_affecting=authority_affecting and packet_can_drive_attention,
        summary=(
            f"Packet attention requires semantic ingestion for {latest_packet_id}."
            if body_followup.required
            and body_followup.reason == "packet_semantic_ingestion_required"
            else f"Packet attention requires absorption for {latest_packet_id}."
            if body_followup.required
            and body_followup.reason == "packet_absorption_required"
            else packet_attention_summary(
                PacketAttentionSummaryInput(
                    record=record,
                    expired_unresolved_packet_ids=expired_unresolved_ids,
                    durable_row_id=durable_row_id,
                    latest_attention_packet_id=latest_packet_id,
                    latest_finding_packet_id=packet_id,
                    pending_delivery_packet_ids=delivery_packet_ids,
                    pending_actionable_packet_ids=pending_packet_ids,
                )
            )
        ),
    )


def _current_plan_attention_packet_id(
    packet_id: str,
    *,
    rows: tuple[PlanRow, ...],
    review_state: Mapping[str, object],
    durable_row_id_by_packet: Mapping[str, str] | None,
    current_plan_authority,
) -> str:
    packet_text = str(packet_id or "").strip()
    if not packet_text:
        return ""
    return (
        packet_text
        if _packet_id_can_drive_attention(
            packet_text,
            rows=rows,
            review_state=review_state,
            durable_row_id_by_packet=durable_row_id_by_packet,
            current_plan_authority=current_plan_authority,
        )
        else ""
    )


def _current_plan_attention_packet_ids(
    packet_ids: tuple[str, ...],
    *,
    rows: tuple[PlanRow, ...],
    review_state: Mapping[str, object],
    durable_row_id_by_packet: Mapping[str, str] | None,
    current_plan_authority,
) -> tuple[str, ...]:
    return tuple(
        packet_id
        for packet_id in packet_ids
        if _packet_id_can_drive_attention(
            packet_id,
            rows=rows,
            review_state=review_state,
            durable_row_id_by_packet=durable_row_id_by_packet,
            current_plan_authority=current_plan_authority,
        )
    )


def _packet_id_can_drive_attention(
    packet_id: str,
    *,
    rows: tuple[PlanRow, ...],
    review_state: Mapping[str, object],
    durable_row_id_by_packet: Mapping[str, str] | None,
    current_plan_authority,
) -> bool:
    packet = packet_by_id(review_state, packet_id)
    durable_row_id = durable_row_id_for_packet(
        rows,
        packet_id,
        durable_row_id_by_packet=durable_row_id_by_packet,
        packet=packet,
    )
    authority_affecting = _authority_affecting_packet(
        packet,
        durable_row_id=durable_row_id,
        rows=rows,
    )
    return _packet_can_drive_attention(
        packet,
        rows=rows,
        current_plan_authority=current_plan_authority,
        durable_row_id=durable_row_id,
        authority_affecting=authority_affecting,
    )


def _packet_can_drive_attention(
    packet: Mapping[str, object],
    *,
    rows: tuple[PlanRow, ...],
    current_plan_authority,
    durable_row_id: str,
    authority_affecting: bool,
) -> bool:
    if not current_plan_authority.has_executable_plan_row:
        return True
    packet_id = _packet_text(packet, "packet_id")
    if not packet_id:
        return True
    current_row_id = current_plan_authority.plan_row_id
    if durable_row_id and durable_row_id == current_row_id:
        return authority_affecting
    allowed, _routing = packet_can_drive_current_plan(
        packet,
        rows,
        current_authority=current_plan_authority,
        authority_affecting=authority_affecting,
    )
    return allowed


def _authority_affecting_packet(
    packet: Mapping[str, object],
    *,
    durable_row_id: str,
    rows: tuple[PlanRow, ...],
) -> bool:
    kind = _packet_text(packet, "kind")
    requested_action = _packet_text(packet, "requested_action")
    if kind in _BLOCKING_KINDS:
        return True
    if kind == "instruction" and requested_action != "review_only":
        return True
    return _active_plan_row_bound(rows, durable_row_id)


def _active_plan_row_bound(rows: tuple[PlanRow, ...], row_id: str) -> bool:
    normalized = str(row_id or "").strip()
    if not normalized:
        return False
    return any(
        row.row_id == normalized and row.status in {"in_progress", "queued"}
        for row in rows
    )


def _packet_text(packet: Mapping[str, object], field: str) -> str:
    return str(packet.get(field) or "").strip()


def _bind_packet_lifecycle_decision(
    command: str,
    *,
    repo_root: Path | None,
    review_state: Mapping[str, object],
    agent: str,
    route: object,
    reason: str,
    packet_id: str,
) -> str:
    if repo_root is None or not command or not packet_id:
        return command
    if "review-channel --action " not in command:
        return command
    lifecycle = _packet_lifecycle_action(reason)
    if not lifecycle:
        return command
    actor_role = str(getattr(route, "actor_role", "") or "").strip()
    session_id = str(getattr(route, "session_id", "") or "").strip()
    if not (actor_role and session_id):
        return command
    source_event_id = _review_state_source_latest_event_id(review_state)
    if not source_event_id:
        return command
    relpath = (
        Path("dev/reports/review_channel/control_decisions")
        / _slug(source_event_id)
        / (
            f"{_slug(agent)}-{_slug(actor_role)}-{_slug(session_id)}-"
            f"{_slug(packet_id)}-{lifecycle}.json"
        )
    )
    payload = _packet_lifecycle_decision_payload(
        actor=agent,
        role=actor_role,
        session_id=session_id,
        packet_id=packet_id,
        lifecycle=lifecycle,
        command=command,
        source_event_id=source_event_id,
    )
    _write_json_atomic(repo_root / relpath, payload)
    return _replace_control_decision_input(command, relpath.as_posix())


def _packet_lifecycle_action(reason: str) -> str:
    normalized = str(reason or "").strip()
    if normalized == "packet_body_open_required":
        return "body-open"
    if normalized == "packet_semantic_ingestion_required":
        return "ingest"
    if normalized == "packet_absorption_required":
        return "absorb"
    return ""


def _packet_lifecycle_decision_payload(
    *,
    actor: str,
    role: str,
    session_id: str,
    packet_id: str,
    lifecycle: str,
    command: str,
    source_event_id: str,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "contract_id": "AgentLoopDecision",
        "schema_version": 1,
        "actor_id": actor,
        "actor_role": role,
        "session_id": session_id,
        "decision": "run_next_command",
        "may_mutate": False,
        "can_run_next_command": False,
        "attention_packet_id": packet_id,
        "active_packet_id": packet_id,
        "next_command": command,
        "source_latest_event_id": source_event_id,
    }
    if lifecycle == "body-open":
        payload.update(
            {
                "required_action": "open_packet_body",
                "reason_code": "packet_body_open_required",
                "body_open_required": True,
                "body_open_packet_id": packet_id,
                "unopened_body_packet_ids": [packet_id],
            }
        )
    elif lifecycle == "ingest":
        payload.update(
            {
                "required_action": "ingest_packet_semantics",
                "reason_code": "packet_semantic_ingestion_required",
                "semantic_ingestion_required": True,
                "semantic_ingestion_packet_id": packet_id,
            }
        )
    else:
        payload.update(
            {
                "required_action": "absorb_packet",
                "reason_code": "packet_absorption_required",
                "absorption_required": True,
                "absorption_packet_id": packet_id,
            }
        )
    return payload


def _replace_control_decision_input(command: str, relpath: str) -> str:
    marker = " --control-decision-input "
    if marker in command:
        prefix, rest = command.split(marker, 1)
        if " " in rest:
            _old, suffix = rest.split(" ", 1)
            return f"{prefix}{marker}{relpath} {suffix}"
        return f"{prefix}{marker}{relpath}"
    terminal_marker = " --terminal none"
    if terminal_marker in command:
        return command.replace(
            terminal_marker,
            f"{marker}{relpath}{terminal_marker}",
            1,
        )
    return f"{command}{marker}{relpath}"


def _review_state_source_latest_event_id(review_state: Mapping[str, object]) -> str:
    for path in (
        ("agent_runtime_clock", "source_latest_event_id"),
        ("agent_sync", "source_latest_event_id"),
        ("reviewer_runtime", "agent_runtime_clock", "source_latest_event_id"),
        ("reviewer_runtime", "source_latest_event_id"),
        ("source_latest_event_id",),
    ):
        current: object = review_state
        for key in path:
            if not isinstance(current, Mapping):
                current = {}
                break
            current = current.get(key)
        text = str(current or "").strip()
        if text:
            return text
    return ""


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "_.-" else "-" for ch in value).strip("-")


def _write_json_atomic(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    try:
        tmp_path.write_text(
            json.dumps(dict(payload), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp_path, path)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass


def _packet_specific_attention_without_packet(
    *,
    status: str,
    wake_reason: str,
    latest_finding_packet_id: str,
    pending_packet_ids: tuple[str, ...],
    pending_delivery_packet_ids: tuple[str, ...],
    expired_unresolved_packet_ids: tuple[str, ...],
) -> bool:
    if (
        latest_finding_packet_id
        or pending_packet_ids
        or pending_delivery_packet_ids
        or expired_unresolved_packet_ids
    ):
        return False
    if status == "wake_required":
        return True
    return wake_reason in {"finding_pending", "expired_unresolved_packet"}


@dataclass(frozen=True, slots=True)
class _AwaitingReviewerAckBarrier:
    """Typed view of one ``awaiting_reviewer_ack`` lane-barrier row.

    Mirrors the shape produced by
    ``review_channel/agent_work_board_barriers.py::build_lane_barriers``
    so the develop-controller attention reducer can fold the same typed
    signal without importing the work-board projection module.
    """

    packet_id: str
    target_actor: str


def _awaiting_reviewer_ack_barrier(
    review_state: Mapping[str, object],
    *,
    agent: str,
) -> _AwaitingReviewerAckBarrier | None:
    """Return the awaiting-reviewer-ack barrier for ``agent``, or None.

    Reads ``agent_sync.agents[agent]`` mirroring the typed work-board
    barrier reducer. The returned barrier is the same row that
    ``sync-status`` renders as ``Lane Barriers (typed)`` so the two
    surfaces agree at the same source_latest_event_id.
    """
    agent_sync = review_state.get("agent_sync")
    if not isinstance(agent_sync, Mapping):
        return None
    agents = agent_sync.get("agents")
    if not isinstance(agents, Mapping):
        return None
    row = agents.get(agent)
    if not isinstance(row, Mapping):
        return None
    awaiting = str(row.get("awaiting_packet_id") or "").strip()
    if not awaiting:
        return None
    target_actor = str(row.get("awaiting_from_agent") or "").strip()
    return _AwaitingReviewerAckBarrier(
        packet_id=awaiting,
        target_actor=target_actor,
    )


def _awaiting_packet_live(
    review_state: Mapping[str, object],
    packet_id: str,
) -> bool:
    """Return True when the awaited packet is still a live pending packet.

    Guards against stale ``agent_sync`` rows whose ``awaiting_packet_id``
    out-paces the live packet inbox (e.g. the awaited packet was already
    acked / disposed). Without this check the attention reducer would
    surface forced attention indefinitely after the packet cleared.
    """
    if not packet_id:
        return False
    packets = review_state.get("packets")
    if not isinstance(packets, (list, tuple)):
        return False
    for packet in packets:
        if not isinstance(packet, Mapping):
            continue
        if str(packet.get("packet_id") or "").strip() != packet_id:
            continue
        return is_live_pending(packet)
    return False


def _awaiting_barrier_only_attention(
    *,
    agent: str,
    barrier: _AwaitingReviewerAckBarrier,
) -> DevelopmentPacketAttention:
    """Return a barrier-only attention shape when no inbox record exists.

    The typed packet inbox only synthesizes records for known agents
    (``codex``, ``claude``, ``cursor``, ``operator`` + any to_agent in
    pending packets). When the actor has no inbound packets, ``record``
    is None — but lane-barrier state still belongs in the attention
    reducer so ``operator`` / future provider lanes do not silently
    drop their typed blockers.
    """
    return DevelopmentPacketAttention(
        attention_required=True,
        agent=agent,
        attention_status="blocked",
        attention_reason=_AWAITING_REVIEWER_ACK_WAKE_REASON,
        wake_reason=_AWAITING_REVIEWER_ACK_WAKE_REASON,
        latest_attention_packet_id=barrier.packet_id,
        pending_actionable_packet_ids=(barrier.packet_id,),
        required_command=inbox_command_for_agent(barrier.target_actor or agent),
        summary=(
            f"{agent} lane awaiting {barrier.target_actor or 'partner'} "
            f"ack on {barrier.packet_id}."
        ),
    )


def review_state_payload(repo_root: Path) -> Mapping[str, object]:
    """Load the latest review-state projection as a typed-controller input."""
    path = repo_root / "dev/reports/review_channel/projections/latest/review_state.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


__all__ = ["packet_attention_from_review_state", "review_state_payload"]
