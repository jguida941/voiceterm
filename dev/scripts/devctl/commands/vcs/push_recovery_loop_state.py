"""State projection helpers for governed push recovery-loop repair."""

from __future__ import annotations

from .push_recovery_loop_payload import (
    compact_step,
    field_value,
    payload_allows_bounded_recovery,
    startup_context_payload_from_step,
    startup_next_command,
)


def mark_recovery_required_from_startup_context_step(
    state: object,
    step: object,
) -> dict[str, object]:
    """Record that managed projection sync found a bounded startup recovery."""
    payload = startup_context_payload_from_step(step)
    required = payload_allows_bounded_recovery(payload)

    record: dict[str, object] = {}
    record["required"] = required
    record["reason"] = (
        "bounded_startup_context_recovery"
        if required
        else "startup_context_failure_not_bounded"
    )
    record["attention_status"] = field_value(payload, "attention_status")
    record["implementation_permission"] = field_value(
        payload,
        "implementation_permission",
    )
    record["observed_control_topology"] = field_value(
        payload,
        "observed_control_topology",
    )
    record["recovery_action"] = field_value(payload, "recovery_action")
    record["recovery_basis"] = field_value(payload, "recovery_basis")
    record["next_command"] = startup_next_command(payload)
    record["startup_context_step"] = compact_step(step)

    set_state_attr(state, "pre_validation_recovery_loop_repair_required", required)
    set_state_attr(state, "pre_validation_recovery_loop_repair_startup", record)

    return record


def recovery_required(state: object) -> bool:
    if bool(getattr(state, "pre_validation_recovery_loop_repair_required", False)):
        return True

    sync = getattr(state, "pre_validation_managed_projection_sync", {})
    return isinstance(sync, dict) and bool(sync.get("startup_context_recovery_required"))


def startup_payload_from_state(state: object) -> dict[str, object]:
    record = getattr(state, "pre_validation_recovery_loop_repair_startup", {})
    if not isinstance(record, dict):
        return {}

    fallback = _startup_payload_from_record(record)
    startup_step = record.get("startup_context_step")
    payload = startup_context_payload_from_step(startup_step)
    if not payload:
        return fallback

    merged = dict(fallback)
    for key, value in payload.items():
        if field_value({key: value}, key) or key not in merged:
            merged[key] = value
    return merged


def _startup_payload_from_record(record: dict[str, object]) -> dict[str, object]:
    fallback: dict[str, object] = {}
    fallback["action"] = "repair_reviewer_loop" if bool(record.get("required")) else ""
    fallback["reason"] = field_value(record, "reason")
    fallback["attention_status"] = field_value(record, "attention_status")
    fallback["recovery_action"] = field_value(record, "recovery_action")
    fallback["next_command"] = field_value(record, "next_command")
    fallback["observed_control_topology"] = field_value(
        record,
        "observed_control_topology",
    )
    fallback["implementation_permission"] = field_value(
        record,
        "implementation_permission",
    )
    fallback["recovery_basis"] = field_value(record, "recovery_basis")
    return fallback


def set_state_attr(state: object, name: str, value: object) -> None:
    try:
        setattr(state, name, value)
    except (AttributeError, TypeError):
        pass


__all__ = [
    "mark_recovery_required_from_startup_context_step",
    "recovery_required",
    "set_state_attr",
    "startup_payload_from_state",
]
