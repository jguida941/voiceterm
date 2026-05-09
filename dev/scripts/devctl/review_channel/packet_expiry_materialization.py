"""Write-side materialization for clock-expired review packets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import secrets

from .context_refs import normalize_context_pack_refs
from .event_models import ReviewChannelEventBundle
from .event_reducer import load_or_refresh_event_bundle, refresh_event_bundle
from .event_store import (
    ReviewChannelArtifactPaths,
    append_event,
    idempotency_key,
    load_events,
    next_event_id,
    parse_utc,
)
from .state import project_id_for_repo
from ..runtime.packet_transport_expiry import packet_uses_transport_expiry
from ..time_utils import utc_timestamp


@dataclass(frozen=True, slots=True)
class PacketExpiryMaterialization:
    """Summary of packet-expiry lifecycle events written by maintenance."""

    materialized_packet_count: int
    remaining_expired_pending_count: int
    packet_ids: tuple[str, ...]
    event_ids: tuple[str, ...]
    limit: int | None
    generated_at_utc: str
    schema_version: int = 1
    contract_id: str = "PacketExpiryMaterialization"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def materialize_expired_packet_events(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    limit: int | None = None,
) -> tuple[ReviewChannelEventBundle, PacketExpiryMaterialization]:
    """Append ``packet_expired`` events for stale pending packets.

    Read-only projections may classify clock-expired pending rows, but durable
    agent coordination needs an event-backed lifecycle transition. This helper
    is the bounded write-side maintenance path for that transition.
    """
    bundle = load_or_refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    events = load_events(Path(artifact_paths.event_log_path))
    candidates = _expired_pending_candidates(
        review_state=bundle.review_state,
        events=events,
        now=datetime.now(timezone.utc),
    )
    selected = candidates[:limit] if limit is not None and limit >= 0 else candidates

    written_events: list[dict[str, object]] = []
    event_log_path = Path(artifact_paths.event_log_path)
    for packet in selected:
        event = _packet_expired_event(
            packet=packet,
            events=events,
            repo_root=repo_root,
        )
        written = append_event(event_log_path, event, existing_events=events)
        events.append(written)
        written_events.append(written)

    if written_events:
        bundle = refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )

    materialization = PacketExpiryMaterialization(
        materialized_packet_count=len(written_events),
        remaining_expired_pending_count=max(len(candidates) - len(written_events), 0),
        packet_ids=tuple(_text(event.get("packet_id")) for event in written_events),
        event_ids=tuple(_text(event.get("event_id")) for event in written_events),
        limit=limit,
        generated_at_utc=utc_timestamp(),
    )
    return bundle, materialization


def _expired_pending_candidates(
    *,
    review_state: Mapping[str, object],
    events: list[dict[str, object]],
    now: datetime,
) -> list[dict[str, object]]:
    expired_event_packet_ids = _packet_ids_with_expiry_events(events)
    post_events = _packet_post_events(events)
    candidates: list[dict[str, object]] = []
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return candidates
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        packet_id = _text(packet.get("packet_id"))
        if not packet_id or packet_id in expired_event_packet_ids:
            continue
        if _text(packet.get("status")) != "pending":
            continue
        if not packet_uses_transport_expiry(packet):
            continue
        expires_at = parse_utc(_text(packet.get("expires_at_utc")))
        if expires_at is None or expires_at.astimezone(timezone.utc) > now:
            continue
        row = dict(packet)
        source_event = post_events.get(packet_id)
        if source_event is not None:
            row["_posted_event"] = dict(source_event)
        candidates.append(row)
    return candidates


def _packet_expired_event(
    *,
    packet: Mapping[str, object],
    events: list[dict[str, object]],
    repo_root: Path,
) -> dict[str, object]:
    source_event = packet.get("_posted_event")
    source = source_event if isinstance(source_event, Mapping) else packet
    packet_id = _text(packet.get("packet_id"))
    timestamp = utc_timestamp()
    return {
        "schema_version": 1,
        "event_id": next_event_id(events),
        "session_id": _text(source.get("session_id")),
        "project_id": _text(source.get("project_id")) or project_id_for_repo(repo_root),
        "packet_id": packet_id,
        "trace_id": _text(packet.get("trace_id") or source.get("trace_id")),
        "timestamp_utc": timestamp,
        "source": "review_channel",
        "plan_id": _text(source.get("plan_id")),
        "controller_run_id": source.get("controller_run_id"),
        "event_type": "packet_expired",
        "from_agent": packet.get("from_agent") or source.get("from_agent"),
        "to_agent": packet.get("to_agent") or source.get("to_agent"),
        "kind": packet.get("kind") or source.get("kind"),
        "summary": packet.get("summary") or source.get("summary"),
        "body": packet.get("body") or source.get("body"),
        "evidence_refs": list(packet.get("evidence_refs") or source.get("evidence_refs") or []),
        "guidance_refs": list(packet.get("guidance_refs") or source.get("guidance_refs") or []),
        "context_pack_refs": normalize_context_pack_refs(
            packet.get("context_pack_refs") or source.get("context_pack_refs")
        ),
        "confidence": float(packet.get("confidence") or source.get("confidence") or 0.0),
        "requested_action": packet.get("requested_action") or source.get("requested_action"),
        "policy_hint": packet.get("policy_hint") or source.get("policy_hint"),
        "approval_required": bool(
            packet.get("approval_required") or source.get("approval_required")
        ),
        "target_kind": packet.get("target_kind") or source.get("target_kind"),
        "target_ref": packet.get("target_ref") or source.get("target_ref"),
        "target_revision": packet.get("target_revision") or source.get("target_revision"),
        "target_role": packet.get("target_role") or source.get("target_role"),
        "target_session_id": packet.get("target_session_id") or source.get("target_session_id"),
        "anchor_refs": list(packet.get("anchor_refs") or source.get("anchor_refs") or []),
        "intake_ref": packet.get("intake_ref") or source.get("intake_ref"),
        "mutation_op": packet.get("mutation_op") or source.get("mutation_op"),
        "pipeline_generation": packet.get("pipeline_generation")
        or source.get("pipeline_generation"),
        "staged_snapshot_hash": packet.get("staged_snapshot_hash")
        or source.get("staged_snapshot_hash"),
        "guard_results_summary": packet.get("guard_results_summary")
        or source.get("guard_results_summary"),
        "full_guard_bundle_evidence": packet.get("full_guard_bundle_evidence")
        or source.get("full_guard_bundle_evidence"),
        "plan_proposal": packet.get("plan_proposal") or source.get("plan_proposal"),
        "semantic_zref": _text(packet.get("semantic_zref"))
        or _text(source.get("semantic_zref"))
        or f"packet:{packet_id}",
        "source_identity": _source_identity(packet) or _source_identity(source),
        "status": "expired",
        "idempotency_key": idempotency_key("packet_expired", packet_id),
        "nonce": secrets.token_hex(12),
        "expires_at_utc": packet.get("expires_at_utc") or source.get("expires_at_utc"),
        "metadata": {
            "actor": "system",
            "reason": "packet TTL elapsed before an explicit disposition event",
            "materialized_from_event_id": _text(source.get("event_id")),
            "materialized_at_utc": timestamp,
            "contract_id": "PacketExpiryMaterialization",
        },
    }


def _packet_ids_with_expiry_events(
    events: list[dict[str, object]],
) -> set[str]:
    return {
        _text(event.get("packet_id"))
        for event in events
        if _text(event.get("event_type")) == "packet_expired"
        and _text(event.get("packet_id"))
    }


def _packet_post_events(
    events: list[dict[str, object]],
) -> dict[str, dict[str, object]]:
    posts: dict[str, dict[str, object]] = {}
    for event in events:
        if _text(event.get("event_type")) != "packet_posted":
            continue
        packet_id = _text(event.get("packet_id"))
        if packet_id:
            posts[packet_id] = dict(event)
    return posts


def _source_identity(packet: Mapping[str, object]) -> dict[str, object]:
    raw = packet.get("source_identity")
    if not isinstance(raw, Mapping):
        return {}
    return {
        _text(key): _text(value)
        for key, value in raw.items()
        if _text(key) and _text(value)
    }


def _text(value: object) -> str:
    return str(value or "").strip()
