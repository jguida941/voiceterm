"""Checkpoint-gate detection helpers for governed push recovery."""

from __future__ import annotations

from .push_recovery_loop_payload import (
    compact_startup_payload,
    field_value,
    startup_context_payload_from_step,
)


def startup_context_step_is_checkpoint_gate(step) -> bool:
    """Return true when startup-context only reported the live checkpoint gate."""
    return payload_is_checkpoint_gate(startup_context_payload_from_step(step))


def payload_is_checkpoint_gate(payload: dict[str, object]) -> bool:
    if not payload:
        return False
    action = field_value(payload, "advisory_action") or field_value(payload, "action")
    attention_status = field_value(payload, "attention_status")
    reason = field_value(payload, "advisory_reason") or field_value(payload, "reason")
    return (
        action in {"checkpoint_before_continue", "cut_checkpoint"}
        or attention_status == "checkpoint_required"
        or reason == "dirty_and_untracked_budget_exceeded"
    )


def defer_startup_context_checkpoint_gate(
    state,
    step,
    *,
    next_step_label: str,
    after_reviewer_follow: bool = False,
) -> None:
    """Preserve authorized publication when startup only reports live dirt."""
    sync = getattr(state, "pre_validation_managed_projection_sync", {})
    if isinstance(sync, dict):
        sync["startup_context_checkpoint_gate_deferred"] = True
        sync["startup_context_checkpoint_gate"] = compact_startup_payload(
            startup_context_payload_from_step(step)
        )
        state.pre_validation_managed_projection_sync = sync
    retry_source = " after reviewer follow" if after_reviewer_follow else ""
    state.warnings.append(
        "Managed projection receipt moved HEAD and startup-context reported "
        f"the live checkpoint gate{retry_source}; preserving authorized "
        f"pipeline publication before {next_step_label}."
    )


__all__ = [
    "defer_startup_context_checkpoint_gate",
    "payload_is_checkpoint_gate",
    "startup_context_step_is_checkpoint_gate",
]
