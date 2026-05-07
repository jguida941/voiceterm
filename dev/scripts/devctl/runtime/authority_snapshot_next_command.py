"""Next-command resolution for authority snapshots."""

from __future__ import annotations

from collections.abc import Mapping

from .authority_snapshot_actions import checkpoint_action_required
from .authority_snapshot_summary import summary_next_command


def resolved_next_command(
    *,
    payload: Mapping[str, object],
    recovery_authority: Mapping[str, object],
    doctor: Mapping[str, object],
    decision: Mapping[str, object],
    next_command: str,
) -> str:
    checkpoint_authority_active = checkpoint_action_required(payload) or any(
        str(action or "").strip() == "cut_checkpoint"
        for action in (
            recovery_authority.get("decision_action_id"),
            doctor.get("decision_action_id"),
            decision.get("action_id"),
        )
    )
    if checkpoint_authority_active:
        return _checkpoint_next_command(
            payload=payload,
            recovery_authority=recovery_authority,
            doctor=doctor,
            decision=decision,
            next_command=next_command,
        )
    command = (
        next_command
        or str(recovery_authority.get("command") or "").strip()
        or str(payload.get("next_command") or "").strip()
        or str(doctor.get("decision_command") or "").strip()
        or str(decision.get("command") or "").strip()
        or str(payload.get("recommended_command") or "").strip()
    )
    if command:
        return command
    if (
        "reviewer_gate" in payload
        or "implementation_permission" in payload
        or "push_decision" in payload
    ):
        return summary_next_command(payload)
    return ""


def _checkpoint_next_command(
    *,
    payload: Mapping[str, object],
    recovery_authority: Mapping[str, object],
    doctor: Mapping[str, object],
    decision: Mapping[str, object],
    next_command: str,
) -> str:
    checkpoint_command = (
        _scoped_checkpoint_command(
            recovery_authority,
            action_key="decision_action_id",
            command_key="command",
        )
        or _scoped_checkpoint_command(
            doctor,
            action_key="decision_action_id",
            command_key="decision_command",
        )
        or _scoped_checkpoint_command(
            decision,
            action_key="action_id",
            command_key="command",
        )
        or next_command
        or str(payload.get("next_command") or "").strip()
        or str(payload.get("recommended_command") or "").strip()
    )
    return checkpoint_command or summary_next_command(payload)


def _scoped_checkpoint_command(
    source: Mapping[str, object],
    *,
    action_key: str,
    command_key: str,
) -> str:
    if str(source.get(action_key) or "").strip() != "cut_checkpoint":
        return ""
    return str(source.get(command_key) or "").strip()


__all__ = ["resolved_next_command"]
