"""Algebraic result cases for TaskCompleteDecision routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, assert_never

from .session_termination_policy import (
    CONTINUATION_ANCHOR_BODY_UNOBSERVED_ERROR,
    PENDING_REVIEW_PACKET_BODY_UNOBSERVED_ERROR,
    STOP_ANCHOR_BODY_UNOBSERVED_ERROR,
    TaskCompleteDecision,
)


@dataclass(frozen=True, slots=True)
class TaskCompletePacketAttentionPending:
    decision: TaskCompleteDecision
    kind: Literal["packet_attention_pending"] = "packet_attention_pending"


@dataclass(frozen=True, slots=True)
class TaskCompleteBodyObservationRequired:
    decision: TaskCompleteDecision
    kind: Literal["body_observation_required"] = "body_observation_required"


@dataclass(frozen=True, slots=True)
class TaskCompletePendingReview:
    decision: TaskCompleteDecision
    kind: Literal["pending_review_packet"] = "pending_review_packet"


@dataclass(frozen=True, slots=True)
class TaskCompleteContinuationMissing:
    decision: TaskCompleteDecision
    kind: Literal["continuation_anchor_missing"] = "continuation_anchor_missing"


@dataclass(frozen=True, slots=True)
class TaskCompleteContinuationActive:
    decision: TaskCompleteDecision
    kind: Literal["continuation_anchor_active"] = "continuation_anchor_active"


@dataclass(frozen=True, slots=True)
class TaskCompleteTerminated:
    decision: TaskCompleteDecision
    kind: Literal["terminated"] = "terminated"


TaskCompleteResult = (
    TaskCompletePacketAttentionPending
    | TaskCompleteBodyObservationRequired
    | TaskCompletePendingReview
    | TaskCompleteContinuationMissing
    | TaskCompleteContinuationActive
    | TaskCompleteTerminated
)

_BODY_OBSERVATION_ERRORS = frozenset(
    {
        CONTINUATION_ANCHOR_BODY_UNOBSERVED_ERROR,
        STOP_ANCHOR_BODY_UNOBSERVED_ERROR,
        PENDING_REVIEW_PACKET_BODY_UNOBSERVED_ERROR,
    }
)


def task_complete_result(decision: TaskCompleteDecision) -> TaskCompleteResult:
    """Classify a TaskCompleteDecision into exhaustive routing cases."""
    if decision.packet_attention_pending:
        return TaskCompletePacketAttentionPending(decision=decision)
    if decision.error_kind in _BODY_OBSERVATION_ERRORS:
        return TaskCompleteBodyObservationRequired(decision=decision)
    if decision.pending_review_packet:
        return TaskCompletePendingReview(decision=decision)
    if decision.continuation_anchor_missing:
        return TaskCompleteContinuationMissing(decision=decision)
    if not decision.terminate:
        return TaskCompleteContinuationActive(decision=decision)
    return TaskCompleteTerminated(decision=decision)


def task_complete_result_reason(result: TaskCompleteResult) -> str:
    """Return the typed reason through an exhaustive result-case match."""
    match result:
        case TaskCompletePacketAttentionPending(decision=decision):
            return decision.reason
        case TaskCompleteBodyObservationRequired(decision=decision):
            return decision.reason
        case TaskCompletePendingReview(decision=decision):
            return decision.reason
        case TaskCompleteContinuationMissing(decision=decision):
            return decision.reason
        case TaskCompleteContinuationActive(decision=decision):
            return decision.reason
        case TaskCompleteTerminated(decision=decision):
            return decision.reason
    assert_never(result)


__all__ = [
    "TaskCompleteBodyObservationRequired",
    "TaskCompleteContinuationActive",
    "TaskCompleteContinuationMissing",
    "TaskCompletePacketAttentionPending",
    "TaskCompletePendingReview",
    "TaskCompleteResult",
    "TaskCompleteTerminated",
    "task_complete_result",
    "task_complete_result_reason",
]
