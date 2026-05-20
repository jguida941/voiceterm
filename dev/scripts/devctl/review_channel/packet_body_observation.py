"""Typed packet-body observation events for review-channel consumers."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path

from ..runtime.correlation_spine import (
    causation_id_for_ref,
    correlation_id_for_ref,
    run_id_for_ref,
)
from ..runtime.packet_observation_receipt import build_packet_observation_receipt
from ..time_utils import utc_timestamp
from .event_models import ReviewChannelEventBundle
from .event_store import (
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    ReviewChannelArtifactPaths,
    append_event,
)
from .service_identity import project_id_for_repo

PACKET_BODY_OBSERVATION_EVENT_TYPE = "packet_body_observed"
PACKET_BODY_OBSERVATION_EVENT_TYPES = frozenset({PACKET_BODY_OBSERVATION_EVENT_TYPE})
PACKET_BODY_OBSERVATION_CONTRACT_ID = "PacketBodyObservation"


def packet_body_digest(packet: Mapping[str, object]) -> str:
    body = str(packet.get("body") or "")
    if not body:
        return ""
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def packet_body_observed_by(
    packet: Mapping[str, object],
    *,
    actor: str,
    role: str = "",
    session: str = "",
    body_digest: str | None = None,
) -> bool:
    actor_id = actor.strip()
    role_id = role.strip()
    session_id = session.strip()
    digest = body_digest or packet_body_digest(packet)
    if not actor_id or not digest:
        return False
    if _body_observation_matches(
        packet,
        actor=actor_id,
        role=role_id,
        session=session_id,
        body_digest=digest,
        allow_event_session_fallback=False,
    ):
        return True
    for event in _body_observation_events(packet):
        if not isinstance(event, Mapping):
            continue
        if _body_observation_matches(
            event,
            actor=actor_id,
            role=role_id,
            session=session_id,
            body_digest=digest,
            allow_event_session_fallback=True,
        ):
            return True
    return False


def _body_observation_events(
    packet: Mapping[str, object],
) -> tuple[object, ...]:
    events = packet.get("body_observation_events")
    if isinstance(events, (list, tuple)):
        return tuple(events)
    return ()


def record_packet_body_observation(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    bundle: ReviewChannelEventBundle,
    packet: Mapping[str, object],
    actor: str,
    role: str = "",
    session_id: str = "",
    source_action: str = "review-channel show",
) -> tuple[ReviewChannelEventBundle, dict[str, object] | None]:
    """Append an idempotent event proving an actor opened a packet body."""
    actor_id = actor.strip()
    packet_id = str(packet.get("packet_id") or "").strip()
    digest = packet_body_digest(packet)
    if not actor_id or not packet_id or not digest:
        return bundle, None
    role_id = role.strip()
    session = session_id.strip()
    if packet_body_observed_by(
        packet,
        actor=actor_id,
        role=role_id,
        session=session,
        body_digest=digest,
    ):
        return bundle, None
    existing = _existing_observation_event(
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

    observed_at = utc_timestamp()
    body_text = str(packet.get("body") or "")
    event = {
        "event_type": PACKET_BODY_OBSERVATION_EVENT_TYPE,
        "event_id": "",
        "timestamp_utc": observed_at,
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
        "body_length": len(body_text),
        "body_observed_by": actor_id,
        "body_observed_role": role_id,
        "body_observed_session_id": session,
        "body_observed_at_utc": observed_at,
        "target_role": role_id or packet.get("target_role"),
        "target_session_id": session or packet.get("target_session_id"),
        "source_packet_event_id": packet.get("latest_event_id"),
        "source_action": source_action,
        "idempotency_key": _observation_idempotency_key(
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
            "body_length": len(body_text),
            "source_packet_event_id": str(packet.get("latest_event_id") or ""),
            "source_action": source_action,
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


def packet_body_observation_payload(event: Mapping[str, object]) -> dict[str, object]:
    payload = event.get("metadata")
    if not isinstance(payload, Mapping):
        payload = {}
    observed_at = str(
        event.get("body_observed_at_utc") or event.get("timestamp_utc") or ""
    ).strip()
    return {
        "contract_id": PACKET_BODY_OBSERVATION_CONTRACT_ID,
        "schema_version": 1,
        "event_id": str(event.get("event_id") or "").strip(),
        "packet_id": str(event.get("packet_id") or "").strip(),
        "body_observed_by": str(
            event.get("body_observed_by")
            or payload.get("actor")
            or event.get("actor")
            or ""
        ).strip(),
        "body_observed_role": str(
            event.get("body_observed_role")
            or payload.get("role")
            or event.get("target_role")
            or ""
        ).strip(),
        "body_observed_session_id": str(
            event.get("body_observed_session_id")
            or payload.get("session")
            or event.get("target_session_id")
            or event.get("session_id")
            or ""
        ).strip(),
        "body_observed_at_utc": observed_at,
        "body_digest": str(
            event.get("body_digest") or payload.get("body_digest") or ""
        ).strip(),
        "body_length": int(event.get("body_length") or payload.get("body_length") or 0),
        "source_packet_event_id": str(
            event.get("source_packet_event_id")
            or payload.get("source_packet_event_id")
            or ""
        ).strip(),
        "source_action": str(
            event.get("source_action") or payload.get("source_action") or ""
        ).strip(),
        "correlation_id": str(event.get("correlation_id") or "").strip(),
        "causation_id": str(event.get("causation_id") or "").strip(),
        "run_id": str(event.get("run_id") or "").strip(),
    }


def packet_body_observation_payload_for_packet(
    event: Mapping[str, object],
    packet: Mapping[str, object],
) -> dict[str, object]:
    """Project one body-observation event, backfilling legacy lineage from packet."""
    payload = packet_body_observation_payload(event)
    packet_id = str(
        payload.get("packet_id") or packet.get("packet_id") or ""
    ).strip()
    if not str(payload.get("correlation_id") or "").strip():
        payload["correlation_id"] = str(
            packet.get("correlation_id") or ""
        ).strip() or correlation_id_for_ref("packet", packet_id)
    if not str(payload.get("causation_id") or "").strip():
        source_event_id = str(payload.get("source_packet_event_id") or "").strip()
        payload["causation_id"] = str(packet.get("causation_id") or "").strip() or (
            causation_id_for_ref("event", source_event_id)
            if source_event_id
            else causation_id_for_ref("packet_body_observation", packet_id)
        )
    if not str(payload.get("run_id") or "").strip():
        run_seed = str(
            packet.get("run_id")
            or payload.get("body_observed_session_id")
            or packet.get("target_session_id")
            or packet.get("session_id")
            or packet_id
        ).strip()
        payload["run_id"] = (
            str(packet.get("run_id") or "").strip()
            or run_id_for_ref("session", run_seed)
        )
    return payload


def packet_observation_receipt_payload_for_packet(
    event: Mapping[str, object],
    packet: Mapping[str, object],
    *,
    attention_cleared: bool = False,
    drain_report_ref: str = "",
) -> dict[str, object]:
    """Project P233 PacketObservationReceipt from a body-observed event."""
    payload = packet_body_observation_payload_for_packet(event, packet)
    receipt = build_packet_observation_receipt(
        observed_packet_id=str(payload.get("packet_id") or "").strip(),
        observed_body_sha256=str(payload.get("body_digest") or "").strip(),
        observer_actor_id=str(payload.get("body_observed_by") or "").strip(),
        observer_role_id=str(payload.get("body_observed_role") or "").strip(),
        observer_session_id=str(
            payload.get("body_observed_session_id") or ""
        ).strip(),
        observed_at_utc=str(payload.get("body_observed_at_utc") or "").strip(),
        observed_body_length=int(payload.get("body_length") or 0),
        source_observation_event_id=str(payload.get("event_id") or "").strip(),
        source_packet_event_id=str(
            payload.get("source_packet_event_id") or ""
        ).strip(),
        source_action=str(payload.get("source_action") or "").strip(),
        attention_cleared=attention_cleared,
        drain_report_ref=drain_report_ref,
        correlation_id=str(payload.get("correlation_id") or "").strip(),
        causation_id=str(payload.get("causation_id") or "").strip(),
        run_id=str(payload.get("run_id") or "").strip(),
    )
    return receipt.to_dict()


def _existing_observation_event(
    events: list[dict[str, object]],
    *,
    packet_id: str,
    actor: str,
    role: str,
    session: str,
    body_digest: str,
) -> dict[str, object] | None:
    for event in reversed(events):
        if str(event.get("event_type") or "").strip() != PACKET_BODY_OBSERVATION_EVENT_TYPE:
            continue
        if str(event.get("packet_id") or "").strip() != packet_id:
            continue
        payload = packet_body_observation_payload(event)
        if (
            str(payload.get("body_observed_by") or "").strip() == actor
            and _observation_scope_matches(
                payload,
                role=role,
                session=session,
                allow_event_session_fallback=False,
            )
            and str(payload.get("body_digest") or "").strip() == body_digest
        ):
            return event
    return None


def _observation_idempotency_key(
    *,
    packet_id: str,
    actor: str,
    role: str,
    session: str,
    body_digest: str,
) -> str:
    return f"packet_body_observed:{packet_id}:{actor}:{role}:{session}:{body_digest}"


def _body_observation_matches(
    row: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
    body_digest: str,
    allow_event_session_fallback: bool,
) -> bool:
    if str(row.get("body_observed_by") or "").strip() != actor:
        return False
    if str(row.get("body_digest") or "").strip() != body_digest:
        return False
    return _observation_scope_matches(
        row,
        role=role,
        session=session,
        allow_event_session_fallback=allow_event_session_fallback,
    )


def _observation_scope_matches(
    row: Mapping[str, object],
    *,
    role: str,
    session: str,
    allow_event_session_fallback: bool,
) -> bool:
    if role:
        observed_role = str(row.get("body_observed_role") or "").strip()
        if allow_event_session_fallback and not observed_role:
            observed_role = str(row.get("target_role") or "").strip()
        if observed_role != role:
            return False
    if session:
        observed_session = str(row.get("body_observed_session_id") or "").strip()
        if allow_event_session_fallback and not observed_session:
            observed_session = str(
                row.get("target_session_id") or row.get("session_id") or ""
            ).strip()
        if observed_session != session:
            return False
    return True


__all__ = [
    "PACKET_BODY_OBSERVATION_CONTRACT_ID",
    "PACKET_BODY_OBSERVATION_EVENT_TYPE",
    "PACKET_BODY_OBSERVATION_EVENT_TYPES",
    "packet_body_digest",
    "packet_body_observation_payload",
    "packet_body_observation_payload_for_packet",
    "packet_body_observed_by",
    "packet_observation_receipt_payload_for_packet",
    "record_packet_body_observation",
]
