"""Parity checks for review-surface consistency reporting."""

from __future__ import annotations

from pathlib import Path

from .support import load_disk_review_state


def bridge_poll_parity_errors(
    bridge_poll: dict[str, object],
    turn_authority: dict[str, object],
) -> list[str]:
    if not bridge_poll or not turn_authority:
        return []
    return [
        "bridge-poll parity mismatch on "
        f"{field}: bridge-poll={bridge_poll.get(field)!r}, "
        f"turn-authority={turn_authority.get(field)!r}"
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


def recovery_surface_parity_errors(
    *,
    review_state: dict[str, object],
    compact: dict[str, object],
    bridge_poll: dict[str, object],
    turn_authority: dict[str, object],
) -> list[str]:
    diagnosis_status = _nested(
        review_state, "recovery_assessment", "diagnosis", "status"
    ) or _nested(review_state, "attention", "status")
    decision_action_id = _nested(
        review_state, "recovery_assessment", "decision", "action_id"
    )
    decision_command = _nested(
        review_state, "recovery_assessment", "decision", "command"
    ) or _nested(review_state, "attention", "recommended_command")
    if not diagnosis_status and not decision_action_id and not decision_command:
        return []

    errors: list[str] = []
    surfaces = {
        "review_state_attention": {
            "diagnosis_status": _nested(review_state, "attention", "status"),
            "decision_command": _nested(
                review_state, "attention", "recommended_command"
            ),
        },
        "review_state_doctor": {
            "status": _nested(review_state, "_compat", "doctor", "status"),
            "diagnosis_status": _nested(
                review_state, "_compat", "doctor", "diagnosis_status"
            ),
            "decision_action_id": _nested(
                review_state, "_compat", "doctor", "decision_action_id"
            ),
            "decision_command": _nested(
                review_state, "_compat", "doctor", "decision_command"
            ),
        },
        "compact_doctor": {
            "status": _nested(compact, "doctor", "status"),
            "diagnosis_status": _nested(compact, "doctor", "diagnosis_status"),
            "decision_action_id": _nested(compact, "doctor", "decision_action_id"),
            "decision_command": _nested(compact, "doctor", "decision_command"),
        },
        "bridge_poll": bridge_poll,
        "turn_authority": turn_authority,
    }
    for surface_name, payload in surfaces.items():
        if not isinstance(payload, dict):
            continue
        if diagnosis_status:
            surface_status = str(payload.get("diagnosis_status") or "").strip()
            if not surface_status and surface_name == "review_state_attention":
                surface_status = str(payload.get("status") or "").strip()
            if surface_status and surface_status != diagnosis_status:
                errors.append(
                    f"diagnosis parity mismatch on {surface_name}: "
                    f"expected={diagnosis_status!r}, actual={surface_status!r}"
                )
        if decision_action_id:
            surface_action_id = str(payload.get("decision_action_id") or "").strip()
            if surface_action_id and surface_action_id != decision_action_id:
                errors.append(
                    f"decision parity mismatch on {surface_name}.decision_action_id: "
                    f"expected={decision_action_id!r}, actual={surface_action_id!r}"
                )
        if decision_command:
            surface_command = str(payload.get("decision_command") or "").strip()
            if not surface_command and surface_name == "review_state_attention":
                surface_command = str(
                    payload.get("decision_command")
                    or payload.get("recommended_command")
                    or ""
                ).strip()
            if surface_command and surface_command != decision_command:
                errors.append(
                    f"decision parity mismatch on {surface_name}.decision_command: "
                    f"expected={decision_command!r}, actual={surface_command!r}"
                )
        status = str(payload.get("status") or "").strip()
        if diagnosis_status not in {"", "healthy"} and status == "healthy":
            errors.append(
                f"{surface_name} reports healthy while diagnosis is {diagnosis_status!r}"
            )
    return errors


def disk_turn_authority_parity_errors(
    *,
    repo_root: Path,
    turn_authority: dict[str, object],
    bridge_poll: dict[str, object],
    disk_review_state_override: dict[str, object] | None = None,
    disk_override_provided: bool = False,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if disk_override_provided:
        disk_state = disk_review_state_override or {}
    else:
        disk_state = load_disk_review_state(repo_root)
    if not disk_state:
        warnings.append("disk review_state.json not found; skipping disk parity check")
        return errors, warnings
    if not turn_authority and not bridge_poll:
        warnings.append("no turn-authority or bridge-poll payload; skipping disk parity check")
        return errors, warnings
    authority_source = turn_authority or bridge_poll
    disk_reviewer_runtime = disk_state.get("reviewer_runtime")
    disk_bridge = disk_state.get("bridge")
    disk_attention = disk_state.get("attention")
    disk_recovery = disk_state.get("recovery_assessment")
    if (
        not isinstance(disk_reviewer_runtime, dict)
        and not isinstance(disk_bridge, dict)
        and not isinstance(disk_recovery, dict)
    ):
        warnings.append(
            "disk review_state.json has no reviewer_runtime, bridge, or recovery_assessment section; "
            "skipping disk parity check"
        )
        return errors, warnings
    for field_name, disk_value in (
        (
            "effective_reviewer_mode",
            _disk_section_value(
                disk_reviewer_runtime,
                disk_bridge,
                key="effective_reviewer_mode",
            ),
        ),
        ("launch_truth", _disk_section_value(disk_bridge, key="launch_truth")),
        ("attention_status", _disk_section_value(disk_attention, key="status")),
        ("diagnosis_status", _disk_nested_value(disk_recovery, "diagnosis", "status")),
        (
            "decision_action_id",
            _disk_nested_value(disk_recovery, "decision", "action_id"),
        ),
        (
            "decision_command",
            _disk_nested_value(disk_recovery, "decision", "command"),
        ),
    ):
        authority_value = authority_source.get(field_name)
        authority_text = str(authority_value) if authority_value is not None else ""
        if disk_value is None or (not authority_text and not disk_value):
            continue
        if authority_text != disk_value:
            errors.append(
                f"disk-artifact parity mismatch on {field_name}: "
                f"authority={authority_text!r}, disk={disk_value!r}"
            )
    return errors, warnings


def _disk_section_value(*sections: object, key: str) -> str | None:
    for section in sections:
        if isinstance(section, dict):
            value = section.get(key)
            if value:
                return str(value)
    return None


def _disk_nested_value(section: object, *keys: str) -> str | None:
    current = section
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if current in (None, ""):
        return None
    return str(current)


def _nested(mapping: dict[str, object], *keys: str) -> str:
    current: object = mapping
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    if current in (None, ""):
        return ""
    return str(current)
