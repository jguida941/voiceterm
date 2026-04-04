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


@dataclass(frozen=True, slots=True)
class OperatorContext:
    """Typed operator-presence metadata for mode-aware decisions."""

    interaction_mode: str = OperatorInteractionMode.LOCAL_TERMINAL.value
    device: str = "desktop"                # desktop, phone, tablet
    operator_available: bool = True
    notification_channel: str = "terminal" # terminal, dashboard, bridge


def operator_context_from_mapping(value: object) -> OperatorContext:
    """Deserialize an OperatorContext from a mapping, defaulting missing fields."""
    mapping = _mapping(value)
    return OperatorContext(
        interaction_mode=(
            _string(mapping.get("interaction_mode"))
            or OperatorInteractionMode.LOCAL_TERMINAL.value
        ),
        device=_string(mapping.get("device")) or "desktop",
        operator_available=bool(mapping.get("operator_available", True)),
        notification_channel=(
            _string(mapping.get("notification_channel")) or "terminal"
        ),
    )
