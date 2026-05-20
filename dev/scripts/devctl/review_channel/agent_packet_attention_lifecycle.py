"""Body lifecycle accounting for actor-scoped packet attention."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..runtime.value_coercion import coerce_text as _text
from .packet_loop_attention import (
    packet_absorption_required,
    packet_semantic_ingestion_required,
)


@dataclass(frozen=True, slots=True)
class BodyLifecycleStatus:
    packet_id: str
    unopened_packet_ids: tuple[str, ...]
    body_open_required: bool
    semantic_ingestion_required: bool
    absorption_required: bool
    absorption_reason: str


def body_lifecycle_status(
    *,
    body_open_packet: Mapping[str, object],
    body_open_packet_rows: tuple[Mapping[str, object], ...],
    actor: str,
    role: str,
    session: str,
) -> BodyLifecycleStatus:
    packet_id = _text(body_open_packet.get("packet_id"))
    semantic_required = bool(
        packet_id
        and packet_semantic_ingestion_required(
            body_open_packet,
            actor=actor,
            role=role,
            session=session,
        )
    )
    absorption_required = bool(
        packet_id
        and packet_absorption_required(
            body_open_packet,
            actor=actor,
            role=role,
            session=session,
        )
    )
    return BodyLifecycleStatus(
        packet_id=packet_id,
        unopened_packet_ids=unopened_body_packet_ids(
            body_open_packet_rows,
            actor=actor,
            role=role,
            session=session,
        ),
        body_open_required=bool(
            packet_id and not semantic_required and not absorption_required
        ),
        semantic_ingestion_required=semantic_required,
        absorption_required=absorption_required,
        absorption_reason=(
            "packet_semantically_ingested_without_absorption"
            if absorption_required
            else ""
        ),
    )


def unopened_body_packet_ids(
    packets: tuple[Mapping[str, object], ...],
    *,
    actor: str,
    role: str,
    session: str,
) -> tuple[str, ...]:
    return tuple(
        packet_id
        for packet in packets
        if (packet_id := _text(packet.get("packet_id")))
        and not packet_semantic_ingestion_required(
            packet,
            actor=actor,
            role=role,
            session=session,
        )
        and not packet_absorption_required(
            packet,
            actor=actor,
            role=role,
            session=session,
        )
    )
