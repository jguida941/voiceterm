"""Inbox/history query helpers for reduced event-backed review state."""

from __future__ import annotations

from datetime import datetime, timezone

from ..runtime.review_packet_inbox_liveness import is_expired_unresolved

from .event_models import event_id_rank
from .pending_packets import live_pending_packets, partition_live_packet_queue
from .packet_body_observation import packet_body_digest, packet_body_observed_by
from .packet_route_scope import normalize_packet_route_role
from .packet_text_fields import clean_optional_text
from .timestamp_parse import parse_utc_value as _parse_utc


# A19 stale-packet hygiene window (delete_after_ingest.md lines 1746-1830).
# Pending packets older than this without an explicit --include-stale opt-in
# are filtered from the default inbox view per amendment requirement that
# "default lane view reflects only actionable items."
A19_DEFAULT_HYGIENE_WINDOW_SECONDS = 24 * 60 * 60


def filter_inbox_packets(
    review_state: dict[str, object],
    *,
    target: str | None = None,
    target_role: str | None = None,
    target_session_id: str | None = None,
    status: str | None = None,
    limit: int | None = None,
    include_stale: bool = False,
    hygiene_window_seconds: int = A19_DEFAULT_HYGIENE_WINDOW_SECONDS,
    now_utc: datetime | None = None,
) -> list[dict[str, object]]:
    """Filter the reduced packet list into one target/status inbox view.

    When filtering by status=pending, expired packets are excluded so the
    inbox matches pending_total, per-agent counts, and derived_next_instruction.

    Per A19 (delete_after_ingest.md lines 1746-1830), when ``include_stale``
    is ``False`` (the default), pending packets older than
    ``hygiene_window_seconds`` are also filtered out so the default lane
    view reflects only actionable items. Pass ``--include-stale`` on the
    CLI to surface the full backlog.
    """
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return []
    filtered = []
    packet_iter = (
        _inbox_pending_packets(
            packets,
            target=target,
            include_stale=include_stale,
            hygiene_window_seconds=hygiene_window_seconds,
            now_utc=now_utc,
        )
        if status == "pending"
        else (packet for packet in packets if isinstance(packet, dict))
    )
    for packet in packet_iter:
        if target and packet.get("to_agent") != target:
            continue
        if target_role or target_session_id:
            if not _packet_has_route_scope(packet):
                continue
            if not _packet_matches_inbox_scope(
                packet,
                target_role=target_role,
                target_session_id=target_session_id,
            ):
                if not target or not _should_surface_route_mismatch(
                    packet,
                    target_role=target_role,
                ):
                    continue
                filtered.append(
                    _with_inbox_routing_status(
                        packet,
                        target_role=target_role,
                        target_session_id=target_session_id,
                    )
                )
                continue
        if status and not _packet_matches_inbox_status(packet, status):
            continue
        filtered.append(
            _with_inbox_routing_status(
                packet,
                target_role=target_role,
                target_session_id=target_session_id,
            )
        )
    if limit is not None and limit >= 0:
        return filtered[:limit]
    return filtered


