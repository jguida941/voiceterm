"""Goal-progress receipt evidence derived from review-channel packets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from .collaboration_packet_kinds import GOAL_PROGRESS_PACKET_KIND
from .session_termination_policy import CONTINUATION_ANCHOR_PACKET_KIND
from .value_coercion import coerce_int, coerce_mapping, coerce_string


GOAL_PROGRESS_RECEIPT_CONTRACT_ID = "GoalProgressReceipt"
GOAL_PROGRESS_RECEIPT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class GoalProgressReceipt:
    """Operator-visible progress toward a continuation goal."""

    schema_version: int = GOAL_PROGRESS_RECEIPT_SCHEMA_VERSION
    contract_id: str = GOAL_PROGRESS_RECEIPT_CONTRACT_ID
    actor_id: str = ""
    continuation_goal: str = ""
    continuation_anchor_packet_id: str = ""
    latest_progress_packet_id: str = ""
    plan_row_id: str = ""
    completed_units: int = 0
    total_units: int = 0
    progress_percentage_toward_goal: int = 0
    status: str = "missing"
    updated_at_utc: str = ""
    summary: str = ""
    evidence_refs: tuple[str, ...] = ()
    packet_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        payload["packet_refs"] = list(self.packet_refs)
        return payload


def resolve_goal_progress_receipt(
    review_state: Mapping[str, object] | None,
    *,
    actor: str,
    continuation_goal: str = "",
) -> GoalProgressReceipt:
    """Resolve the newest goal_progress receipt for one actor and goal."""
    state = coerce_mapping(review_state)
    actor_id = coerce_string(actor)
    goal = coerce_string(continuation_goal)
    anchor = _latest_continuation_anchor(state, actor_id=actor_id)
    anchor_id = coerce_string(anchor.get("packet_id"))
    match_tokens = _match_tokens(goal=goal, anchor_id=anchor_id)
    progress_packet = _latest_goal_progress_packet(
        state,
        actor_id=actor_id,
        match_tokens=match_tokens,
    )
    base = {
        "actor_id": actor_id,
        "continuation_goal": goal or anchor_id,
        "continuation_anchor_packet_id": anchor_id,
    }
    if not progress_packet:
        return GoalProgressReceipt(
            **base,
            status="missing",
            summary="No matching goal_progress packet has been posted.",
        )

    completed, total, percentage = _progress_values(progress_packet)
    if percentage < 0:
        return GoalProgressReceipt(
            **base,
            latest_progress_packet_id=coerce_string(progress_packet.get("packet_id")),
            plan_row_id=_plan_row_id(progress_packet),
            status="invalid_progress",
            updated_at_utc=_packet_time(progress_packet),
            summary="goal_progress packet did not carry parseable progress evidence.",
            evidence_refs=_evidence_refs(progress_packet),
            packet_refs=_packet_refs(progress_packet),
        )
    status = "complete" if percentage >= 100 else "in_progress"
    return GoalProgressReceipt(
        **base,
        latest_progress_packet_id=coerce_string(progress_packet.get("packet_id")),
        plan_row_id=_plan_row_id(progress_packet),
        completed_units=completed,
        total_units=total,
        progress_percentage_toward_goal=percentage,
        status=status,
        updated_at_utc=_packet_time(progress_packet),
        summary=f"Goal progress is {percentage}% toward {goal or anchor_id}.",
        evidence_refs=_evidence_refs(progress_packet),
        packet_refs=_packet_refs(progress_packet),
    )


def goal_progress_receipt_from_mapping(payload: Mapping[str, object]) -> GoalProgressReceipt:
    """Normalize a mapping into a GoalProgressReceipt."""
    mapping = coerce_mapping(payload)
    return GoalProgressReceipt(
        schema_version=coerce_int(mapping.get("schema_version"))
        or GOAL_PROGRESS_RECEIPT_SCHEMA_VERSION,
        contract_id=coerce_string(mapping.get("contract_id"))
        or GOAL_PROGRESS_RECEIPT_CONTRACT_ID,
        actor_id=coerce_string(mapping.get("actor_id")),
        continuation_goal=coerce_string(mapping.get("continuation_goal")),
        continuation_anchor_packet_id=coerce_string(
            mapping.get("continuation_anchor_packet_id")
        ),
        latest_progress_packet_id=coerce_string(mapping.get("latest_progress_packet_id")),
        plan_row_id=coerce_string(mapping.get("plan_row_id")),
        completed_units=coerce_int(mapping.get("completed_units")),
        total_units=coerce_int(mapping.get("total_units")),
        progress_percentage_toward_goal=coerce_int(
            mapping.get("progress_percentage_toward_goal")
        ),
        status=coerce_string(mapping.get("status")) or "missing",
        updated_at_utc=coerce_string(mapping.get("updated_at_utc")),
        summary=coerce_string(mapping.get("summary")),
        evidence_refs=_string_items(mapping.get("evidence_refs")),
        packet_refs=_string_items(mapping.get("packet_refs")),
    )


def _latest_continuation_anchor(
    review_state: Mapping[str, object],
    *,
    actor_id: str,
) -> Mapping[str, object]:
    candidates = [
        packet
        for packet in _packet_rows(review_state)
        if coerce_string(packet.get("kind")) == CONTINUATION_ANCHOR_PACKET_KIND
        and _active(packet)
        and _actor_matches(packet, actor_id=actor_id)
    ]
    return _latest_packet(candidates)


def _latest_goal_progress_packet(
    review_state: Mapping[str, object],
    *,
    actor_id: str,
    match_tokens: tuple[str, ...],
) -> Mapping[str, object]:
    candidates = [
        packet
        for packet in _packet_rows(review_state)
        if coerce_string(packet.get("kind")) == GOAL_PROGRESS_PACKET_KIND
        and _active(packet)
        and coerce_string(packet.get("from_agent")) == actor_id
        and _matches_goal(packet, match_tokens=match_tokens)
    ]
    return _latest_packet(candidates)


def _matches_goal(
    packet: Mapping[str, object],
    *,
    match_tokens: tuple[str, ...],
) -> bool:
    if not match_tokens:
        return True
    values = {
        coerce_string(packet.get("target_ref")),
        *_anchor_refs(packet),
        *_evidence_refs(packet),
    }
    return bool(values & set(match_tokens))


def _progress_values(packet: Mapping[str, object]) -> tuple[int, int, int]:
    for ref in _evidence_refs(packet):
        prefix, _, value = ref.partition(":")
        if prefix in {"goal_progress", "progress"}:
            completed, total = _ratio(value)
            if total > 0:
                return completed, total, min(100, max(0, round(completed * 100 / total)))
        if prefix in {"progress_percentage", "progress_percent"}:
            percentage = coerce_int(value)
            return 0, 0, min(100, max(0, percentage))
    return 0, 0, -1


def _ratio(value: str) -> tuple[int, int]:
    left, sep, right = value.partition("/")
    if not sep:
        return 0, 0
    return coerce_int(left), coerce_int(right)


def _packet_rows(review_state: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows = review_state.get("packets")
    if not isinstance(rows, (list, tuple)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _latest_packet(packets: list[Mapping[str, object]]) -> Mapping[str, object]:
    if not packets:
        return {}
    return sorted(
        packets,
        key=lambda packet: (
            _event_rank(coerce_string(packet.get("latest_event_id"))),
            coerce_string(packet.get("posted_at")),
            coerce_string(packet.get("packet_id")),
        ),
    )[-1]


def _actor_matches(packet: Mapping[str, object], *, actor_id: str) -> bool:
    if not actor_id:
        return True
    return actor_id in {
        coerce_string(packet.get("from_agent")),
        coerce_string(packet.get("to_agent")),
    }


def _active(packet: Mapping[str, object]) -> bool:
    status = coerce_string(packet.get("status"))
    lifecycle = coerce_string(packet.get("lifecycle_current_state"))
    return status in {"", "pending", "acked", "acknowledged"} and lifecycle not in {
        "applied",
        "dismissed",
        "expired",
        "archived",
    }


def _match_tokens(*, goal: str, anchor_id: str) -> tuple[str, ...]:
    values = []
    for value in (goal, anchor_id):
        token = coerce_string(value)
        if not token:
            continue
        values.extend([token, f"packet:{token}"])
    return tuple(dict.fromkeys(values))


def _plan_row_id(packet: Mapping[str, object]) -> str:
    for ref in _anchor_refs(packet):
        prefix, _, value = ref.partition(":")
        if prefix in {"section", "checklist", "progress"}:
            return value
    return ""


def _packet_time(packet: Mapping[str, object]) -> str:
    return coerce_string(packet.get("posted_at")) or coerce_string(
        packet.get("timestamp_utc")
    )


def _packet_refs(packet: Mapping[str, object]) -> tuple[str, ...]:
    packet_id = coerce_string(packet.get("packet_id"))
    return (f"packet:{packet_id}",) if packet_id else ()


def _anchor_refs(packet: Mapping[str, object]) -> tuple[str, ...]:
    return _string_items(packet.get("anchor_refs"))


def _evidence_refs(packet: Mapping[str, object]) -> tuple[str, ...]:
    return _string_items(packet.get("evidence_refs"))


def _string_items(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(coerce_string(item) for item in value if coerce_string(item))


def _event_rank(event_id: str) -> int:
    if not event_id.startswith("rev_evt_"):
        return -1
    try:
        return int(event_id.removeprefix("rev_evt_"))
    except ValueError:
        return -1


__all__ = [
    "GOAL_PROGRESS_RECEIPT_CONTRACT_ID",
    "GOAL_PROGRESS_RECEIPT_SCHEMA_VERSION",
    "GoalProgressReceipt",
    "goal_progress_receipt_from_mapping",
    "resolve_goal_progress_receipt",
]
