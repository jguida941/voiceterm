"""Algebraic result cases for governed push projection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, assert_never

from ...runtime import ActionResult
from ...runtime.action_contracts import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionOutcome,
)


@dataclass(frozen=True, slots=True)
class PushSucceeded:
    action_id: str
    operator_guidance: str
    kind: Literal["succeeded"] = "succeeded"


@dataclass(frozen=True, slots=True)
class PushPartialProgress:
    action_id: str
    reason: str
    operator_guidance: str
    kind: Literal["partial_progress"] = "partial_progress"


@dataclass(frozen=True, slots=True)
class PushFailed:
    action_id: str
    reason: str
    operator_guidance: str
    retryable: bool = True
    kind: Literal["failed"] = "failed"


PushResult = PushSucceeded | PushPartialProgress | PushFailed


def action_result_for_push_result(result: PushResult) -> ActionResult:
    """Return the canonical ActionResult through an exhaustive push-result match."""
    match result:
        case PushSucceeded(action_id=action_id, operator_guidance=operator_guidance):
            return ActionResult(
                schema_version=ACTION_RESULT_SCHEMA_VERSION,
                contract_id=ACTION_RESULT_CONTRACT_ID,
                action_id=action_id,
                ok=True,
                status=ActionOutcome.PASS,
                reason="push_completed",
                operator_guidance=operator_guidance,
            )
        case PushPartialProgress(
            action_id=action_id,
            reason=reason,
            operator_guidance=operator_guidance,
        ):
            return ActionResult(
                schema_version=ACTION_RESULT_SCHEMA_VERSION,
                contract_id=ACTION_RESULT_CONTRACT_ID,
                action_id=action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason=reason,
                retryable=True,
                partial_progress=True,
                operator_guidance=operator_guidance,
            )
        case PushFailed(
            action_id=action_id,
            reason=reason,
            operator_guidance=operator_guidance,
            retryable=retryable,
        ):
            return ActionResult(
                schema_version=ACTION_RESULT_SCHEMA_VERSION,
                contract_id=ACTION_RESULT_CONTRACT_ID,
                action_id=action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason=reason,
                retryable=retryable,
                operator_guidance=operator_guidance,
            )
    assert_never(result)


__all__ = [
    "PushFailed",
    "PushPartialProgress",
    "PushResult",
    "PushSucceeded",
    "action_result_for_push_result",
]
