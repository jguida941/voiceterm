"""Bridge-poll parity checks for review-surface consistency reporting."""

from __future__ import annotations

from .models import ConvergencePassViolation


def bridge_poll_parity_errors(
    bridge_poll: dict[str, object],
    turn_authority: dict[str, object],
) -> list[str]:
    return [
        violation.detail
        for violation in bridge_poll_parity_violations(
            bridge_poll=bridge_poll,
            turn_authority=turn_authority,
        )
    ]


def bridge_poll_parity_violations(
    *,
    bridge_poll: dict[str, object],
    turn_authority: dict[str, object],
) -> list[ConvergencePassViolation]:
    if not bridge_poll or not turn_authority:
        return []
    return [
        ConvergencePassViolation(
            category="bridge_poll_parity",
            surface="bridge_poll",
            field=field,
            expected=repr(turn_authority.get(field)),
            actual=repr(bridge_poll.get(field)),
            detail=(
                "bridge-poll parity mismatch on "
                f"{field}: bridge-poll={bridge_poll.get(field)!r}, "
                f"turn-authority={turn_authority.get(field)!r}"
            ),
        )
        for field in (
            "effective_reviewer_mode",
            "launch_truth",
            "attention_status",
            "recovery_action_allowed",
            "diagnosis_status",
            "decision_action_id",
            "decision_command",
            "decision_execution_owner",
            "decision_requires_approval",
            "decision_can_auto_fix",
            "implementation_blocked",
            "implementation_block_reason",
            "reviewed_hash_current",
            "review_needed",
            "next_turn_required",
            "next_turn_role",
            "next_turn_reason",
        )
        if bridge_poll.get(field) != turn_authority.get(field)
    ]
