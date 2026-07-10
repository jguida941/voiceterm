"""Packet-row helpers used by the review-channel event reducer."""

from __future__ import annotations

from collections.abc import Mapping

from .context_refs import normalize_context_pack_refs
from .event_models import ReviewPacketRow
from .packet_creation_binding import PACKET_CREATION_BINDING_EVENT_TYPES
from .packet_body_observation import (
    PACKET_BODY_OBSERVATION_EVENT_TYPES,
    packet_body_observation_payload_for_packet,
)
from .packet_semantic_ingestion import (
    PACKET_SEMANTIC_INGESTION_EVENT_TYPES,
    packet_semantic_ingestion_payload_for_packet,
)
from .packet_debt_remediation_contracts import PACKET_DURABLE_INGESTION_EVENT_TYPES
from .packet_lifecycle import apply_lifecycle_transition, project_packet_lifecycle
from .packet_source_identity import source_identity
from .pending_packets import partition_live_pending_packets

PACKET_WAKE_EVENT_TYPES = {"packet_wake_attempted"}


def summarize_packets(
    packets_by_id: dict[str, ReviewPacketRow],
) -> tuple[list[dict[str, object]], dict[str, int], int]:
    packet_rows: list[dict[str, object]] = []
    pending_counts = {"codex": 0, "claude": 0, "cursor": 0, "operator": 0}
    ordered_packets = [
        dict(packet)
        for packet in sorted(
            packets_by_id.values(),
            key=lambda item: str(item.get("_sort_timestamp") or ""),
            reverse=True,
        )
    ]
    live_packets, stale_packets = partition_live_pending_packets(ordered_packets)
    live_packet_ids = {
        str(packet.get("packet_id") or "").strip()
        for packet in live_packets
        if isinstance(packet, dict)
    }
    stale_packet_ids = {
        str(packet.get("packet_id") or "").strip()
        for packet in stale_packets
        if isinstance(packet, dict)
    }
    for packet in ordered_packets:
        stale_pending = str(packet.get("packet_id") or "").strip() in stale_packet_ids
        if str(packet.get("packet_id") or "").strip() in live_packet_ids:
            target = str(packet.get("to_agent") or "").strip()
            if target in pending_counts:
                pending_counts[target] += 1
        clean_packet = project_packet_lifecycle(packet, stale_pending=stale_pending)
        clean_packet.pop("_sort_timestamp", None)
        packet_rows.append(clean_packet)
    return packet_rows, pending_counts, len(stale_packets)


def packet_from_event(event: dict[str, object]) -> ReviewPacketRow:
    is_action_request = str(event.get("kind") or "").strip() == "action_request"
    return project_packet_lifecycle(ReviewPacketRow(
        packet_id=event.get("packet_id"),
        trace_id=event.get("trace_id"),
        plan_id=event.get("plan_id"),
        latest_event_id=event.get("event_id"),
        correlation_id=event.get("correlation_id"),
        causation_id=event.get("causation_id"),
        run_id=event.get("run_id"),
        from_agent=event.get("from_agent"),
        to_agent=event.get("to_agent"),
        kind=event.get("kind"),
        summary=event.get("summary"),
        body=event.get("body"),
        evidence_refs=list(event.get("evidence_refs") or []),
        guidance_refs=list(event.get("guidance_refs") or []),
        context_pack_refs=normalize_context_pack_refs(
            event.get("context_pack_refs")
        ),
        confidence=float(event.get("confidence") or 0.0),
        requested_action=event.get("requested_action"),
        policy_hint=event.get("policy_hint"),
        approval_required=bool(event.get("approval_required")),
        attention_urgency=event.get("attention_urgency"),
        attention_class=event.get("attention_class"),
        target_kind=event.get("target_kind"),
        target_ref=event.get("target_ref"),
        target_revision=event.get("target_revision"),
        anchor_refs=list(event.get("anchor_refs") or []),
        intake_ref=event.get("intake_ref"),
        mutation_op=event.get("mutation_op"),
        target_role=event.get("target_role"),
        target_session_id=event.get("target_session_id"),
        anchor_scope=event.get("anchor_scope"),
        requested_session_visibility=event.get("requested_session_visibility"),
        pipeline_generation=event.get("pipeline_generation"),
        staged_snapshot_hash=event.get("staged_snapshot_hash"),
        guard_results_summary=event.get("guard_results_summary"),
        full_guard_bundle_evidence=event.get("full_guard_bundle_evidence"),
        plan_proposal=event.get("plan_proposal"),
        packet_creation_binding={},
        packet_durable_ingestion_receipt={},
        durable_binding={},
        plan_ingestion={},
        plan_integration={},
        semantic_zref=_semantic_zref(event),
        source_identity=source_identity(event),
        metadata=_metadata(event),
        status=event.get("status"),
        posted_at=event.get("timestamp_utc"),
        acked_by=None,
        acked_at_utc=None,
        applied_at_utc=None,
        delivery_emitted_at_utc=event.get("timestamp_utc") if is_action_request else None,
        delivery_observed_at_utc="",
        delivery_observed_by="",
        body_observed_at_utc="",
        body_observed_by="",
        body_observed_role="",
        body_observed_session_id="",
        body_observed_event_id="",
        body_digest="",
        body_observation_events=[],
        semantic_ingested_at_utc="",
        semantic_ingested_by="",
        semantic_ingested_role="",
        semantic_ingested_session_id="",
        semantic_ingested_event_id="",
        packet_semantic_ingestion_receipt={},
        semantic_ingestion_events=[],
        execution_started_at_utc="",
        execution_started_by="",
        execution_failed_at_utc="",
        execution_failed_by="",
        execution_failed_reason="",
        apply_pending_after_execution_at_utc="",
        apply_pending_after_execution_by="",
        apply_pending_after_execution_reason="",
        reviewer_wake={},
        expires_at_utc=event.get("expires_at_utc"),
        _sort_timestamp=event.get("timestamp_utc"),
    ))


