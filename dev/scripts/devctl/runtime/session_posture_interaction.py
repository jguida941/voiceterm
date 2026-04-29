"""Interaction-mode helpers for SessionPosture."""

from __future__ import annotations

from collections.abc import Mapping

_REMOTE_ATTACHMENT_ACTIVE = frozenset({"attached", "unknown"})


def resolve_interaction_mode(
    value: object,
    *,
    remote_control_attachment: object | None = None,
    effective_reviewer_mode: object = "",
) -> str:
    """Resolve current interaction mode from typed runtime posture inputs."""
    if remote_attachment_active(remote_control_attachment):
        return "remote_control"
    mode = _text(value)
    if mode in {"remote_control", "local_terminal", "dual_agent", "single_agent"}:
        return mode
    effective = _text(effective_reviewer_mode)
    if effective == "active_dual_agent":
        return "dual_agent"
    if effective == "single_agent":
        return "single_agent"
    return "unresolved"


def remote_attachment_active(value: object | None) -> bool:
    """Return whether a remote-control attachment proves live remote control."""
    if value is None:
        return False
    status = _text(getattr(value, "status", ""))
    if not status and isinstance(value, Mapping):
        status = _text(value.get("status"))
    return status in _REMOTE_ATTACHMENT_ACTIVE


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["remote_attachment_active", "resolve_interaction_mode"]
