"""Typed semantic-ingestion events for review-channel packet bodies."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from ..runtime.correlation_spine import (
    causation_id_for_ref,
    correlation_id_for_ref,
    run_id_for_ref,
)
from ..runtime.packet_absorption import (
    PACKET_SEMANTIC_INGESTION_RECEIPT_CONTRACT_ID,
    build_packet_semantic_ingestion_receipt,
)
from ..runtime.value_coercion import coerce_string
from ..time_utils import utc_timestamp
from .event_models import ReviewChannelEventBundle
from .event_store import (
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    ReviewChannelArtifactPaths,
    append_event,
)
from .packet_body_observation import packet_body_digest, packet_body_observed_by
from .service_identity import project_id_for_repo

PACKET_SEMANTIC_INGESTION_EVENT_TYPE = "packet_semantic_ingestion_recorded"
PACKET_SEMANTIC_INGESTION_EVENT_TYPES = frozenset(
    {PACKET_SEMANTIC_INGESTION_EVENT_TYPE}
)


def record_packet_semantic_ingestion(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    bundle: ReviewChannelEventBundle,
    packet: Mapping[str, object],
    actor: str,
    role: str = "",
    session_id: str = "",
    action_item_rows: Sequence[Mapping[str, object]] = (),
    resulting_decision: str = "",
    decision_rationale: str = "",
    source_action: str = "review-channel ingest",
) -> tuple[ReviewChannelEventBundle, dict[str, object] | None]:
    """Append an idempotent event proving semantic packet-body ingestion."""
    actor_id = coerce_string(actor)
    packet_id = coerce_string(packet.get("packet_id"))
    digest = packet_body_digest(packet) or coerce_string(packet.get("body_digest"))
    if not actor_id or not packet_id or not digest:
        return bundle, None
    role_id = coerce_string(role)
    session = coerce_string(session_id)
    if not packet_body_observed_by(
        packet,
        actor=actor_id,
        role=role_id,
        session=session,
        body_digest=digest,
    ):
        return bundle, None
    rows = tuple(action_item_rows)
    if not rows:
        return bundle, None
    decision = (
        coerce_string(resulting_decision) or "semantic_ingestion_recorded"
    )
    rationale = coerce_string(decision_rationale) or (
        "packet body parsed into typed semantic-ingestion rows; "
        "absorption remains a separate lifecycle step"
    )
    existing = _existing_semantic_ingestion_event(
        bundle.events,
        packet_id=packet_id,
        actor=actor_id,
        role=role_id,
        session=session,
        body_digest=digest,
    )
    if existing:
        from .event_reducer import refresh_event_bundle

        return refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        ), existing

    ingested_at = utc_timestamp()
    receipt = build_packet_semantic_ingestion_receipt(
        packet_id=packet_id,
        body_sha256=digest,
        ingested_by_actor=actor_id,
        ingested_by_role=role_id,
        ingested_by_session_id=session,
        ingested_at_utc=ingested_at,
        action_item_rows=rows,
        resulting_decision=decision,
        decision_rationale=rationale,
    ).to_dict()
    event = {
        "event_type": PACKET_SEMANTIC_INGESTION_EVENT_TYPE,
        "event_id": "",
        "timestamp_utc": ingested_at,
        "project_id": project_id_for_repo(repo_root),
        "session_id": session or DEFAULT_REVIEW_CHANNEL_SESSION_ID,
        "trace_id": packet.get("trace_id"),
        "plan_id": packet.get("plan_id"),
        "packet_id": packet_id,
        "from_agent": packet.get("from_agent"),
        "to_agent": packet.get("to_agent"),
        "kind": packet.get("kind"),
        "summary": packet.get("summary"),
        "status": packet.get("status"),
        "body_digest": digest,
        "semantic_ingested_by": actor_id,
        "semantic_ingested_role": role_id,
        "semantic_ingested_session_id": session,
        "semantic_ingested_at_utc": ingested_at,
        "target_role": role_id or packet.get("target_role"),
        "target_session_id": session or packet.get("target_session_id"),
        "source_packet_event_id": packet.get("latest_event_id"),
        "source_action": source_action,
        "packet_semantic_ingestion_receipt": receipt,
        "idempotency_key": _semantic_ingestion_idempotency_key(
            packet_id=packet_id,
            actor=actor_id,
            role=role_id,
            session=session,
            body_digest=digest,
        ),
        "metadata": {
            "actor": actor_id,
            "role": role_id,
            "session": session,
            "body_digest": digest,
            "source_packet_event_id": coerce_string(packet.get("latest_event_id")),
            "source_action": source_action,
            "packet_semantic_ingestion_receipt": receipt,
        },
    }
    written = append_event(
        Path(artifact_paths.event_log_path),
        event,
        existing_events=bundle.events,
    )
    from .event_reducer import refresh_event_bundle

    refreshed = refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    return refreshed, written


def packet_semantic_ingestion_payload(event: Mapping[str, object]) -> dict[str, object]:
    payload = event.get("packet_semantic_ingestion_receipt")
    if not isinstance(payload, Mapping):
        metadata = event.get("metadata")
        payload = (
            metadata.get("packet_semantic_ingestion_receipt")
            if isinstance(metadata, Mapping)
            else {}
        )
    if not isinstance(payload, Mapping):
        payload = {}
    result = {str(key): value for key, value in payload.items() if str(key)}
    result.setdefault("contract_id", PACKET_SEMANTIC_INGESTION_RECEIPT_CONTRACT_ID)
    result.setdefault("event_id", coerce_string(event.get("event_id")))
    result.setdefault(
        "recorded_at_utc",
        coerce_string(event.get("timestamp_utc")),
    )
    result.setdefault("packet_id", coerce_string(event.get("packet_id")))
    result.setdefault("body_sha256", coerce_string(event.get("body_digest")))
    result.setdefault("ingested_by_actor", coerce_string(event.get("semantic_ingested_by")))
    result.setdefault("ingested_by_role", coerce_string(event.get("semantic_ingested_role")))
    result.setdefault(
        "ingested_by_session_id",
        coerce_string(event.get("semantic_ingested_session_id")),
    )
    result.setdefault(
        "ingested_at_utc",
        coerce_string(event.get("semantic_ingested_at_utc"))
        or coerce_string(event.get("timestamp_utc")),
    )
    if not coerce_string(result.get("correlation_id")):
        packet_id = coerce_string(result.get("packet_id"))
        result["correlation_id"] = coerce_string(
            event.get("correlation_id")
        ) or correlation_id_for_ref("packet", packet_id)
    if not coerce_string(result.get("causation_id")):
        source_event_id = coerce_string(event.get("source_packet_event_id"))
        result["causation_id"] = coerce_string(event.get("causation_id")) or (
            causation_id_for_ref("event", source_event_id)
            if source_event_id
            else causation_id_for_ref(
                "packet_semantic_ingestion",
                coerce_string(result.get("packet_id")),
            )
        )
    if not coerce_string(result.get("run_id")):
        run_seed = (
            coerce_string(event.get("run_id"))
            or coerce_string(result.get("ingested_by_session_id"))
            or coerce_string(event.get("target_session_id"))
            or coerce_string(event.get("session_id"))
            or coerce_string(result.get("packet_id"))
        )
        result["run_id"] = coerce_string(event.get("run_id")) or run_id_for_ref(
            "session",
            run_seed,
        )
    return result


def packet_semantic_ingestion_payload_for_packet(
    event: Mapping[str, object],
    packet: Mapping[str, object],
) -> dict[str, object]:
    payload = packet_semantic_ingestion_payload(event)
    payload.setdefault("packet_id", coerce_string(packet.get("packet_id")))
    if not coerce_string(payload.get("body_sha256")):
        payload["body_sha256"] = (
            packet_body_digest(packet) or coerce_string(packet.get("body_digest"))
        )
    return payload


def _existing_semantic_ingestion_event(
    events: list[dict[str, object]],
    *,
    packet_id: str,
    actor: str,
    role: str,
    session: str,
    body_digest: str,
) -> dict[str, object] | None:
    for event in reversed(events):
        if (
            coerce_string(event.get("event_type"))
            != PACKET_SEMANTIC_INGESTION_EVENT_TYPE
        ):
            continue
        if coerce_string(event.get("packet_id")) != packet_id:
            continue
        payload = packet_semantic_ingestion_payload(event)
        if (
            coerce_string(payload.get("ingested_by_actor")) == actor
            and coerce_string(payload.get("ingested_by_role")) == role
            and coerce_string(payload.get("ingested_by_session_id")) == session
            and coerce_string(payload.get("body_sha256")) == body_digest
        ):
            return event
    return None


def _semantic_ingestion_idempotency_key(
    *,
    packet_id: str,
    actor: str,
    role: str,
    session: str,
    body_digest: str,
) -> str:
    return (
        "packet_semantic_ingestion_recorded:"
        f"{packet_id}:{actor}:{role}:{session}:{body_digest}"
    )


__all__ = [
    "PACKET_SEMANTIC_INGESTION_EVENT_TYPE",
    "PACKET_SEMANTIC_INGESTION_EVENT_TYPES",
    "packet_semantic_ingestion_payload",
    "packet_semantic_ingestion_payload_for_packet",
    "record_packet_semantic_ingestion",
]