def apply_packet_transition(
    packet: dict[str, object],
    event: dict[str, object],
) -> dict[str, object]:
    next_packet = dict(packet)
    event_type = str(event.get("event_type") or "").strip()
    next_packet["latest_event_id"] = event.get("event_id")
    next_packet["_sort_timestamp"] = event.get("timestamp_utc")
    if event_type in {
        "packet_plan_ingestion_recorded",
        "packet_plan_ingestion_failed",
        "packet_plan_integration_recorded",
        "packet_plan_integration_failed",
    }:
        plan_payload = _plan_integration_payload(event)
        next_packet["plan_ingestion"] = plan_payload
        next_packet["plan_integration"] = plan_payload
        return project_packet_lifecycle(next_packet)
    if event_type in PACKET_CREATION_BINDING_EVENT_TYPES:
        binding_payload = _packet_creation_binding_payload(event)
        next_packet["packet_creation_binding"] = binding_payload
        next_packet["durable_binding"] = binding_payload
        return project_packet_lifecycle(next_packet)
    if event_type in PACKET_DURABLE_INGESTION_EVENT_TYPES:
        receipt = _packet_durable_ingestion_payload(event)
        next_packet["packet_durable_ingestion_receipt"] = receipt
        next_packet["durable_binding"] = receipt
        return project_packet_lifecycle(next_packet)
    if event_type in PACKET_WAKE_EVENT_TYPES:
        next_packet["reviewer_wake"] = _packet_wake_payload(event)
        return project_packet_lifecycle(next_packet)
    if event_type in PACKET_BODY_OBSERVATION_EVENT_TYPES:
        return _apply_packet_body_observation(next_packet, event)
    if event_type in PACKET_SEMANTIC_INGESTION_EVENT_TYPES:
        return _apply_packet_semantic_ingestion(next_packet, event)
    next_packet["status"] = event.get("status") or action_request_lifecycle_status(
        event_type
    )
    if event.get("guidance_refs") is not None or packet.get("guidance_refs"):
        next_packet["guidance_refs"] = list(
            event.get("guidance_refs") or packet.get("guidance_refs") or []
        )
    if event.get("context_pack_refs") is not None or packet.get("context_pack_refs"):
        next_packet["context_pack_refs"] = normalize_context_pack_refs(
            event.get("context_pack_refs") or packet.get("context_pack_refs")
        )
    if event.get("pipeline_generation") is not None or packet.get("pipeline_generation"):
        next_packet["pipeline_generation"] = (
            event.get("pipeline_generation") or packet.get("pipeline_generation")
        )
    if event.get("staged_snapshot_hash") is not None or packet.get("staged_snapshot_hash"):
        next_packet["staged_snapshot_hash"] = (
            event.get("staged_snapshot_hash")
            or packet.get("staged_snapshot_hash")
        )
    if event.get("guard_results_summary") is not None or packet.get("guard_results_summary"):
        next_packet["guard_results_summary"] = (
            event.get("guard_results_summary")
            or packet.get("guard_results_summary")
        )
    if (
        event.get("full_guard_bundle_evidence") is not None
        or packet.get("full_guard_bundle_evidence")
    ):
        next_packet["full_guard_bundle_evidence"] = (
            event.get("full_guard_bundle_evidence")
            or packet.get("full_guard_bundle_evidence")
        )
    if event.get("plan_proposal") is not None or packet.get("plan_proposal"):
        next_packet["plan_proposal"] = event.get("plan_proposal") or packet.get(
            "plan_proposal"
        )
    for lineage_field in ("correlation_id", "causation_id", "run_id"):
        if event.get(lineage_field) is not None or packet.get(lineage_field):
            next_packet[lineage_field] = event.get(lineage_field) or packet.get(
                lineage_field
            )
    if event.get("semantic_zref") is not None or packet.get("semantic_zref"):
        next_packet["semantic_zref"] = (
            event.get("semantic_zref") or packet.get("semantic_zref")
        )
    else:
        next_packet["semantic_zref"] = _semantic_zref(next_packet)
    if event.get("source_identity") is not None or packet.get("source_identity"):
        next_packet["source_identity"] = (
            source_identity(event) or source_identity(packet)
        )
    actor = str((event.get("metadata") or {}).get("actor") or "").strip()
    if event_type == "packet_acked":
        next_packet["acked_by"] = actor or packet.get("to_agent")
        next_packet["acked_at_utc"] = event.get("timestamp_utc")
    if event_type == "packet_applied":
        next_packet["applied_at_utc"] = event.get("timestamp_utc")
    if str(packet.get("kind") or "").strip() == "action_request":
        if not str(next_packet.get("delivery_emitted_at_utc") or "").strip():
            next_packet["delivery_emitted_at_utc"] = (
                packet.get("delivery_emitted_at_utc")
                or packet.get("posted_at")
            )
        if event_type == "packet_acked":
            next_packet["execution_started_at_utc"] = event.get("timestamp_utc")
            next_packet["execution_started_by"] = actor or packet.get("to_agent")
        if event_type == "action_request_execution_failed":
            next_packet["execution_failed_at_utc"] = event.get("timestamp_utc")
            next_packet["execution_failed_by"] = actor or packet.get("to_agent")
            next_packet["execution_failed_reason"] = _event_reason(event)
        if event_type == "action_request_apply_pending_after_execution":
            next_packet["apply_pending_after_execution_at_utc"] = event.get(
                "timestamp_utc"
            )
            next_packet["apply_pending_after_execution_by"] = (
                actor or packet.get("to_agent")
            )
            next_packet["apply_pending_after_execution_reason"] = _event_reason(event)
        if (
            event_type == "packet_applied"
            and not str(next_packet.get("execution_started_at_utc") or "").strip()
        ):
            next_packet["execution_started_at_utc"] = event.get("timestamp_utc")
            next_packet["execution_started_by"] = actor or packet.get("to_agent")
    return apply_lifecycle_transition(next_packet, event)


