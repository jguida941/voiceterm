"""Build and finish event-backed packet transition events."""

from __future__ import annotations

import secrets
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

from .context_refs import normalize_context_pack_refs
from .event_store import (
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    ReviewChannelArtifactPaths,
    append_event,
    idempotency_key,
    load_events,
)
from .packet_attestation import validate_packet_apply_attestation
from .packet_contract import PacketTransitionRequest
from .packet_plan_integration import maybe_append_packet_plan_row
from .packet_source_identity import source_identity
from .remote_control_attachment_artifact import heartbeat_repo_remote_control_attachment

TRANSITION_EVENT_TYPES = {
    "ack": "packet_acked",
    "dismiss": "packet_dismissed",
    "apply": "packet_applied",
}


def build_transition_event(
    *,
    packet: dict[str, object],
    request: PacketTransitionRequest,
    event_id: str,
    timestamp_utc: str,
    project_id: str,
) -> dict[str, object]:
    event_type = TRANSITION_EVENT_TYPES[request.action]
    metadata = _transition_metadata(
        packet=packet,
        request=request,
        timestamp_utc=timestamp_utc,
    )
    return dict(
        schema_version=1,
        event_id=event_id,
        session_id=request.session_id,
        project_id=project_id,
        packet_id=request.packet_id,
        trace_id=packet.get("trace_id"),
        timestamp_utc=timestamp_utc,
        source="review_channel",
        plan_id=_transition_plan_id(packet=packet, request=request),
        controller_run_id=request.controller_run_id,
        correlation_id=request.correlation_id or packet.get("correlation_id"),
        causation_id=request.causation_id or packet.get("causation_id"),
        run_id=request.run_id or packet.get("run_id"),
        event_type=event_type,
        from_agent=packet.get("from_agent"),
        to_agent=packet.get("to_agent"),
        kind=packet.get("kind"),
        summary=packet.get("summary"),
        body=packet.get("body"),
        evidence_refs=list(packet.get("evidence_refs") or []),
        guidance_refs=list(packet.get("guidance_refs") or []),
        context_pack_refs=normalize_context_pack_refs(
            packet.get("context_pack_refs")
        ),
        confidence=float(packet.get("confidence") or 0.0),
        requested_action=packet.get("requested_action"),
        policy_hint=packet.get("policy_hint"),
        approval_required=bool(packet.get("approval_required")),
        target_kind=packet.get("target_kind"),
        target_ref=packet.get("target_ref"),
        target_revision=packet.get("target_revision"),
        target_role=packet.get("target_role"),
        target_session_id=packet.get("target_session_id"),
        requested_session_visibility=packet.get("requested_session_visibility"),
        anchor_refs=list(packet.get("anchor_refs") or []),
        intake_ref=packet.get("intake_ref"),
        mutation_op=packet.get("mutation_op"),
        pipeline_generation=packet.get("pipeline_generation"),
        staged_snapshot_hash=packet.get("staged_snapshot_hash"),
        guard_results_summary=packet.get("guard_results_summary"),
        full_guard_bundle_evidence=packet.get("full_guard_bundle_evidence"),
        semantic_zref=packet.get("semantic_zref") or _packet_semantic_zref(packet),
        source_identity=source_identity(packet),
        status={"ack": "acked", "dismiss": "dismissed", "apply": "applied"}[
            request.action
        ],
        idempotency_key=idempotency_key(
            event_type,
            request.packet_id,
            request.actor,
        ),
        nonce=secrets.token_hex(12),
        expires_at_utc=packet.get("expires_at_utc"),
        metadata=metadata,
    )


def _packet_semantic_zref(packet: dict[str, object]) -> str:
    packet_id = str(packet.get("packet_id") or "").strip()
    return f"packet:{packet_id}" if packet_id else ""


def _transition_plan_id(
    *,
    packet: Mapping[str, object],
    request: PacketTransitionRequest,
) -> str:
    packet_plan_id = str(packet.get("plan_id") or "").strip()
    request_plan_id = str(request.plan_id or "").strip()
    if request_plan_id and request_plan_id != DEFAULT_REVIEW_CHANNEL_PLAN_ID:
        return request_plan_id
    return packet_plan_id or request_plan_id


def finish_transition_event(
    *,
    repo_root: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    packet: dict[str, object],
    request: PacketTransitionRequest,
    written_event: dict[str, object],
) -> dict[str, object]:
    heartbeat_repo_remote_control_attachment(
        repo_root=repo_root,
        provider=str(request.actor or "").strip(),
        seen_at_utc=str(written_event.get("timestamp_utc") or "").strip(),
    )
    if request.action == "apply":
        plan_integration = maybe_append_packet_plan_row(
            repo_root=repo_root,
            packet=packet,
            event=written_event,
        )
        written_event["plan_ingestion"] = plan_integration
        written_event["plan_integration"] = plan_integration
        if _should_record_plan_integration_event(packet, plan_integration):
            integration_event = _plan_integration_event(
                packet=packet,
                request=request,
                written_event=written_event,
                plan_integration=plan_integration,
            )
            written_integration_event = append_event(
                Path(artifact_paths.event_log_path),
                integration_event,
                existing_events=load_events(Path(artifact_paths.event_log_path)),
            )
            written_event["plan_integration_event_id"] = written_integration_event.get(
                "event_id"
            )
    return written_event


