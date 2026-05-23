"""Typed packet-absorption events for review-channel packets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from ..runtime.correlation_spine import (
    causation_id_for_ref,
    correlation_id_for_ref,
    run_id_for_ref,
)
from ..runtime.packet_absorption import (
    PACKET_ABSORPTION_RECEIPT_CONTRACT_ID,
    packet_semantically_ingested_by,
    valid_semantic_ingestion_receipts,
)
from ..runtime.value_coercion import coerce_string
from .event_models import ReviewChannelEventBundle
from .event_store import (
    ReviewChannelArtifactPaths,
    append_event,
)
from .packet_absorption_constants import (
    PACKET_ABSORPTION_EVENT_TYPE,
    PACKET_ABSORPTION_EVENT_TYPES,
)
from .packet_absorption_event_builder import build_packet_absorption_event
from .packet_absorption_plan_evidence import rows_have_required_plan_evidence
from .packet_body_observation import packet_body_digest


def record_packet_absorption(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    bundle: ReviewChannelEventBundle,
    packet: Mapping[str, object],
    actor: str,
    role: str = "",
    session_id: str = "",
    resulting_decision: str = "",
    decision_rationale: str = "",
    source_action: str = "review-channel absorb",
) -> tuple[ReviewChannelEventBundle, dict[str, object] | None]:
    """Append an idempotent PacketAbsorptionReceipt event.

    Absorption is deliberately downstream of semantic ingestion. It does not
    create semantic rows; it consumes the explicit rows already recorded for the
    same actor/role/session and turns them into a lifecycle disposition.
    """
    if not isinstance(bundle, ReviewChannelEventBundle):
        raise TypeError(
            "absorb_packet requires a typed ReviewChannelEventBundle"
        )

    actor_id = coerce_string(actor)
    role_id = coerce_string(role)
    session = coerce_string(session_id)
    packet_id = coerce_string(packet.get("packet_id"))
    digest = coerce_string(packet.get("body_digest")) or packet_body_digest(packet)
    if not (actor_id and role_id and session and packet_id and digest):
        return bundle, None
    if not packet_semantically_ingested_by(
        packet,
        actor=actor_id,
        role=role_id,
        session=session,
    ):
        return bundle, None
    semantic_receipt = _matching_semantic_ingestion_receipt(
        packet,
        actor=actor_id,
        role=role_id,
        session=session,
        body_digest=digest,
    )
    if not semantic_receipt:
        return bundle, None
    rows = _semantic_action_item_rows(semantic_receipt)
    if not rows:
        return bundle, None
    if not rows_have_required_plan_evidence(rows, packet=packet):
        return bundle, None

    existing = _existing_absorption_event(
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

    event = build_packet_absorption_event(
        repo_root=repo_root,
        packet=packet,
        packet_id=packet_id,
        digest=digest,
        actor_id=actor_id,
        role_id=role_id,
        session=session,
        semantic_receipt=semantic_receipt,
        rows=rows,
        resulting_decision=resulting_decision,
        decision_rationale=decision_rationale,
        source_action=source_action,
    )
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


def packet_absorption_payload(event: Mapping[str, object]) -> dict[str, object]:
    payload = event.get("packet_absorption_receipt")
    if not isinstance(payload, Mapping):
        metadata = event.get("metadata")
        payload = (
            metadata.get("packet_absorption_receipt")
            if isinstance(metadata, Mapping)
            else {}
        )
    if not isinstance(payload, Mapping):
        payload = {}
    result = {str(key): value for key, value in payload.items() if str(key)}
    result.setdefault("contract_id", PACKET_ABSORPTION_RECEIPT_CONTRACT_ID)
    result.setdefault("event_id", coerce_string(event.get("event_id")))
    result.setdefault("recorded_at_utc", coerce_string(event.get("timestamp_utc")))
    result.setdefault("packet_id", coerce_string(event.get("packet_id")))
    result.setdefault("body_sha256", coerce_string(event.get("body_digest")))
    result.setdefault(
        "source_semantic_ingestion_receipt_id",
        coerce_string(event.get("source_semantic_ingestion_receipt_id")),
    )
    result.setdefault(
        "source_semantic_ingestion_event_id",
        coerce_string(event.get("source_semantic_ingestion_event_id")),
    )
    result.setdefault("absorbed_by_actor", coerce_string(event.get("absorbed_by")))
    result.setdefault("absorbed_by_role", coerce_string(event.get("absorbed_role")))
    result.setdefault(
        "absorbed_by_session_id",
        coerce_string(event.get("absorbed_session_id")),
    )
    result.setdefault(
        "absorbed_at_utc",
        coerce_string(event.get("absorbed_at_utc"))
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
                "packet_absorption",
                coerce_string(result.get("packet_id")),
            )
        )
    if not coerce_string(result.get("run_id")):
        run_seed = (
            coerce_string(event.get("run_id"))
            or coerce_string(result.get("absorbed_by_session_id"))
            or coerce_string(event.get("target_session_id"))
            or coerce_string(event.get("session_id"))
            or coerce_string(result.get("packet_id"))
        )
        result["run_id"] = coerce_string(event.get("run_id")) or run_id_for_ref(
            "session",
            run_seed,
        )
    return result


def packet_absorption_payload_for_packet(
    event: Mapping[str, object],
    packet: Mapping[str, object],
) -> dict[str, object]:
    payload = packet_absorption_payload(event)
    payload.setdefault("packet_id", coerce_string(packet.get("packet_id")))
    if not coerce_string(payload.get("body_sha256")):
        payload["body_sha256"] = (
            coerce_string(packet.get("body_digest")) or packet_body_digest(packet)
        )
    return payload


def _matching_semantic_ingestion_receipt(
    packet: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
    body_digest: str,
) -> Mapping[str, object]:
    for receipt in reversed(valid_semantic_ingestion_receipts(packet)):
        if (
            coerce_string(receipt.get("packet_id")) == coerce_string(packet.get("packet_id"))
            and coerce_string(receipt.get("body_sha256")) == body_digest
            and coerce_string(receipt.get("ingested_by_actor")) == actor
            and coerce_string(receipt.get("ingested_by_role")) == role
            and coerce_string(receipt.get("ingested_by_session_id")) == session
        ):
            return receipt
    return {}


def _semantic_ingestion_receipts(
    packet: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows: list[Mapping[str, object]] = []
    receipt = packet.get("packet_semantic_ingestion_receipt")
    if isinstance(receipt, Mapping):
        rows.append(receipt)
    events = packet.get("semantic_ingestion_events")
    if isinstance(events, Sequence) and not isinstance(events, (str, bytes)):
        for event in events:
            if not isinstance(event, Mapping):
                continue
            receipt = event.get("packet_semantic_ingestion_receipt")
            if isinstance(receipt, Mapping):
                rows.append(receipt)
            elif coerce_string(event.get("contract_id")) == (
                "PacketSemanticIngestionReceipt"
            ):
                rows.append(event)
    return tuple(rows)


def _semantic_action_item_rows(
    receipt: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows = receipt.get("action_item_rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _existing_absorption_event(
    events: list[dict[str, object]],
    *,
    packet_id: str,
    actor: str,
    role: str,
    session: str,
    body_digest: str,
) -> dict[str, object] | None:
    for event in reversed(events):
        if coerce_string(event.get("event_type")) != PACKET_ABSORPTION_EVENT_TYPE:
            continue
        if coerce_string(event.get("packet_id")) != packet_id:
            continue
        payload = packet_absorption_payload(event)
        if (
            coerce_string(payload.get("absorbed_by_actor")) == actor
            and coerce_string(payload.get("absorbed_by_role")) == role
            and coerce_string(payload.get("absorbed_by_session_id")) == session
            and coerce_string(payload.get("body_sha256")) == body_digest
        ):
            return event
    return None

