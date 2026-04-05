"""Typed operator-interaction mode authority for governance pipeline decisions.

OperatorInteractionMode captures how the human operator connects to the
system (local keyboard, remote phone, dual-agent bridge, or single-AI auto).
OperatorContext bundles that mode with device metadata so downstream code
(recovery terminal selection, launch script rollover, startup summary) can
make mode-aware decisions without string comparisons scattered across modules.
"""

from __future__ import annotations

from dataclasses import dataclass

from .enum_compat import StrEnum
from .value_coercion import (
    coerce_mapping as _mapping,
    coerce_string as _string,
)


class OperatorInteractionMode(StrEnum):
    """How the human operator interacts with the governance pipeline."""

    LOCAL_TERMINAL = "local_terminal"      # human at keyboard, Terminal prompts OK
    REMOTE_CONTROL = "remote_control"      # operator on phone, route to bridge/dashboard
    DUAL_AGENT = "dual_agent"              # Codex reviews + Claude codes, bridge coordination
    SINGLE_AGENT = "single_agent"          # one AI, full auto
    UNRESOLVED = "unresolved"              # mode not yet determined — fail closed


# Modes that represent a resolved operator state (safe to act on).
RESOLVED_MODES: frozenset[str] = frozenset(
    m.value for m in OperatorInteractionMode if m is not OperatorInteractionMode.UNRESOLVED
)

# Modes where the operator is NOT at a local keyboard.
REMOTE_MODES: frozenset[str] = frozenset({
    OperatorInteractionMode.REMOTE_CONTROL.value,
    OperatorInteractionMode.DUAL_AGENT.value,
})


def resolve_operator_interaction_mode(raw: str) -> OperatorInteractionMode:
    """Map a raw string to a typed operator interaction mode.

    Fails closed: unknown or empty values resolve to UNRESOLVED instead of
    silently defaulting to LOCAL_TERMINAL.
    """
    normalized = (raw or "").strip().lower()
    if not normalized:
        return OperatorInteractionMode.UNRESOLVED
    try:
        return OperatorInteractionMode(normalized)
    except ValueError:
        return OperatorInteractionMode.UNRESOLVED


def is_remote_mode(mode: str) -> bool:
    """Return True when the operator is NOT at a local keyboard."""
    return mode in REMOTE_MODES


def is_resolved(mode: str) -> bool:
    """Return True when the mode is known and safe to act on."""
    return mode in RESOLVED_MODES


@dataclass(frozen=True, slots=True)
class OperatorContext:
    """Typed operator-presence metadata for mode-aware decisions."""

    interaction_mode: str = OperatorInteractionMode.UNRESOLVED.value
    device: str = "desktop"                # desktop, phone, tablet
    operator_available: bool = True
    notification_channel: str = "terminal" # terminal, dashboard, bridge


def operator_context_from_mapping(value: object) -> OperatorContext:
    """Deserialize an OperatorContext from a mapping.

    Fails closed: missing interaction_mode resolves to UNRESOLVED.
    """
    mapping = _mapping(value)
    raw_mode = _string(mapping.get("interaction_mode"))
    resolved = resolve_operator_interaction_mode(raw_mode)
    return OperatorContext(
        interaction_mode=resolved.value,
        device=_string(mapping.get("device")) or "desktop",
        operator_available=bool(mapping.get("operator_available", True)),
        notification_channel=(
            _string(mapping.get("notification_channel")) or "terminal"
        ),
    )