def _should_record_plan_integration_event(
    packet: Mapping[str, object],
    plan_integration: Mapping[str, object],
) -> bool:
    if str(packet.get("target_kind") or "").strip() != "plan":
        return False
    reason = str(plan_integration.get("reason") or "").strip()
    return reason != "target_kind_not_plan"


def _plan_integration_event(
    *,
    packet: Mapping[str, object],
    request: PacketTransitionRequest,
    written_event: Mapping[str, object],
    plan_integration: Mapping[str, object],
) -> dict[str, object]:
    packet_id = str(packet.get("packet_id") or request.packet_id or "").strip()
    event_type = (
        "packet_plan_ingestion_recorded"
        if _plan_integration_recorded(plan_integration)
        else "packet_plan_ingestion_failed"
    )
    actor = str(request.actor or "").strip()
    return {
        "schema_version": 1,
        "event_id": "",
        "session_id": request.session_id,
        "project_id": written_event.get("project_id"),
        "packet_id": packet_id,
        "trace_id": packet.get("trace_id"),
        "timestamp_utc": written_event.get("timestamp_utc"),
        "source": "review_channel",
        "plan_id": written_event.get("plan_id") or packet.get("plan_id"),
        "controller_run_id": request.controller_run_id,
        "correlation_id": request.correlation_id or packet.get("correlation_id"),
        "causation_id": request.causation_id or packet.get("causation_id"),
        "run_id": request.run_id or packet.get("run_id"),
        "event_type": event_type,
        "from_agent": packet.get("from_agent"),
        "to_agent": packet.get("to_agent"),
        "kind": packet.get("kind"),
        "summary": packet.get("summary"),
        "body": packet.get("body"),
        "target_kind": packet.get("target_kind"),
        "target_ref": packet.get("target_ref"),
        "target_revision": packet.get("target_revision"),
        "status": (
            "applied" if event_type == "packet_plan_ingestion_recorded"
            else "plan_ingestion_failed"
        ),
        "idempotency_key": idempotency_key(event_type, packet_id, actor),
        "nonce": secrets.token_hex(12),
        "plan_ingestion": dict(plan_integration),
        "plan_integration": dict(plan_integration),
        "metadata": {
            "actor": actor,
            "plan_ingestion": dict(plan_integration),
            "plan_integration": dict(plan_integration),
            "correlation_id": request.correlation_id
            or packet.get("correlation_id")
            or "",
            "causation_id": request.causation_id or packet.get("causation_id") or "",
            "run_id": request.run_id or packet.get("run_id") or "",
        },
    }


def _plan_integration_recorded(plan_integration: Mapping[str, object]) -> bool:
    return str(plan_integration.get("status") or "").strip() in {
        "inserted",
        "updated",
        "already_present",
    }


def _transition_metadata(
    *,
    packet: dict[str, object],
    request: PacketTransitionRequest,
    timestamp_utc: str,
) -> dict[str, object]:
    metadata: dict[str, object] = {"actor": request.actor}
    guard_attestation = _normalized_guard_attestation(
        request=request,
        timestamp_utc=timestamp_utc,
    )
    if request.action == "apply" and guard_attestation is not None:
        metadata["guard_attestation"] = guard_attestation.to_dict()
    event = {
        "event_type": TRANSITION_EVENT_TYPES[request.action],
        "timestamp_utc": timestamp_utc,
        "metadata": metadata,
    }
    if request.action == "apply":
        attestation = validate_packet_apply_attestation(packet=packet, event=event)
        metadata["guard_attestation"] = attestation.to_dict()
    return metadata


def _normalized_guard_attestation(
    *,
    request: PacketTransitionRequest,
    timestamp_utc: str,
):
    guard_attestation = request.guard_attestation
    if (
        request.action != "apply"
        or guard_attestation is None
        or (
            guard_attestation.attested_at_utc
            and guard_attestation.attested_by
        )
    ):
        return guard_attestation
    return replace(
        guard_attestation,
        attested_at_utc=guard_attestation.attested_at_utc or timestamp_utc,
        attested_by=guard_attestation.attested_by or request.actor,
    )


__all__ = [
    "TRANSITION_EVENT_TYPES",
    "build_transition_event",
    "finish_transition_event",
]
