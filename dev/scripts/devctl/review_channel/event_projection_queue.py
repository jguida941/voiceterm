"""Queue-derivation helpers for event-backed review-state projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from .event_projection_context import (
    append_event_instruction_context,
    build_event_context_packet,
    build_instruction_source,
)
from .packet_control_loop import (
    format_priority_instruction,
    latest_failed_action_request,
    select_priority_pending_packet,
)
from ..runtime.instruction_authority import (
    InstructionPriorityDecision,
    packet_instruction_provenance,
)
from ..runtime.review_state_models import ReviewQueueState
from ..time_utils import utc_timestamp
from .action_request_delivery import attach_action_request_delivery_receipts

_PENDING_QUEUE_PROVIDERS = ("codex", "claude", "cursor", "operator")
_EVENT_LOG_REL = "dev/reports/review_channel/events/trace.ndjson"


def derive_event_next_instruction(packets: list[dict[str, object]]) -> str:
    return derive_event_next_instruction_bundle(packets)[0]


def derive_event_next_instruction_bundle(
    packets: list[dict[str, object]],
    *,
    build_event_context_packet_fn=build_event_context_packet,
    append_event_instruction_context_fn=append_event_instruction_context,
    build_instruction_source_fn=build_instruction_source,
) -> tuple[str, dict[str, object]]:
    packet, control_metadata = select_priority_pending_packet(packets)
    if packet is not None:
        summary = format_priority_instruction(
            str(packet.get("summary") or ""),
            selection_policy=str(control_metadata.get("selection_policy") or ""),
        )
        if summary:
            context_packet = None
            if str(packet.get("kind") or "").strip() != "action_request":
                context_packet = build_event_context_packet_fn(packet)
            instruction = append_event_instruction_context_fn(summary, context_packet)
            source = build_instruction_source_fn(packet, context_packet)
            source.update(control_metadata)
            provenance = packet_instruction_provenance(
                packet,
                event_log_rel=_EVENT_LOG_REL,
            )
            source["provenance"] = provenance.to_dict()
            source["priority_decision"] = _priority_decision_for_packet(
                packet,
                packets,
                rule_id=str(control_metadata.get("selection_policy") or ""),
            ).to_dict()
            return instruction, source
    return "", {}


def derive_event_next_instruction_source(
    packets: list[dict[str, object]],
    **kwargs,
) -> dict[str, object]:
    return derive_event_next_instruction_bundle(packets, **kwargs)[1]


def build_event_queue_summary(
    pending_counts: dict[str, int],
    stale_packet_count: int,
    *,
    packets: list[dict[str, object]],
    build_event_context_packet_fn=build_event_context_packet,
    append_event_instruction_context_fn=append_event_instruction_context,
    build_instruction_source_fn=build_instruction_source,
) -> dict[str, object]:
    """Build the event-backed queue summary plus derived next-step hint."""
    derived_instruction, derived_source = derive_event_next_instruction_bundle(
        packets,
        build_event_context_packet_fn=build_event_context_packet_fn,
        append_event_instruction_context_fn=append_event_instruction_context_fn,
        build_instruction_source_fn=build_instruction_source_fn,
    )
    summary: dict[str, object] = {
        "pending_total": sum(pending_counts.values()),
        "derived_next_instruction": derived_instruction,
        "derived_next_instruction_source": derived_source,
        "instruction_priority_decision": _queue_priority_decision(derived_source),
        "last_failed_action_request": _failed_action_request_summary(packets),
    }
    for provider, count in pending_counts.items():
        summary[f"pending_{provider}"] = count
    summary["stale_packet_count"] = stale_packet_count
    return summary


def build_event_queue_state(
    pending_counts: dict[str, int],
    stale_packet_count: int,
    packet_rows: list[dict[str, object]],
    *,
    build_event_context_packet_fn=build_event_context_packet,
    append_event_instruction_context_fn=append_event_instruction_context,
    build_instruction_source_fn=build_instruction_source,
) -> ReviewQueueState:
    """Build a typed ReviewQueueState from event reduction outputs."""
    derived_instruction, derived_source = derive_event_next_instruction_bundle(
        packet_rows,
        build_event_context_packet_fn=build_event_context_packet_fn,
        append_event_instruction_context_fn=append_event_instruction_context_fn,
        build_instruction_source_fn=build_instruction_source_fn,
    )
    return ReviewQueueState(
        pending_total=sum(pending_counts.values()),
        pending_codex=pending_counts.get("codex", 0),
        pending_claude=pending_counts.get("claude", 0),
        pending_cursor=pending_counts.get("cursor", 0),
        pending_operator=pending_counts.get("operator", 0),
        stale_packet_count=stale_packet_count,
        derived_next_instruction=derived_instruction,
        derived_next_instruction_source=derived_source,
        instruction_priority_decision=_queue_priority_decision(derived_source),
        last_failed_action_request=_failed_action_request_summary(packet_rows),
    )


def attach_event_queue_state(
    review_state: dict[str, object],
    *,
    artifact_root,
) -> None:
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return
    review_state["packets"] = attach_action_request_delivery_receipts(
        packets=packets,
        artifact_root=artifact_root,
    )

    queue = _mapping(review_state.get("queue"))
    pending_counts = _pending_counts_from_queue(queue)
    review_state["queue"] = build_event_queue_state(
        pending_counts,
        int(queue.get("stale_packet_count") or 0),
        review_state["packets"],
    )
    review_state["queue"] = asdict(review_state["queue"])


def _pending_counts_from_queue(queue: Mapping[str, object]) -> dict[str, int]:
    return {
        provider: int(queue.get(f"pending_{provider}") or 0)
        for provider in _PENDING_QUEUE_PROVIDERS
    }


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _queue_priority_decision(
    derived_source: Mapping[str, object],
) -> dict[str, object]:
    decision = derived_source.get("priority_decision")
    if isinstance(decision, Mapping):
        return dict(decision)
    return InstructionPriorityDecision(
        selected_instruction_id="",
        selected_source_kind="none",
        rule_id="no_live_instruction_authority",
        rejected_alternatives=(),
        rejection_reasons=(),
        decided_at_utc=utc_timestamp(),
    ).to_dict()


def _failed_action_request_summary(
    packets: list[dict[str, object]],
) -> dict[str, object]:
    packet = latest_failed_action_request(packets)
    if packet is None:
        return {}
    return {
        "packet_id": str(packet.get("packet_id") or "").strip(),
        "from_agent": str(packet.get("from_agent") or "").strip(),
        "to_agent": str(packet.get("to_agent") or "").strip(),
        "requested_action": str(packet.get("requested_action") or "").strip(),
        "summary": str(packet.get("summary") or "").strip(),
        "execution_failed_at_utc": str(
            packet.get("execution_failed_at_utc") or ""
        ).strip(),
        "execution_failed_by": str(packet.get("execution_failed_by") or "").strip(),
        "execution_failed_reason": str(
            packet.get("execution_failed_reason") or ""
        ).strip(),
        "required_recovery": "fresh_action_request",
    }


def _priority_decision_for_packet(
    selected: Mapping[str, object],
    packets: list[dict[str, object]],
    *,
    rule_id: str,
) -> InstructionPriorityDecision:
    selected_id = str(selected.get("packet_id") or "").strip()
    rejected: list[str] = []
    reasons: list[str] = []
    for packet in packets:
        packet_id = str(packet.get("packet_id") or "").strip()
        if not packet_id or packet_id == selected_id:
            continue
        if not _is_instruction_candidate(packet):
            continue
        rejected.append(packet_id)
        reasons.append(f"{packet_id}:lower_priority_than_{rule_id or 'selected_rule'}")
    return InstructionPriorityDecision(
        selected_instruction_id=selected_id,
        selected_source_kind="packet",
        rule_id=rule_id or "packet_priority",
        rejected_alternatives=tuple(rejected),
        rejection_reasons=tuple(reasons),
        decided_at_utc=utc_timestamp(),
    )


def _is_instruction_candidate(packet: Mapping[str, object]) -> bool:
    kind = str(packet.get("kind") or "").strip()
    return kind in {"action_request", "instruction"}
