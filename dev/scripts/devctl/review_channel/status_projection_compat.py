"""Compatibility-payload helpers for bridge-backed status projection."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

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
    current_session: object
    bridge_state: object
    doctor: object
    snapshot_id: str = ""
    packets: list[dict[str, object]] | None = None


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
            current_session=_mapping(inputs.current_session),
            bridge_state=_mapping(inputs.bridge_state),
            packets=inputs.packets,
        )
    )
    bridge_projection = compat.get("bridge_projection")
    if isinstance(bridge_projection, dict):
        metadata = bridge_projection.get("metadata")
        if isinstance(metadata, dict) and inputs.snapshot_id:
            metadata["snapshot_id"] = inputs.snapshot_id
    compat["doctor"] = _mapping(inputs.doctor)
    if inputs.snapshot_id:
        compat["snapshot_id"] = inputs.snapshot_id
    compat["agents"] = inputs.legacy_agents
    return compat


def attach_bridge_compat_projection(
    *,
    result: dict[str, object],
    inputs: CompatProjectionInputs,
) -> dict[str, object]:
    """Attach the `_compat` payload and return the canonical review-state dict."""
    result["_compat"] = build_bridge_compat_projection(inputs=inputs)
    return result


def legacy_agent_entry(agent: object) -> dict[str, object]:
    """Project one runtime registry row into the legacy bridge-agent shape."""
    entry = dict(agent) if isinstance(agent, dict) else {}
    entry["status"] = entry.get("job_state", "")
    entry["role"] = entry.get("current_job", "")
    entry["capabilities"] = []
    return entry


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
