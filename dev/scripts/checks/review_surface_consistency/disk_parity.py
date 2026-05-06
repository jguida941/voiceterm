"""Disk artifact parity checks for review-surface consistency reporting."""

from __future__ import annotations

from pathlib import Path

from .models import ConvergencePassViolation
from .support import load_disk_review_state


def disk_turn_authority_parity_errors(
    *,
    repo_root: Path,
    turn_authority: dict[str, object],
    bridge_poll: dict[str, object],
    disk_review_state_override: dict[str, object] | None = None,
    disk_override_provided: bool = False,
) -> tuple[list[str], list[str]]:
    violations, warnings = disk_turn_authority_parity_violations(
        repo_root=repo_root,
        turn_authority=turn_authority,
        bridge_poll=bridge_poll,
        disk_review_state_override=disk_review_state_override,
        disk_override_provided=disk_override_provided,
    )
    return [violation.detail for violation in violations], warnings


def disk_turn_authority_parity_violations(
    *,
    repo_root: Path,
    turn_authority: dict[str, object],
    bridge_poll: dict[str, object],
    disk_review_state_override: dict[str, object] | None = None,
    disk_override_provided: bool = False,
) -> tuple[list[ConvergencePassViolation], list[str]]:
    errors: list[ConvergencePassViolation] = []
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
                ConvergencePassViolation(
                    category="disk_artifact_parity",
                    surface="disk_review_state",
                    field=field_name,
                    expected=authority_text,
                    actual=disk_value,
                    detail=(
                        f"disk-artifact parity mismatch on {field_name}: "
                        f"authority={authority_text!r}, disk={disk_value!r}"
                    ),
                )
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
