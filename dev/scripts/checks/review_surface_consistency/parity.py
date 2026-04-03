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
    if not isinstance(disk_reviewer_runtime, dict) and not isinstance(disk_bridge, dict):
        warnings.append(
            "disk review_state.json has no reviewer_runtime or bridge section; "
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
