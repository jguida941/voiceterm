"""Field resolution helpers for typed reviewer turn authority."""

from __future__ import annotations

from ..runtime.conductor_capability import authority_reviewer_mode
from .turn_authority_helpers import recommended_command


def resolve_modes(
    bridge_liveness,
    bridge,
    reviewer_runtime,
    typed_complete,
    fallback_eff,
):
    reviewer_mode = (
        reviewer_runtime.reviewer_mode
        if typed_complete
        and reviewer_runtime is not None
        and reviewer_runtime.reviewer_mode
        else (
            bridge.reviewer_mode
            if typed_complete and bridge is not None and bridge.reviewer_mode
            else bridge_liveness.reviewer_mode
        )
    )
    effective_reviewer_mode = (
        reviewer_runtime.effective_reviewer_mode
        if typed_complete
        and reviewer_runtime is not None
        and reviewer_runtime.effective_reviewer_mode
        else (
            bridge.effective_reviewer_mode
            if typed_complete and bridge is not None and bridge.effective_reviewer_mode
            else fallback_eff if fallback_eff else reviewer_mode
        )
    )
    reviewer_mode = authority_reviewer_mode(
        reviewer_mode,
        effective_reviewer_mode,
    )
    reviewer_freshness = (
        reviewer_runtime.reviewer_freshness
        if reviewer_runtime is not None and reviewer_runtime.reviewer_freshness
        else (
            bridge.reviewer_freshness
            if bridge is not None and bridge.reviewer_freshness
            else bridge_liveness.reviewer_freshness
        )
    )
    return reviewer_mode, effective_reviewer_mode, reviewer_freshness


def resolve_recovery_action(
    reviewer_runtime,
    recovery_assessment,
    typed_complete,
    fallback_assessment,
    attention_status,
):
    if (
        typed_complete
        and recovery_assessment is not None
        and recovery_assessment.decision.command
    ):
        return recovery_assessment.decision.command

    if (
        typed_complete
        and reviewer_runtime is not None
        and reviewer_runtime.recovery_action_allowed
    ):
        return reviewer_runtime.recovery_action_allowed

    if fallback_assessment is not None and fallback_assessment.decision.command:
        return fallback_assessment.decision.command

    return recommended_command(attention_status)


def resolve_implementation_block(reviewer_runtime, typed_complete, attention_status):
    blocked = bool(
        reviewer_runtime.implementation_blocked
        if typed_complete and reviewer_runtime is not None
        else False
    )
    reason = (
        reviewer_runtime.implementation_block_reason
        if typed_complete
        and reviewer_runtime is not None
        and reviewer_runtime.implementation_block_reason
        else attention_status if blocked and attention_status else ""
    )
    return blocked, reason


def review_needed(reviewed_hash_current: bool | None) -> bool | None:
    if reviewed_hash_current is None:
        return None
    return not reviewed_hash_current
