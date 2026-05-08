"""Shell command builders for typed agent-loop decisions."""

from __future__ import annotations

from .agent_loop_operator_override import (
    DEFAULT_OPERATOR_OVERRIDE_REASON,
    EDIT_ONLY_OVERRIDE_SCOPE,
    OPERATOR_OVERRIDE_REQUESTOR,
)

_OPERATOR_OVERRIDE_FLAG = "--operator-override"
_OVERRIDE_SCOPE_FLAG = "--override-scope"
_OVERRIDE_REASON_FLAG = "--override-reason"
_OVERRIDE_BY_FLAG = "--override-by"


def scoped_loop_command(ctx) -> str:
    parts = [
        "python3",
        "dev/scripts/devctl.py",
        "agent-loop",
        "--format",
        "json",
        "--actor",
        _shell_word(ctx.actor or "claude"),
        "--role",
        _shell_word(ctx.role or "dashboard"),
    ]
    if ctx.session:
        parts.extend(("--session-id", _shell_word(ctx.session)))
    if ctx.loop_intent and ctx.loop_intent != "auto":
        parts.extend(("--mode", _shell_word(ctx.loop_intent)))
    if ctx.requested_plan_ref:
        parts.extend(("--plan", _shell_word(ctx.requested_plan_ref)))
    if ctx.requested_packet_id:
        parts.extend(("--packet", _shell_word(ctx.requested_packet_id)))
    if ctx.operator_override.requested:
        parts.append(_OPERATOR_OVERRIDE_FLAG)
        if ctx.operator_override.scope:
            parts.extend((_OVERRIDE_SCOPE_FLAG, _shell_word(ctx.operator_override.scope)))
        if ctx.operator_override.reason:
            parts.extend((_OVERRIDE_REASON_FLAG, _shell_word(ctx.operator_override.reason)))
        if ctx.operator_override.requested_by:
            parts.extend((_OVERRIDE_BY_FLAG, _shell_word(ctx.operator_override.requested_by)))
    return " ".join(parts)


def scoped_operator_override_command(ctx, *, reason: str) -> str:
    """Return the explicit edit-only override command for a scoped loop target."""
    if ctx.operator_override.requested or ctx.operator_override.active:
        return ""
    if not (ctx.requested_plan_ref or ctx.requested_packet_id):
        return ""
    return " ".join(
        (
            scoped_loop_command(ctx),
            _OPERATOR_OVERRIDE_FLAG,
            _OVERRIDE_SCOPE_FLAG,
            EDIT_ONLY_OVERRIDE_SCOPE,
            _OVERRIDE_REASON_FLAG,
            _shell_word(reason or DEFAULT_OPERATOR_OVERRIDE_REASON),
            _OVERRIDE_BY_FLAG,
            OPERATOR_OVERRIDE_REQUESTOR,
        )
    )


def _shell_word(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "''"
    if all(ch.isalnum() or ch in "._:-/" for ch in text):
        return text
    return "'" + text.replace("'", "'\"'\"'") + "'"


__all__ = ["scoped_loop_command", "scoped_operator_override_command"]
