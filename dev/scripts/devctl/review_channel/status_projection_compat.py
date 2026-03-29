"""Compatibility-payload helpers for bridge-backed status projection."""

from __future__ import annotations

from dataclasses import dataclass

from .attach_auth_projection import (
    build_attach_auth_policy_state,
    build_service_identity_state,
)
from .bridge_projection import (
    bridge_projection_state_to_dict,
    build_bridge_projection_state,
)
from .status_projection_helpers import build_bridge_runtime


@dataclass(frozen=True)
class CompatProjectionInputs:
    project_id: str
    bridge_text: str
    bridge_liveness: dict[str, object]
    reduced_runtime: dict[str, object] | None
    service_identity: dict[str, object]
    attach_auth_policy: dict[str, object]
    legacy_agents: list[dict[str, object]]


def build_bridge_compat_projection(
    *,
    inputs: CompatProjectionInputs,
) -> dict[str, object]:
    """Build the bridge-backed `_compat` payload without one large dict literal."""
    compat: dict[str, object] = {}
    compat["project_id"] = inputs.project_id
    compat["runtime"] = build_bridge_runtime(
        inputs.bridge_liveness,
        inputs.reduced_runtime,
    )
    compat["service_identity"] = build_service_identity_state(
        inputs.service_identity
    )
    compat["attach_auth_policy"] = build_attach_auth_policy_state(
        inputs.attach_auth_policy
    )
    compat["bridge_projection"] = bridge_projection_state_to_dict(
        build_bridge_projection_state(
            bridge_text=inputs.bridge_text,
            bridge_liveness=inputs.bridge_liveness,
        )
    )
    compat["agents"] = inputs.legacy_agents
    return compat
