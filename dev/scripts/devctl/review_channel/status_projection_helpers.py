"""Helpers extracted from status_projection to stay under code-shape limits."""

from __future__ import annotations

from pathlib import Path

from .core import active_conductor_providers as _active_conductor_providers
from .reviewer_runtime_session_owner import conductor_visibility as _conductor_visibility
from .status_projection_liveness import (
    bridge_liveness_warnings,
    hybrid_loop_errors,
    single_agent_lane_has_live_typed_authority,
)
from .status_projection_runtime import (
    build_bridge_push_enforcement_state,
    build_bridge_runtime,
    clean_section,
)
from . import status_projection_liveness as _liveness

active_conductor_providers = _active_conductor_providers
conductor_visibility = _conductor_visibility


def attach_conductor_session_state(
    *,
    bridge_liveness: dict[str, object],
    output_root: Path,
) -> None:
    """Compatibility wrapper that keeps patchable helper names stable.

    Tests and legacy callers patch `status_projection_helpers.active_conductor_providers`
    and `status_projection_helpers.conductor_visibility`. After the helper split,
    keep this public entrypoint routing through those names instead of the
    deeper module globals.
    """
    active_providers = list(active_conductor_providers(session_output_root=output_root))
    for provider in _liveness._single_agent_remote_control_providers(
        bridge_liveness=bridge_liveness,
        output_root=output_root,
    ):
        if provider not in active_providers:
            active_providers.append(provider)
    reviewer_provider = _liveness._single_agent_local_reviewer_provider(
        bridge_liveness=bridge_liveness,
        output_root=output_root,
    )
    if reviewer_provider and reviewer_provider not in active_providers:
        active_providers.append(reviewer_provider)
    bridge_liveness["active_conductor_providers"] = list(active_providers)
    bridge_liveness["codex_conductor_active"] = "codex" in active_providers
    bridge_liveness["claude_conductor_active"] = "claude" in active_providers
    bridge_liveness["conductor_visibility"] = conductor_visibility(
        session_output_root=output_root
    )
    bridge_liveness["launch_truth"] = _liveness.classify_launch_truth(bridge_liveness).value
    _liveness._degrade_active_dual_agent_freshness(bridge_liveness)
    bridge_liveness["effective_reviewer_mode"] = _liveness.effective_reviewer_mode(
        bridge_liveness
    )
    if (
        str(bridge_liveness.get("effective_reviewer_mode") or "").strip()
        == "single_agent"
        and single_agent_lane_has_live_typed_authority(bridge_liveness)
    ):
        bridge_liveness["overall_state"] = _liveness.OverallLivenessState.SINGLE_AGENT_ACTIVE
