"""Packet-truth normalization for review-channel current-session state."""

from __future__ import annotations

from dataclasses import replace

from .collaboration_provider import (
    coding_provider_from_review_state,
    reviewer_provider_from_review_state,
)
from .current_session_attention import has_explicit_packet_truth
from .current_session_queue import (
    queue_instruction_preserves_packet_truth_clear,
)
from .current_session_support import compute_implementer_state_hash
from ..runtime.review_packet_inbox import (
    packet_inbox_from_review_state,
    summarize_packet_attention_open_findings,
)
from ..runtime.review_state_semantics import is_missing_instruction


def normalize_current_session_from_packet_truth(
    *,
    current_session,
    review_state: dict[str, object] | None,
):
    if current_session is None:
        return current_session
    resolved_review_state = _resolved_review_state(review_state)
    packet_truth_present = bool(
        isinstance(resolved_review_state, dict)
        and has_explicit_packet_truth(resolved_review_state)
    )
    packet_inbox = (
        packet_inbox_from_review_state(resolved_review_state)
        if packet_truth_present
        else None
    )
    implementer_provider = coding_provider_from_review_state(resolved_review_state)
    reviewer_provider = reviewer_provider_from_review_state(resolved_review_state)
    record = (
        packet_inbox.for_agent(implementer_provider)
        if packet_inbox is not None
        else None
    )
    clear_instruction = bool(
        record is not None
        and not str(record.current_instruction_packet_id or "").strip()
    )
    if clear_instruction and not _current_instruction_is_packet_owned(
        resolved_review_state,
        current_session=current_session,
    ):
        clear_instruction = False
    if clear_instruction and queue_instruction_preserves_packet_truth_clear(
        resolved_review_state,
        current_instruction=current_session.current_instruction,
    ):
        clear_instruction = False
    if clear_instruction and _attention_preserves_current_instruction(
        resolved_review_state,
        current_session=current_session,
    ):
        clear_instruction = False
    packet_attention_present = record is not None
    missing_instruction = is_missing_instruction(current_session.current_instruction)
    clear_current_instruction = clear_instruction or missing_instruction
    cleared_ack = "" if clear_current_instruction else current_session.implementer_ack
    return replace(
        current_session,
        current_instruction=(
            "" if clear_current_instruction else current_session.current_instruction
        ),
        current_instruction_revision=(
            ""
            if clear_current_instruction
            else current_session.current_instruction_revision
        ),
        implementer_ack=cleared_ack,
        implementer_ack_revision=(
            ""
            if clear_current_instruction
            else current_session.implementer_ack_revision
        ),
        implementer_ack_state=(
            "missing"
            if clear_current_instruction
            else current_session.implementer_ack_state
        ),
        implementer_state_hash=compute_implementer_state_hash(
            implementer_status=current_session.implementer_status,
            implementer_ack=cleared_ack,
        ),
        open_findings=summarize_packet_attention_open_findings(
            resolved_review_state,
            fallback="" if packet_attention_present else current_session.open_findings,
            agent=reviewer_provider,
        ),
    )


def _attention_preserves_current_instruction(
    review_state: dict[str, object] | None,
    *,
    current_session,
) -> bool:
    if is_missing_instruction(current_session.current_instruction):
        return False
    resolved_review_state = _resolved_review_state(review_state)
    if not isinstance(resolved_review_state, dict):
        return False
    attention = resolved_review_state.get("attention")
    if not isinstance(attention, dict):
        return False
    return str(attention.get("status") or "").strip() in {
        "checkpoint_required",
    }


def _current_instruction_is_packet_owned(
    review_state: dict[str, object] | None,
    *,
    current_session,
) -> bool:
    instruction = str(current_session.current_instruction or "").strip()
    if not instruction or is_missing_instruction(instruction):
        return False
    if instruction.startswith("Priority action_request:"):
        return True
    resolved_review_state = _resolved_review_state(review_state)
    if not isinstance(resolved_review_state, dict):
        return False
    queue = resolved_review_state.get("queue")
    if not isinstance(queue, dict):
        return False
    source = queue.get("derived_next_instruction_source")
    if not isinstance(source, dict) or not source:
        return False
    derived_instruction = str(queue.get("derived_next_instruction") or "").strip()
    return bool(derived_instruction and derived_instruction == instruction)


def _resolved_review_state(
    review_state: dict[str, object] | None,
) -> dict[str, object] | None:
    if isinstance(review_state, dict) and isinstance(
        review_state.get("review_state"), dict
    ):
        return review_state.get("review_state")
    return review_state
