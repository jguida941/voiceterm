"""Event construction helpers for packet absorption."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..runtime.packet_absorption import build_packet_absorption_receipt
from ..runtime.value_coercion import coerce_string, coerce_string_items
from ..time_utils import utc_timestamp
from .event_store import DEFAULT_REVIEW_CHANNEL_SESSION_ID
from .packet_absorption_constants import PACKET_ABSORPTION_EVENT_TYPE
from .service_identity import project_id_for_repo


def build_packet_absorption_event(
    *,
    repo_root: Path,
    packet: Mapping[str, object],
    packet_id: str,
    digest: str,
    actor_id: str,
    role_id: str,
    session: str,
    semantic_receipt: Mapping[str, object],
    rows: tuple[Mapping[str, object], ...],
    resulting_decision: str,
    decision_rationale: str,
    source_action: str,
) -> dict[str, object]:
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
        resulting_decision=coerce_string(resulting_decision) or "packet_absorbed",
        decision_rationale=coerce_string(decision_rationale) or (
            "semantic ingestion rows were dispositioned into a typed packet "
            "absorption receipt; plan authority changes require separate "
            "plan-integration evidence"
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
    return {
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


def _action_item_dispositions(rows: tuple[Mapping[str, object], ...]) -> tuple[str, ...]:
    result: list[str] = []
    for row in rows:
        item_id = coerce_string(row.get("action_item_id"))
        disposition = coerce_string(row.get("disposition"))
        if item_id and disposition:
            result.append(f"{item_id}:{disposition}")
    return tuple(result)


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
