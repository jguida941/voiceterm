"""Plan-graph routing for review packets.

Packets are inputs to the typed plan graph.  They may carry evidence,
blockers, or plan proposals, but they are not executable plan rows unless
plan-intent ingestion materializes or amends a real ``PlanRow``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass

from .current_plan_authority import CurrentPlanAuthority, resolve_current_plan_authority

PLAN_PACKET_ROUTING_CONTRACT_ID = "PlanPacketRouting"
PLAN_PACKET_ROUTING_SCHEMA_VERSION = 1

PLAN_ROW_PRIORITY_AMENDMENT_PACKET_KIND = "plan_row_priority_amendment"

SAME_ROW_BLOCKER = "same_row_blocker"
UPSTREAM_CHANGE = "upstream_change"
FUTURE_ROW_NOTE = "future_row_note"
STALE_UNBOUND_COMMUNICATION = "stale_unbound_communication"
PLAN_AMENDMENT = "plan_amendment"

_PLAN_AMENDMENT_KINDS = frozenset(
    {
        "plan_gap_review",
        "plan_patch_review",
        "plan_ready_gate",
        PLAN_ROW_PRIORITY_AMENDMENT_PACKET_KIND,
    }
)
_PLAN_AMENDMENT_OPS = frozenset(
    {
        "append_acceptance_extension",
        "append_progress_log",
        "create_plan_row",
        "ingest_plan_intent",
        "plan_amendment",
        "plan_row_priority_amendment",
        "priority_amendment",
        "supersede_plan_row",
        "supersedes",
    }
)
_BLOCKING_KINDS = frozenset({"action_request", "approval_request", "commit_approval"})
_UPSTREAM_CHANGE_OPS = frozenset(
    {
        "invalidate_downstream",
        "mark_revalidation_required",
        "plan_revision_refresh",
        "revalidation_required",
        "upstream_change",
    }
)


@dataclass(frozen=True, slots=True)
class PlanPacketRouting:
    packet_id: str
    classification: str
    current_plan_row_id: str = ""
    target_plan_row_id: str = ""
    target_plan_row_status: str = ""
    scheduler_eligible: bool = False
    bind_as_plan_evidence: bool = True
    requires_plan_intake: bool = False
    reason: str = ""
    contract_id: str = PLAN_PACKET_ROUTING_CONTRACT_ID
    schema_version: int = PLAN_PACKET_ROUTING_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def classify_packet_for_plan_graph(
    packet: Mapping[str, object],
    plan_rows: Iterable[object],
    *,
    current_authority: CurrentPlanAuthority | None = None,
    authority_affecting: bool = False,
) -> PlanPacketRouting:
    """Classify one packet against the current executable plan row."""
    rows = tuple(plan_rows)
    authority = current_authority or resolve_current_plan_authority(rows)
    packet_id = _text(packet.get("packet_id"))
    kind = _text(packet.get("kind"))
    requested_action = _text(packet.get("requested_action"))
    mutation_op = _text(packet.get("mutation_op"))
    target_ref = _text(packet.get("target_ref")) or _text(packet.get("plan_id"))
    target_row = target_plan_row(packet, rows)
    target_row_id = _row_attr(target_row, "row_id") if target_row is not None else ""
    target_status = _row_attr(target_row, "status") if target_row is not None else ""

    if _is_plan_amendment(packet, kind=kind, requested_action=requested_action, mutation_op=mutation_op):
        return PlanPacketRouting(
            packet_id=packet_id,
            classification=PLAN_AMENDMENT,
            current_plan_row_id=authority.plan_row_id,
            target_plan_row_id=target_row_id,
            target_plan_row_status=target_status,
            scheduler_eligible=False,
            bind_as_plan_evidence=False,
            requires_plan_intake=True,
            reason="packet carries plan amendment/proposal; route through plan-intent ingestion",
        )

    if _is_upstream_change(requested_action=requested_action, mutation_op=mutation_op):
        return PlanPacketRouting(
            packet_id=packet_id,
            classification=UPSTREAM_CHANGE,
            current_plan_row_id=authority.plan_row_id,
            target_plan_row_id=target_row_id,
            target_plan_row_status=target_status,
            scheduler_eligible=False,
            bind_as_plan_evidence=True,
            reason="packet changes upstream plan assumptions; downstream rows require revalidation",
        )

    if target_row_id and target_row_id == authority.plan_row_id:
        return PlanPacketRouting(
            packet_id=packet_id,
            classification=SAME_ROW_BLOCKER,
            current_plan_row_id=authority.plan_row_id,
            target_plan_row_id=target_row_id,
            target_plan_row_status=target_status,
            scheduler_eligible=_is_blocking_packet(
                kind=kind,
                requested_action=requested_action,
                authority_affecting=authority_affecting,
            ),
            bind_as_plan_evidence=True,
            reason="packet targets the current executable PlanRow",
        )

    if target_row_id:
        return PlanPacketRouting(
            packet_id=packet_id,
            classification=FUTURE_ROW_NOTE,
            current_plan_row_id=authority.plan_row_id,
            target_plan_row_id=target_row_id,
            target_plan_row_status=target_status,
            scheduler_eligible=False,
            bind_as_plan_evidence=True,
            reason="packet targets a non-current PlanRow and is parked as evidence",
        )

    return PlanPacketRouting(
        packet_id=packet_id,
        classification=STALE_UNBOUND_COMMUNICATION,
        current_plan_row_id=authority.plan_row_id,
        target_plan_row_id="",
        target_plan_row_status="",
        scheduler_eligible=False,
        bind_as_plan_evidence=bool(target_ref),
        reason="packet is unbound to an executable PlanRow",
    )


def packet_can_drive_current_plan(
    packet: Mapping[str, object],
    plan_rows: Iterable[object],
    *,
    current_authority: CurrentPlanAuthority | None = None,
    authority_affecting: bool = False,
) -> tuple[bool, PlanPacketRouting]:
    """Return whether a packet may become scheduler/continuation work."""
    rows = tuple(plan_rows)
    authority = current_authority or resolve_current_plan_authority(rows)
    routing = classify_packet_for_plan_graph(
        packet,
        rows,
        current_authority=authority,
        authority_affecting=authority_affecting,
    )
    if not authority.has_executable_plan_row:
        return True, routing
    return (
        routing.scheduler_eligible
        and routing.target_plan_row_id == authority.plan_row_id,
        routing,
    )


def target_plan_row(
    packet: Mapping[str, object],
    plan_rows: Iterable[object],
) -> object | None:
    target_ref = _text(packet.get("target_ref")) or _text(packet.get("plan_id"))
    if not target_ref:
        return None
    normalized = _normalize_plan_ref(target_ref)
    rows = tuple(plan_rows)
    for row in rows:
        row_id = _row_attr(row, "row_id")
        if normalized and row_id == normalized:
            return row
        if target_ref in {row_id, f"plan:{row_id}"}:
            return row
    for row in rows:
        if target_ref and _row_attr(row, "target_ref") == target_ref:
            return row
    return None


def _is_plan_amendment(
    packet: Mapping[str, object],
    *,
    kind: str,
    requested_action: str,
    mutation_op: str,
) -> bool:
    if kind in _PLAN_AMENDMENT_KINDS:
        return True
    if requested_action in _PLAN_AMENDMENT_OPS or mutation_op in _PLAN_AMENDMENT_OPS:
        return True
    proposal = packet.get("plan_proposal")
    return isinstance(proposal, Mapping) and bool(proposal)


def _is_upstream_change(*, requested_action: str, mutation_op: str) -> bool:
    return requested_action in _UPSTREAM_CHANGE_OPS or mutation_op in _UPSTREAM_CHANGE_OPS


def _is_blocking_packet(
    *,
    kind: str,
    requested_action: str,
    authority_affecting: bool,
) -> bool:
    if authority_affecting:
        return True
    if requested_action == "review_only":
        return False
    return kind in _BLOCKING_KINDS or kind == "instruction"


def _normalize_plan_ref(value: str) -> str:
    text = _text(value)
    if text.startswith("plan:"):
        return text.removeprefix("plan:")
    return text


def _row_attr(row: object | None, attr: str) -> str:
    if row is None:
        return ""
    if isinstance(row, Mapping):
        value = row.get(attr, "")
    else:
        value = getattr(row, attr, "")
    return _text(value)


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "FUTURE_ROW_NOTE",
    "PLAN_AMENDMENT",
    "PLAN_PACKET_ROUTING_CONTRACT_ID",
    "PLAN_PACKET_ROUTING_SCHEMA_VERSION",
    "PLAN_ROW_PRIORITY_AMENDMENT_PACKET_KIND",
    "PlanPacketRouting",
    "SAME_ROW_BLOCKER",
    "STALE_UNBOUND_COMMUNICATION",
    "UPSTREAM_CHANGE",
    "classify_packet_for_plan_graph",
    "packet_can_drive_current_plan",
    "target_plan_row",
]
