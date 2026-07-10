"""Typed pre-decision composability window evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

from .collaboration_packet_kinds import (
    REVIEW_ACCEPTED_PACKET_KIND,
    TASK_STARTED_PACKET_KIND,
)
from .value_coercion import coerce_int as _int
from .value_coercion import coerce_string as _text


CONTRACT_ID = "PreDecisionComposabilityWindow"
SCHEMA_VERSION = 1
DEFAULT_PRE_DECISION_WINDOW_SECONDS = 900
MIN_COMPOSABILITY_ANCHORS = 3
PRE_DECISION_ACK_TOKEN = "pre_decision_ack"
PRE_DECISION_OBJECTION_TOKEN = "pre_decision_objection"
_TERMINAL_STATUSES = frozenset({"applied", "dismissed", "expired", "archived"})


@dataclass(frozen=True, slots=True)
class PreDecisionComposabilityWindow:
    contract_id: str = CONTRACT_ID
    schema_version: int = SCHEMA_VERSION
    actor_id: str = ""
    reviewer_id: str = ""
    plan_row_id: str = ""
    task_started_packet_id: str = ""
    ack_packet_id: str = ""
    objection_packet_id: str = ""
    opened_at_utc: str = ""
    closes_at_utc: str = ""
    window_seconds: int = DEFAULT_PRE_DECISION_WINDOW_SECONDS
    composability_anchors: tuple[str, ...] = ()
    duplicate_hunt_ref: str = ""
    status: str = "missing"
    commit_blocked: bool = True
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["composability_anchors"] = list(self.composability_anchors)
        return payload


def resolve_pre_decision_window(
    review_state: Mapping[str, object],
    *,
    actor: str,
    reviewer: str,
    plan_row_id: str,
    now_utc: str = "",
    window_seconds: int = DEFAULT_PRE_DECISION_WINDOW_SECONDS,
) -> PreDecisionComposabilityWindow:
    """Resolve the pre-decision window for one actor/reviewer/plan row."""
    actor_id = _text(actor)
    reviewer_id = _text(reviewer)
    row_id = _text(plan_row_id)
    window = max(0, _int(window_seconds) or DEFAULT_PRE_DECISION_WINDOW_SECONDS)
    base = {
        "actor_id": actor_id,
        "reviewer_id": reviewer_id,
        "plan_row_id": row_id,
        "window_seconds": window,
    }
    if not actor_id or not reviewer_id or not row_id:
        return PreDecisionComposabilityWindow(
            **base,
            status="missing_scope",
            commit_blocked=True,
            summary="actor, reviewer, and plan_row_id are required",
        )

    task_started = _latest_task_started(
        review_state,
        actor=actor_id,
        reviewer=reviewer_id,
        plan_row_id=row_id,
    )
    if not task_started:
        return PreDecisionComposabilityWindow(
            **base,
            status="missing_task_started",
            commit_blocked=True,
            summary="task_started pre-decision packet missing",
        )

    task_packet_id = _text(task_started.get("packet_id"))
    anchors = _anchor_refs(task_started)
    duplicate_hunt_ref = _duplicate_hunt_ref(task_started)
    opened_at = _packet_time(task_started)
    closes_at = _window_closes_at(opened_at, window)
    evidence = {
        **base,
        "task_started_packet_id": task_packet_id,
        "opened_at_utc": opened_at,
        "closes_at_utc": closes_at,
        "composability_anchors": anchors,
        "duplicate_hunt_ref": duplicate_hunt_ref,
    }
    if len(anchors) < MIN_COMPOSABILITY_ANCHORS:
        return PreDecisionComposabilityWindow(
            **evidence,
            status="invalid_missing_composability_anchors",
            commit_blocked=True,
            summary="task_started packet must cite at least three composability anchors",
        )
    if not duplicate_hunt_ref:
        return PreDecisionComposabilityWindow(
            **evidence,
            status="invalid_missing_duplicate_hunt",
            commit_blocked=True,
            summary="task_started packet must carry duplicate_hunt evidence",
        )

    objection = _latest_response_packet(
        review_state,
        from_agent=reviewer_id,
        to_agent=actor_id,
        task_packet_id=task_packet_id,
        predicate=_is_objection_packet,
    )
    if objection:
        return PreDecisionComposabilityWindow(
            **evidence,
            objection_packet_id=_text(objection.get("packet_id")),
            status="blocked_by_objection",
            commit_blocked=True,
            summary="reviewer posted pre_decision_objection evidence",
        )

    ack = _latest_response_packet(
        review_state,
        from_agent=reviewer_id,
        to_agent=actor_id,
        task_packet_id=task_packet_id,
        predicate=_is_ack_packet,
    )
    if ack:
        return PreDecisionComposabilityWindow(
            **evidence,
            ack_packet_id=_text(ack.get("packet_id")),
            status="acknowledged",
            commit_blocked=False,
            summary="reviewer acknowledged the pre-decision window",
        )

    if _window_open(closes_at, now_utc=now_utc):
        return PreDecisionComposabilityWindow(
            **evidence,
            status="open_waiting_for_reviewer",
            commit_blocked=True,
            summary="pre-decision window is open and waiting for reviewer response",
        )

    return PreDecisionComposabilityWindow(
        **evidence,
        status="elapsed_without_objection",
        commit_blocked=False,
        summary="pre-decision window elapsed without reviewer objection",
    )


def _latest_task_started(
    review_state: Mapping[str, object],
    *,
    actor: str,
    reviewer: str,
    plan_row_id: str,
) -> Mapping[str, object]:
    candidates = [
        packet
        for packet in _packet_rows(review_state)
        if _text(packet.get("kind")) == TASK_STARTED_PACKET_KIND
        and _text(packet.get("from_agent")) == actor
        and _text(packet.get("to_agent")) == reviewer
        and _packet_matches_plan_row(packet, plan_row_id)
        and not _packet_resolved(packet)
    ]
    return _latest_by_event_id(candidates)


def _latest_response_packet(
    review_state: Mapping[str, object],
    *,
    from_agent: str,
    to_agent: str,
    task_packet_id: str,
    predicate,
) -> Mapping[str, object]:
    anchor = f"packet:{task_packet_id}" if task_packet_id else ""
    candidates = [
        packet
        for packet in _packet_rows(review_state)
        if _text(packet.get("from_agent")) == from_agent
        and _text(packet.get("to_agent")) == to_agent
        and (not anchor or anchor in _anchor_refs(packet))
        and predicate(packet)
        and not _packet_resolved(packet)
    ]
    return _latest_by_event_id(candidates)


def _packet_rows(review_state: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows = review_state.get("packets")
    if not isinstance(rows, (list, tuple)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _packet_matches_plan_row(packet: Mapping[str, object], plan_row_id: str) -> bool:
    refs = {
        _text(packet.get("target_ref")),
        *(_anchor_refs(packet)),
    }
    plan_refs = {
        plan_row_id,
        f"section:{plan_row_id}",
        f"checklist:{plan_row_id}",
        f"progress:{plan_row_id}",
        f"audit:{plan_row_id}",
    }
    return bool(refs & plan_refs)


def _is_ack_packet(packet: Mapping[str, object]) -> bool:
    kind = _text(packet.get("kind"))
    if kind == REVIEW_ACCEPTED_PACKET_KIND:
        return True
    return PRE_DECISION_ACK_TOKEN in _packet_text_blob(packet)


def _is_objection_packet(packet: Mapping[str, object]) -> bool:
    return PRE_DECISION_OBJECTION_TOKEN in _packet_text_blob(packet)


def _packet_text_blob(packet: Mapping[str, object]) -> str:
    values = [
        _text(packet.get("kind")),
        _text(packet.get("summary")),
        _text(packet.get("body")),
        _text(packet.get("target_ref")),
        *(_anchor_refs(packet)),
        *(_evidence_refs(packet)),
    ]
    return " ".join(values).lower()


def _anchor_refs(packet: Mapping[str, object]) -> tuple[str, ...]:
    refs = packet.get("anchor_refs")
    if not isinstance(refs, (list, tuple)):
        return ()
    return tuple(_text(ref) for ref in refs if _text(ref))


def _evidence_refs(packet: Mapping[str, object]) -> tuple[str, ...]:
    refs = packet.get("evidence_refs")
    if not isinstance(refs, (list, tuple)):
        return ()
    return tuple(_text(ref) for ref in refs if _text(ref))


def _duplicate_hunt_ref(packet: Mapping[str, object]) -> str:
    for ref in _evidence_refs(packet):
        lowered = ref.lower()
        if lowered.startswith("duplicate_hunt:") or lowered.startswith("duplicate-hunt:"):
            return ref
    return ""


def _latest_by_event_id(
    packets: list[Mapping[str, object]],
) -> Mapping[str, object]:
    if not packets:
        return {}
    return sorted(
        packets,
        key=lambda packet: (
            _event_rank(_text(packet.get("latest_event_id"))),
            _text(packet.get("posted_at")),
            _text(packet.get("packet_id")),
        ),
    )[-1]


def _packet_resolved(packet: Mapping[str, object]) -> bool:
    status = _text(packet.get("status"))
    lifecycle = _text(packet.get("lifecycle_current_state"))
    return status in _TERMINAL_STATUSES or lifecycle in _TERMINAL_STATUSES


def _packet_time(packet: Mapping[str, object]) -> str:
    return _text(packet.get("posted_at")) or _text(packet.get("timestamp_utc"))


def _window_closes_at(opened_at: str, window_seconds: int) -> str:
    opened = _parse_utc(opened_at)
    if opened is None:
        return ""
    return _format_utc(opened + timedelta(seconds=window_seconds))


def _window_open(closes_at: str, *, now_utc: str) -> bool:
    close_time = _parse_utc(closes_at)
    now = _parse_utc(now_utc) or datetime.now(UTC)
    if close_time is None:
        return True
    return now < close_time


def _event_rank(event_id: str) -> int:
    if not event_id.startswith("rev_evt_"):
        return -1
    try:
        return int(event_id.removeprefix("rev_evt_"))
    except ValueError:
        return -1


def _parse_utc(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = [
    "CONTRACT_ID",
    "DEFAULT_PRE_DECISION_WINDOW_SECONDS",
    "MIN_COMPOSABILITY_ANCHORS",
    "PRE_DECISION_ACK_TOKEN",
    "PRE_DECISION_OBJECTION_TOKEN",
    "PreDecisionComposabilityWindow",
    "resolve_pre_decision_window",
]
