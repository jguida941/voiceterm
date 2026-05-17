"""Focused helpers for event-backed review-state reduction."""

from __future__ import annotations

from ..runtime.role_profile import role_for_provider
from .event_models import ReviewAgentRow, ReviewPacketRow

_ROLE_JOB_STATE: dict[str, str] = {
    "reviewer": "reviewing",
    "implementer": "implementing",
    "operator": "waiting",
}


def record_provider_packet_state(
    provider_state: dict[str, dict[str, object]],
    event: dict[str, object],
    packet_id: str,
) -> None:
    provider_from = str(event.get("from_agent") or "").strip()
    provider_to = str(event.get("to_agent") or "").strip()
    if is_runtime_provider(provider_from):
        provider_state.setdefault(provider_from, {})
    if is_runtime_provider(provider_to):
        provider_state.setdefault(provider_to, {})
    if provider_from in provider_state:
        provider_state[provider_from]["last_packet_seen"] = packet_id
    if provider_to in provider_state:
        provider_state[provider_to]["last_packet_seen"] = packet_id
    if str(event.get("event_type") or "").strip() == "packet_applied":
        actor = str((event.get("metadata") or {}).get("actor") or "").strip()
        if actor in provider_state:
            provider_state[actor]["last_packet_applied"] = packet_id


def hydrate_provider_job_state(
    provider_state: dict[str, dict[str, object]],
    pending_counts: dict[str, int],
) -> None:
    for provider in provider_state:
        role = role_for_provider(provider)
        active_label = _ROLE_JOB_STATE.get(role.value, "waiting")
        provider_state[provider].setdefault(
            "job_state",
            active_label if pending_counts.get(provider, 0) else "assigned",
        )
    for provider, count in pending_counts.items():
        if count and provider in provider_state:
            provider_state[provider]["waiting_on"] = provider


def build_agent_rows(
    *,
    packets: list[dict[str, object]],
    latest_timestamp: str,
    providers: tuple[str, ...],
) -> list[ReviewAgentRow]:
    pending_targets = {
        str(packet.get("to_agent") or "").strip()
        for packet in packets
        if packet.get("status") == "pending"
    }
    latest_packet_by_target = {
        agent_id: next(
            (
                packet
                for packet in packets
                if packet.get("to_agent") == agent_id
                or packet.get("from_agent") == agent_id
            ),
            None,
        )
        for agent_id in providers
    }
    return [
        _agent_row(
            agent_id=agent_id,
            display_name=agent_id.title(),
            role=str(role_for_provider(agent_id)),
            pending=bool(agent_id in pending_targets),
            latest_packet=latest_packet_by_target[agent_id],
            latest_timestamp=latest_timestamp,
        )
        for agent_id in providers
    ]


def initial_provider_state(lanes: list | None) -> dict[str, dict[str, object]]:
    providers = {str(lane.provider) for lane in (lanes or []) if getattr(lane, "provider", "")}
    providers.update({"codex", "claude", "operator"})
    return {provider: {} for provider in sorted(providers)}


def legacy_agent_ids(
    lanes: list | None,
    packets: list[dict[str, object]],
) -> tuple[str, ...]:
    ordered: list[str] = []
    for lane in lanes or []:
        provider = str(getattr(lane, "provider", "")).strip()
        if provider and provider not in ordered:
            ordered.append(provider)
    for packet in packets:
        for field in ("from_agent", "to_agent"):
            provider = str(packet.get(field) or "").strip()
            if is_runtime_provider(provider) and provider not in ordered:
                ordered.append(provider)
    for provider in ("codex", "claude", "operator"):
        if provider not in ordered:
            ordered.append(provider)
    return tuple(ordered)


def is_runtime_provider(provider: str) -> bool:
    return provider in {"codex", "claude", "cursor", "operator", "human"}


def _agent_capabilities(agent_id: str) -> list[str]:
    if agent_id == "codex":
        return ["review", "planning", "coordination"]
    if agent_id == "operator":
        return ["approval", "dispatch", "triage"]
    return ["implementation", "fixes", "handoff"]


def _agent_row(
    *,
    agent_id: str,
    display_name: str,
    role: str,
    pending: bool,
    latest_packet: ReviewPacketRow | dict[str, object] | None,
    latest_timestamp: str,
) -> ReviewAgentRow:
    role_label = str(role_for_provider(agent_id))
    active_label = _ROLE_JOB_STATE.get(role_label, "waiting")
    if pending:
        job_status = active_label
    elif latest_packet is not None:
        job_status = "done"
    else:
        job_status = "waiting"
    return ReviewAgentRow(
        agent_id=agent_id,
        display_name=display_name,
        role=role,
        status="active" if pending else "idle",
        capabilities=_agent_capabilities(agent_id),
        lane=agent_id,
        last_seen_utc=latest_timestamp if latest_packet is not None else None,
        assigned_job=latest_packet.get("summary") if latest_packet else None,
        job_status=job_status,
        waiting_on=(
            latest_packet.get("from_agent")
            if latest_packet is not None and latest_packet.get("to_agent") == agent_id
            else None
        ),
        last_packet_id_seen=latest_packet.get("packet_id") if latest_packet else None,
        last_packet_id_applied=(
            latest_packet.get("packet_id")
            if latest_packet is not None and latest_packet.get("status") == "applied"
            else None
        ),
        script_profile="review-channel-event",
    )