def _apply_packet_body_observation(
    packet: dict[str, object],
    event: dict[str, object],
) -> dict[str, object]:
    payload = packet_body_observation_payload_for_packet(event, packet)
    observed_by = str(payload.get("body_observed_by") or "").strip()
    observed_at = str(payload.get("body_observed_at_utc") or "").strip()
    digest = str(payload.get("body_digest") or "").strip()
    event_id = str(payload.get("event_id") or "").strip()
    events = list(packet.get("body_observation_events") or [])
    if not any(
        isinstance(row, dict)
        and str(row.get("event_id") or "").strip() == event_id
        and event_id
        for row in events
    ):
        events.append(payload)
    packet["body_observation_events"] = events
    if observed_by:
        packet["body_observed_by"] = observed_by
    observed_role = str(payload.get("body_observed_role") or "").strip()
    observed_session = str(payload.get("body_observed_session_id") or "").strip()
    if observed_role:
        packet["body_observed_role"] = observed_role
    if observed_session:
        packet["body_observed_session_id"] = observed_session
    if observed_at:
        packet["body_observed_at_utc"] = observed_at
    if event_id:
        packet["body_observed_event_id"] = event_id
    if digest:
        packet["body_digest"] = digest
    return project_packet_lifecycle(packet)


def _apply_packet_semantic_ingestion(
    packet: dict[str, object],
    event: dict[str, object],
) -> dict[str, object]:
    payload = packet_semantic_ingestion_payload_for_packet(event, packet)
    ingested_by = str(payload.get("ingested_by_actor") or "").strip()
    ingested_at = str(payload.get("ingested_at_utc") or "").strip()
    event_id = str(payload.get("event_id") or event.get("event_id") or "").strip()
    events = list(packet.get("semantic_ingestion_events") or [])
    if not any(
        isinstance(row, dict)
        and str(row.get("event_id") or "").strip() == event_id
        and event_id
        for row in events
    ):
        events.append(payload)
    packet["semantic_ingestion_events"] = events
    packet["packet_semantic_ingestion_receipt"] = payload
    if ingested_by:
        packet["semantic_ingested_by"] = ingested_by
    ingested_role = str(payload.get("ingested_by_role") or "").strip()
    ingested_session = str(payload.get("ingested_by_session_id") or "").strip()
    if ingested_role:
        packet["semantic_ingested_role"] = ingested_role
    if ingested_session:
        packet["semantic_ingested_session_id"] = ingested_session
    if ingested_at:
        packet["semantic_ingested_at_utc"] = ingested_at
    if event_id:
        packet["semantic_ingested_event_id"] = event_id
    body_digest = str(payload.get("body_sha256") or "").strip()
    if body_digest:
        packet["body_digest"] = body_digest
    return project_packet_lifecycle(packet)


