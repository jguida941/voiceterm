"""Compatibility exports for review-surface parity checks."""

from __future__ import annotations

from .bridge_poll_parity import (
    bridge_poll_parity_errors,
    bridge_poll_parity_violations,
)
from .disk_parity import (
    disk_turn_authority_parity_errors,
    disk_turn_authority_parity_violations,
)
from .queue_parity import queue_current_instruction_parity_violations
from .recovery_parity import (
    attention_projection_parity_errors,
    attention_projection_parity_violations,
    recovery_surface_parity_errors,
    recovery_surface_parity_violations,
)
from .support import _nested

__all__ = [
    "_nested",
    "attention_projection_parity_errors",
    "attention_projection_parity_violations",
    "bridge_poll_parity_errors",
    "bridge_poll_parity_violations",
    "disk_turn_authority_parity_errors",
    "disk_turn_authority_parity_violations",
    "queue_current_instruction_parity_violations",
    "recovery_surface_parity_errors",
    "recovery_surface_parity_violations",
]
