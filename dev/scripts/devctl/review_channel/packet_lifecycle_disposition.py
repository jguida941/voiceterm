"""Packet lifecycle disposition reducer."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from .packet_lifecycle_binding import (
    has_creation_binding,
    plan_ingestion_payload,
    plan_integration_recorded,
)

PACKET_DISPOSITION_CONTRACT_ID = "PacketDisposition"


@dataclass(frozen=True, slots=True)
class PacketDisposition:
    """Typed disposition sink for a review packet."""

    sink: str
    status: str
    resolution_anchor: str
    reason: str
    schema_version: int = 1
    contract_id: str = PACKET_DISPOSITION_CONTRACT_ID
    plan_target: str = ""
    next_slice_target: str = ""
    archive_classification: str = ""


def acted_on_disposition(
    packet: Mapping[str, object],
    action_event: Mapping[str, object],
) -> dict[str, object]:
    action = _text(action_event.get("action"))
    target_anchor = _text(action_event.get("target_anchor"))

    if action == "failed":
        return asdict(
            PacketDisposition(
                sink="recovery_required",
                status="failed",
                resolution_anchor=target_anchor or f"packet:{_text(packet.get('packet_id'))}",
                reason=(
                    _text(action_event.get("reason"))
                    or "Action-request execution failed before resolution."
                ),
                next_slice_target="fresh_action_request",
            )
        )

    if action == "apply_pending_after_execution":
        return asdict(
            PacketDisposition(
                sink="recovery_required",
                status="apply_pending_after_execution",
                resolution_anchor=target_anchor or f"packet:{_text(packet.get('packet_id'))}",
                reason=(
                    _text(action_event.get("reason"))
                    or "Commit execution completed but packet apply remains pending."
                ),
                next_slice_target="fresh_action_request_or_explicit_recovery",
            )
        )

    if action == "applied" and _text(packet.get("target_kind")) == "plan":
        return _plan_disposition(
            packet,
            target_anchor=target_anchor,
        )
    if action == "applied":
        return archive_disposition(
            status="applied",
            classification="applied_to_target",
            reason="Packet was acted on and resolved against its target.",
            anchor=target_anchor,
        )
    if action == "dismissed":
        return archive_disposition(
            status="dismissed",
            classification="dismissed_with_actor",
            reason="Packet was explicitly dismissed by the addressed actor.",
            anchor=target_anchor,
        )
    if action == "archived" and has_creation_binding(packet):
        return archive_disposition(
            status="archived",
            classification="expired_after_durable_binding",
            reason="Packet expired after typed creation binding recorded durable ownership.",
            anchor=target_anchor,
        )
    return archive_disposition(
        status="archived",
        classification="clock_expired_without_disposition",
        reason="Packet entered archive because an expiry event was recorded.",
        anchor=target_anchor,
    )


def archive_disposition(
    *,
    status: str,
    classification: str,
    reason: str,
    anchor: str = "",
) -> dict[str, object]:
    resolution_anchor = anchor or f"archive_classification:{classification}"
    return asdict(
        PacketDisposition(
            sink="archived",
            status=status,
            resolution_anchor=resolution_anchor,
            archive_classification=classification,
            reason=reason,
        )
    )


def _plan_disposition(
    packet: Mapping[str, object],
    *,
    target_anchor: str,
) -> dict[str, object]:
    plan_integration = plan_ingestion_payload(packet)
    integration_status = _text(plan_integration.get("status"))
    integration_reason = _text(plan_integration.get("reason"))
    if not plan_integration_recorded(plan_integration):
        return asdict(
            PacketDisposition(
                sink="recovery_required",
                status="plan_ingestion_failed",
                resolution_anchor=target_anchor or f"packet:{_text(packet.get('packet_id'))}",
                plan_target=target_anchor,
                reason=(
                    integration_reason
                    or "Applied plan packet lacks durable typed plan ingestion evidence."
                ),
                next_slice_target="packet_plan_ingestion_repair",
                archive_classification=integration_status,
            )
        )
    return asdict(
        PacketDisposition(
            sink="plan_integrated",
            status="applied",
            resolution_anchor=target_anchor,
            plan_target=target_anchor,
            reason="Applied packet targeted a canonical plan artifact.",
        )
    )


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "PACKET_DISPOSITION_CONTRACT_ID",
    "PacketDisposition",
    "acted_on_disposition",
    "archive_disposition",
]
