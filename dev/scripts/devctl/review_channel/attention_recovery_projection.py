"""Attention-status projections that depend on recovery executability."""

from __future__ import annotations

from .conductor_authority import (
    conductor_signal_present,
    live_reviewer_conductor_present,
)
from .peer_liveness import AttentionStatus


def project_recover_ineligible_status(status: str, ctx) -> str:
    """Project implementer-only recover to pair relaunch when recover cannot run."""
    if status != AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED.value:
        return status
    if not conductor_signal_present(ctx.bridge_liveness):
        return status
    if live_reviewer_conductor_present(ctx.bridge_liveness):
        return status
    return AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value
