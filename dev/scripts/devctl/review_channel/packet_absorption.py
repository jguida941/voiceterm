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
    build_packet_absorption_receipt,
    packet_semantically_ingested_by,
    valid_semantic_ingestion_receipts,
)
from ..runtime.value_coercion import coerce_string, coerce_string_items
from ..time_utils import utc_timestamp
from .event_models import ReviewChannelEventBundle
from .event_store import (
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    ReviewChannelArtifactPaths,
    append_event,
)
from .packet_body_observation import packet_body_digest
from .service_identity import project_id_for_repo

PACKET_ABSORPTION_EVENT_TYPE = "packet_absorption_recorded"
PACKET_ABSORPTION_EVENT_TYPES = frozenset({PACKET_ABSORPTION_EVENT_TYPE})


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
    if not _rows_have_required_plan_evidence(rows):
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

    absorbed_at = utc_timestamp()
    receipt = build_packet_absorption_receipt(
        packet_id=packet_id,
        body_sha256=digest,
        absorbed_by_actor=actor_id,
        absorbed_by_role=role_id,
        absorbed_by_session_id=session,
        absorbed_at_utc=absorbed_at,
        source_semantic_ingestion_receipt_id=coerce_string(
            semantic_receipt.get("receipt_id")
        ),
        source_semantic_ingestion_event_id=coerce_string(
            semantic_receipt.get("event_id")
        ),
        action_item_dispositions=_action_item_dispositions(rows),
        resulting_decision=(
            coerce_string(resulting_decision) or "packet_absorbed"
        ),
        decision_rationale=(
            coerce_string(decision_rationale)
            or (
                "semantic ingestion rows were dispositioned into a typed packet "
                "absorption receipt; plan authority changes require separate "
                "plan-integration evidence"
            )
        ),
        defer_reason=_joined_row_reasons(rows, dispositions={"deferred"}),
        blocked_reason=_joined_row_reasons(
            rows,
            dispositions={"blocked", "rejected", "needs_operator_decision"},
        ),
        next_slice_refs=_next_slice_refs(rows),
        superseded_packet_id=_superseded_packet_id(rows),
        evidence_refs=_evidence_refs(
            packet_id=packet_id,
            semantic_receipt=semantic_receipt,
            rows=rows,
        ),
    ).to_dict()
    event = {
        "event_type": PACKET_ABSORPTION_EVENT_TYPE,
        "event_id": "",
        "timestamp_utc": absorbed_at,
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
        "absorbed_by": actor_id,
        "absorbed_role": role_id,
        "absorbed_session_id": session,
        "absorbed_at_utc": absorbed_at,
        "target_role": role_id or packet.get("target_role"),
        "target_session_id": session or packet.get("target_session_id"),
        "source_packet_event_id": packet.get("latest_event_id"),
        "source_semantic_ingestion_receipt_id": coerce_string(
            semantic_receipt.get("receipt_id")
        ),
        "source_semantic_ingestion_event_id": coerce_string(
            semantic_receipt.get("event_id")
        ),
        "source_action": source_action,
        "packet_absorption_receipt": receipt,
        "idempotency_key": _absorption_idempotency_key(
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
            "packet_absorption_receipt": receipt,
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


def _action_item_dispositions(rows: tuple[Mapping[str, object], ...]) -> tuple[str, ...]:
    result: list[str] = []
    for row in rows:
        item_id = coerce_string(row.get("action_item_id"))
        disposition = _absorption_disposition(coerce_string(row.get("disposition")))
        if item_id and disposition:
            result.append(f"{item_id}:{disposition}")
    return tuple(result)


def _absorption_disposition(disposition: str) -> str:
    return disposition


def _rows_have_required_plan_evidence(
    rows: tuple[Mapping[str, object], ...],
) -> bool:
    for row in rows:
        if not _row_is_plan_affecting(row):
            continue
        if not _row_has_plan_evidence(row):
            return False
    return True


def _row_is_plan_affecting(row: Mapping[str, object]) -> bool:
    kind = coerce_string(row.get("kind")).strip().lower()
    target_ref = coerce_string(row.get("target_ref")).strip().lower()
    slice_ref = coerce_string(row.get("slice_ref")).strip().lower()
    plan_kinds = {
        "plan_change",
        "plan_update",
        "plan_proposal",
        "plan_integration",
        "plan_row",
    }
    return (
        kind in plan_kinds
        or target_ref.startswith(("plan:", "plan_row:"))
        or slice_ref.startswith(("plan:", "plan_row:"))
    )


def _row_has_plan_evidence(row: Mapping[str, object]) -> bool:
    evidence_refs = coerce_string_items(row.get("evidence_refs"))
    return any(
        ref.startswith(
            (
                "plan:",
                "plan_row:",
                "plan_proposal:",
                "packet_plan_integration:",
                "receipt:plan",
                "receipt:PacketPlanIntegration",
            )
        )
        for ref in evidence_refs
    )


def _joined_row_reasons(
    rows: tuple[Mapping[str, object], ...],
    *,
    dispositions: set[str],
) -> str:
    parts: list[str] = []
    for row in rows:
        disposition = coerce_string(row.get("disposition")).lower()
        if disposition not in dispositions:
            continue
        item_id = coerce_string(row.get("action_item_id"))
        reason = (
            coerce_string(row.get("blocked_reason"))
            or coerce_string(row.get("reason"))
        )
        if reason:
            parts.append(f"{item_id}: {reason}" if item_id else reason)
    return "; ".join(parts)


def _next_slice_refs(rows: tuple[Mapping[str, object], ...]) -> tuple[str, ...]:
    result: list[str] = []
    for row in rows:
        for ref in coerce_string_items(row.get("next_slice_refs")):
            if ref and ref not in result:
                result.append(ref)
    return tuple(result)


def _superseded_packet_id(rows: tuple[Mapping[str, object], ...]) -> str:
    ids = [
        coerce_string(row.get("superseded_packet_id"))
        for row in rows
        if coerce_string(row.get("superseded_packet_id"))
    ]
    return ";".join(ids)


def _evidence_refs(
    *,
    packet_id: str,
    semantic_receipt: Mapping[str, object],
    rows: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    refs = [f"packet:{packet_id}"]
    receipt_id = coerce_string(semantic_receipt.get("receipt_id"))
    if receipt_id:
        refs.append(f"receipt:{receipt_id}")
    for row in rows:
        for ref in coerce_string_items(row.get("evidence_refs")):
            if ref and ref not in refs:
                refs.append(ref)
    return tuple(refs)


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


def _absorption_idempotency_key(
    *,
    packet_id: str,
    actor: str,
    role: str,
    session: str,
    body_digest: str,
) -> str:
    return ":".join(
        (
            PACKET_ABSORPTION_EVENT_TYPE,
            packet_id,
            actor,
            role,
            session,
            body_digest,
        )
    )