def _plan_integration_payload(event: Mapping[str, object]) -> dict[str, object]:
    payload = event.get("plan_ingestion")
    if not isinstance(payload, Mapping):
        payload = event.get("plan_integration")
    if not isinstance(payload, Mapping):
        payload = event.get("metadata")
    if not isinstance(payload, Mapping):
        payload = {}
    result = {str(key): value for key, value in payload.items() if str(key)}
    result.setdefault(
        "contract_id",
        "PacketPlanIntegration",
    )
    result.setdefault("event_id", str(event.get("event_id") or "").strip())
    result.setdefault(
        "recorded_at_utc",
        str(event.get("timestamp_utc") or "").strip(),
    )
    return result


def _packet_creation_binding_payload(event: Mapping[str, object]) -> dict[str, object]:
    payload = event.get("packet_creation_binding")
    if not isinstance(payload, Mapping):
        payload = event.get("metadata")
    if not isinstance(payload, Mapping):
        payload = {}
    result = {str(key): value for key, value in payload.items() if str(key)}
    result.setdefault("contract_id", "PacketCreationBinding")
    result.setdefault("event_id", str(event.get("event_id") or "").strip())
    result.setdefault(
        "recorded_at_utc",
        str(event.get("timestamp_utc") or "").strip(),
    )
    return result


def _packet_durable_ingestion_payload(event: Mapping[str, object]) -> dict[str, object]:
    payload = event.get("packet_durable_ingestion")
    if not isinstance(payload, Mapping):
        payload = event.get("durable_binding")
    if not isinstance(payload, Mapping):
        payload = event.get("metadata")
    if not isinstance(payload, Mapping):
        payload = {}
    result = {str(key): value for key, value in payload.items() if str(key)}
    result.setdefault("contract_id", "PacketDurableIngestionReceipt")
    result.setdefault("event_id", str(event.get("event_id") or "").strip())
    result.setdefault(
        "recorded_at_utc",
        str(event.get("timestamp_utc") or "").strip(),
    )
    return result


def _packet_wake_payload(event: Mapping[str, object]) -> dict[str, object]:
    payload = event.get("wake_receipt")
    if not isinstance(payload, Mapping):
        payload = event.get("metadata")
    if not isinstance(payload, Mapping):
        payload = {}
    result = {str(key): value for key, value in payload.items() if str(key)}
    result.setdefault("contract_id", "PacketWakeReceipt")
    result.setdefault("event_id", str(event.get("event_id") or "").strip())
    result.setdefault(
        "recorded_at_utc",
        str(event.get("timestamp_utc") or "").strip(),
    )
    result.setdefault("packet_id", str(event.get("packet_id") or "").strip())
    return result


def action_request_lifecycle_status(event_type: str) -> str:
    if event_type == "action_request_execution_failed":
        return "failed"
    if event_type == "action_request_apply_pending_after_execution":
        return "apply_pending_after_execution"
    return ""


def _event_reason(event: Mapping[str, object]) -> str:
    metadata = event.get("metadata")
    if not isinstance(metadata, Mapping):
        return ""
    return str(metadata.get("reason") or "").strip()


def _metadata(event: Mapping[str, object]) -> dict[str, object]:
    metadata = event.get("metadata")
    return dict(metadata) if isinstance(metadata, Mapping) else {}


def _semantic_zref(packet: Mapping[str, object]) -> str:
    explicit = str(packet.get("semantic_zref") or "").strip()
    if explicit:
        return explicit
    packet_id = str(packet.get("packet_id") or "").strip()
    return f"packet:{packet_id}" if packet_id else ""