def filter_history_packets(
    review_state: dict[str, object],
    *,
    target: str | None = None,
    packet_id: str | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Filter the reduced packet list into one packet-history view."""
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return []
    requested_packet_id = str(packet_id or "").strip()
    if requested_packet_id:
        packet = packet_by_id(review_state, requested_packet_id)
        if packet is None:
            return []
        if target and packet.get("to_agent") != target:
            return []
        return [packet]
    _, history_packets, _ = partition_live_packet_queue(
        packet for packet in packets if isinstance(packet, dict)
    )
    filtered = []
    for packet in history_packets:
        if not isinstance(packet, dict):
            continue
        if target and packet.get("to_agent") != target:
            continue
        filtered.append(packet)
    if limit is not None and limit >= 0:
        return filtered[:limit]
    return filtered


def filter_history_events(
    events: list[dict[str, object]],
    *,
    trace_id: str | None = None,
    packet_id: str | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Filter the append-only event log into one history view."""
    requested_packet_id = str(packet_id or "").strip()
    filtered = [
        event
        for event in events
        if not trace_id or event.get("trace_id") == trace_id
        if not requested_packet_id or event.get("packet_id") == requested_packet_id
    ]
    if limit is not None and limit >= 0:
        return filtered[-limit:]
    return filtered


def packet_by_id(
    review_state: dict[str, object],
    packet_id: str,
) -> dict[str, object] | None:
    """Look up one packet in the reduced state."""
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return None
    for packet in packets:
        if isinstance(packet, dict) and packet.get("packet_id") == packet_id:
            return packet
    return None


def _inbox_pending_packets(
    packets: object,
    *,
    target: str | None,
    include_stale: bool = False,
    hygiene_window_seconds: int = A19_DEFAULT_HYGIENE_WINDOW_SECONDS,
    now_utc: datetime | None = None,
) -> tuple[dict[str, object], ...]:
    """Return route-scoped live pending packets, freshest first.

    v4.55.4 (rev_pkt_4786/4787): sort by ``latest_event_id`` descending so
    plan-bound packets named by `develop next` surface at the top of the
    inbox view instead of being buried under old transport debt.
    `live_pending_packets` itself preserves insertion order (audit
    determinism); freshness ordering is layered on at the inbox boundary
    so other consumers retain insertion order.

    A19 (delete_after_ingest.md 1746-1830): when ``include_stale`` is
    False, also filter out pending packets whose ``posted_at`` is older
    than ``hygiene_window_seconds``. This implements the amendment's
    requirement that "default lane view reflects only actionable items"
    without dropping the underlying packet rows (they are still visible
    with ``--include-stale``).
    """
    packet_rows = tuple(packet for packet in packets if isinstance(packet, dict))
    live_rows = tuple(
        packet for packet in live_pending_packets(packet_rows)
        if isinstance(packet, dict)
    )
    if not include_stale:
        live_rows = _drop_packets_past_hygiene_window(
            live_rows,
            hygiene_window_seconds=hygiene_window_seconds,
            now_utc=now_utc,
        )
    live_ids = {
        str(packet.get("packet_id") or "").strip()
        for packet in live_rows
    }
    if not target:
        return _sort_inbox_packets_freshest_first(live_rows)
    routed_rows = tuple(
        packet
        for packet in packet_rows
        if str(packet.get("packet_id") or "").strip() not in live_ids
        and _route_scoped_actor_packet_still_requires_read(packet, target=target)
    )
    if not include_stale:
        routed_rows = _drop_packets_past_hygiene_window(
            routed_rows,
            hygiene_window_seconds=hygiene_window_seconds,
            now_utc=now_utc,
        )
    combined = (*live_rows, *routed_rows)
    return _sort_inbox_packets_freshest_first(combined)


def _drop_packets_past_hygiene_window(
    packets: tuple[dict[str, object], ...],
    *,
    hygiene_window_seconds: int,
    now_utc: datetime | None,
) -> tuple[dict[str, object], ...]:
    """Return packets posted within ``hygiene_window_seconds`` of now.

    Packets with missing or unparseable ``posted_at`` are kept (we cannot
    prove staleness without a timestamp, and dropping them would hide
    legitimate work). Negative ages also fall through unchanged.
    """
    if hygiene_window_seconds <= 0:
        return packets
    now = now_utc if now_utc is not None else datetime.now(tz=timezone.utc)
    kept: list[dict[str, object]] = []
    for packet in packets:
        raw_posted = str(packet.get("posted_at") or "").strip()
        if not raw_posted:
            kept.append(packet)
            continue
        posted_at = _parse_utc(raw_posted)
        if posted_at is None:
            kept.append(packet)
            continue
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        age_seconds = (now - posted_at).total_seconds()
        if age_seconds < 0 or age_seconds <= hygiene_window_seconds:
            kept.append(packet)
    return tuple(kept)


def _sort_inbox_packets_freshest_first(
    packets: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    """Sort inbox packets so the highest ``latest_event_id`` ranks first.

    Uses ``event_id_rank`` (same comparator the agent-loop attention
    selector consumes) so the inbox and ``develop next`` agree on which
    packet is current. Packets without a parseable ``latest_event_id``
    sort last but keep stable relative order.
    """
    return tuple(
        sorted(
            packets,
            key=lambda packet: event_id_rank(
                str(packet.get("latest_event_id") or "").strip()
            ),
            reverse=True,
        )
    )


def _route_scoped_actor_packet_still_requires_read(
    packet: dict[str, object],
    *,
    target: str,
) -> bool:
    if clean_optional_text(packet.get("to_agent")) != clean_optional_text(target):
        return False
    if packet.get("status") != "pending":
        return False
    if is_expired_unresolved(packet):
        return False
    if not (packet.get("target_role") or packet.get("target_session_id")):
        return False
    digest = packet_body_digest(packet)
    if not digest:
        return True
    return not packet_body_observed_by(
        packet,
        actor=clean_optional_text(target) or "",
        body_digest=digest,
    )


def _with_inbox_routing_status(
    packet: dict[str, object],
    *,
    target_role: str | None,
    target_session_id: str | None,
) -> dict[str, object]:
    scope_role = normalize_packet_route_role(target_role)
    scope_session = clean_optional_text(target_session_id) or ""
    packet_role = normalize_packet_route_role(packet.get("target_role"))
    packet_session = clean_optional_text(packet.get("target_session_id")) or ""
    if scope_role and packet_role and packet_role != scope_role:
        annotated = dict(packet)
        annotated["inbox_routing_status"] = "wrong_role_for_actor"
        annotated["inbox_routing_expected_role"] = scope_role
        annotated["inbox_routing_packet_role"] = packet_role
        return annotated
    if scope_session and packet_session and packet_session != scope_session:
        annotated = dict(packet)
        annotated["inbox_routing_status"] = "wrong_session_for_actor"
        annotated["inbox_routing_expected_session_id"] = scope_session
        annotated["inbox_routing_packet_session_id"] = packet_session
        return annotated
    if packet_role or packet_session:
        annotated = dict(packet)
        annotated["inbox_routing_status"] = "route_scoped_to_actor"
        return annotated
    return packet


def _should_surface_route_mismatch(
    packet: dict[str, object],
    *,
    target_role: str | None,
) -> bool:
    scope_role = normalize_packet_route_role(target_role)
    packet_role = normalize_packet_route_role(packet.get("target_role"))
    return bool(scope_role and packet_role and packet_role != scope_role)


def _packet_matches_inbox_status(packet: dict[str, object], status: str) -> bool:
    if status == "expired":
        return is_expired_unresolved(packet)
    return packet.get("status") == status


def _packet_has_route_scope(packet: dict[str, object]) -> bool:
    return bool(packet.get("target_role") or packet.get("target_session_id"))


def _packet_matches_inbox_scope(
    packet: dict[str, object],
    *,
    target_role: str | None,
    target_session_id: str | None,
) -> bool:
    """Return whether a packet is visible in one typed role/session inbox.

    Visibility is intentionally broader than consumption authority. A role-only
    query must surface session-pinned packets for that role so a lane watcher or
    operator can discover pending work without knowing the elected session id in
    advance. A session-specific query remains exact for packets pinned only by
    session.
    """
    scope_role = normalize_packet_route_role(target_role)
    scope_session = clean_optional_text(target_session_id) or ""
    packet_role = normalize_packet_route_role(packet.get("target_role"))
    packet_session = clean_optional_text(packet.get("target_session_id")) or ""

    if scope_role:
        if packet_role != scope_role:
            return False
        return not scope_session or not packet_session or packet_session == scope_session
    if scope_session:
        return packet_session == scope_session
    return False
