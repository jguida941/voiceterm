"""Typed scope semantics for session termination anchors."""

from __future__ import annotations

from collections.abc import Mapping

ANCHOR_SCOPE_SESSION = "session"
ANCHOR_SCOPE_ROLE = "role"
ANCHOR_SCOPE_PLAN = "plan"
VALID_ANCHOR_SCOPES = frozenset(
    {
        ANCHOR_SCOPE_SESSION,
        ANCHOR_SCOPE_ROLE,
        ANCHOR_SCOPE_PLAN,
    }
)

SESSION_TERMINATION_ANCHOR_KINDS = frozenset(
    {
        "continuation_anchor",
        "stop_anchor",
    }
)


def normalize_anchor_scope(value: object) -> str:
    """Return a canonical anchor scope token or an empty string."""
    scope = _text(value).lower().replace("-", "_")
    if scope in {"target_role", "target_role_scoped", "role_scoped"}:
        scope = ANCHOR_SCOPE_ROLE
    if scope in {"session_scoped"}:
        scope = ANCHOR_SCOPE_SESSION
    if scope in {"plan_scoped"}:
        scope = ANCHOR_SCOPE_PLAN
    return scope if scope in VALID_ANCHOR_SCOPES else ""


def effective_anchor_scope(packet: Mapping[str, object]) -> str:
    """Resolve explicit scope first, then infer the legacy route shape."""
    if not is_session_termination_anchor(packet):
        return ""
    explicit = normalize_anchor_scope(packet.get("anchor_scope"))
    if explicit:
        return explicit
    if _text(packet.get("target_session_id")):
        return ANCHOR_SCOPE_SESSION
    if _text(packet.get("target_kind")) == "plan" and _text(packet.get("target_ref")):
        return ANCHOR_SCOPE_PLAN
    return ANCHOR_SCOPE_ROLE


def has_structured_anchor_scope(packet: Mapping[str, object]) -> bool:
    """Return whether an anchor carries typed scope fields, not body prose."""
    if normalize_anchor_scope(packet.get("anchor_scope")):
        return True
    if _text(packet.get("target_session_id")):
        return True
    if _text(packet.get("target_role")):
        return True
    return _text(packet.get("target_kind")) == "plan" and bool(
        _text(packet.get("target_ref"))
    )


def is_session_termination_anchor(packet: Mapping[str, object]) -> bool:
    """Return whether a packet participates in continuation/stop anchoring."""
    return _text(packet.get("kind")) in SESSION_TERMINATION_ANCHOR_KINDS


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "ANCHOR_SCOPE_PLAN",
    "ANCHOR_SCOPE_ROLE",
    "ANCHOR_SCOPE_SESSION",
    "SESSION_TERMINATION_ANCHOR_KINDS",
    "VALID_ANCHOR_SCOPES",
    "effective_anchor_scope",
    "has_structured_anchor_scope",
    "is_session_termination_anchor",
    "normalize_anchor_scope",
]
