"""Projection-input parser for PushEnforcement runtime records."""

from __future__ import annotations

from collections.abc import Mapping

from ..governance.push_state_selection import PushProjectionInputs
from .value_coercion import coerce_string


def push_projection_inputs_from_payload(
    payload: Mapping[str, object],
) -> PushProjectionInputs:
    """Parse the push projection fields through their owning typed contract."""
    return PushProjectionInputs(
        upstream_ref=coerce_string(payload.get("upstream_ref")),
        default_remote=coerce_string(payload.get("default_remote")) or "origin",
        current_branch=coerce_string(payload.get("current_branch")),
        current_head_commit=coerce_string(payload.get("current_head_commit")),
        current_approved_target_identity=coerce_string(
            payload.get("current_approved_target_identity")
        ),
        current_worktree_identity=coerce_string(
            payload.get("current_worktree_identity")
        ),
    )
