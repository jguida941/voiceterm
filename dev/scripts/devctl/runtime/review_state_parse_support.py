"""Support helpers shared by review-state parsing."""

from __future__ import annotations

from collections.abc import Mapping

from .control_state import _mapping, _string
from .review_state_models import ConductorCapabilityState
from .review_state_semantics import is_pending_implementer_state


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _optional_bool(mapping: Mapping[str, object], key: str) -> bool | None:
    """Preserve explicit unknown booleans instead of coercing them to False."""
    if key not in mapping:
        return None
    value = mapping.get(key)
    if value is None:
        return None
    return _bool(value)


def bridge_ack_state(
    *,
    bridge: Mapping[str, object],
    implementer_ack: str,
) -> str:
    """Classify implementer ACK state from bridge-backed projections."""
    if is_pending_implementer_state(
        implementer_status=_string(bridge.get("claude_status")),
        implementer_ack=implementer_ack,
    ):
        return "pending"
    if not implementer_ack:
        return "missing"
    if _bool(bridge.get("claude_ack_current")):
        return "current"
    return "stale"


def conductor_capability_state_from_payload(
    value: object,
) -> ConductorCapabilityState | None:
    """Parse one typed conductor-capability payload when present."""
    mapping = _mapping(value)
    if not mapping:
        return None
    return ConductorCapabilityState(
        provider=_string(mapping.get("provider")),
        role=_string(mapping.get("role")),
        startup_context_command=_string(mapping.get("startup_context_command")),
        may_edit_repo=_bool(mapping.get("may_edit_repo")),
        requires_explicit_takeover=_bool(
            mapping.get("requires_explicit_takeover")
        ),
        worker_unavailable_policy=_string(
            mapping.get("worker_unavailable_policy")
        ),
        queue_policy=_string(mapping.get("queue_policy")),
        takeover_command=_string(mapping.get("takeover_command")),
        status_summary=_string(mapping.get("status_summary")),
    )
