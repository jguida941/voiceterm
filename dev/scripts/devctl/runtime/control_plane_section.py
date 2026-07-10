"""Shared command-surface projection for the control-plane read model."""

from __future__ import annotations

from typing import Any

from .control_plane_read_model import ControlPlaneReadModel

CONTROL_PLANE_SECTION_FIELDS = (
    "resolved_phase",
    "top_blocker",
    "next_action",
    "next_command",
    "push_eligible",
    "review_accepted",
    "reviewer_mode",
    "operator_interaction_mode",
    "last_guard_ok",
    "pending_action_requests",
)


def project_control_plane_section(model: ControlPlaneReadModel) -> dict[str, Any]:
    """Project the parity-relevant control-plane fields for command surfaces."""
    return {field: getattr(model, field) for field in CONTROL_PLANE_SECTION_FIELDS}
