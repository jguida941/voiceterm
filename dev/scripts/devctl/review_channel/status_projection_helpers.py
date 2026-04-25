"""Helpers extracted from status_projection to stay under code-shape limits."""

from __future__ import annotations

from pathlib import Path

from ..runtime.reviewer_mode_projection import write_effective_reviewer_mode
from . import status_projection_liveness as _liveness
from .core import active_conductor_providers as _active_conductor_providers
from .reviewer_runtime_session_owner import (
    conductor_visibility as _conductor_visibility,
)
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
from .status_projection_runtime_presence import (
    apply_reviewer_activity_runtime_liveness,
    runtime_presence_projection,
)

active_conductor_providers = _active_conductor_providers
conductor_visibility = _conductor_visibility


def attach_conductor_session_state(
    *,
    bridge_liveness: dict[str, object],
    output_root: Path,
    reviewer_provider: str = "",
) -> None:
    """Compatibility wrapper that keeps patchable helper names stable.

    Tests and legacy callers patch `status_projection_helpers.active_conductor_providers`
    and `status_projection_helpers.conductor_visibility`. After the helper split,
    keep this public entrypoint routing through those names instead of the
    deeper module globals.
    """
    active_providers = list(active_conductor_providers(session_output_root=output_root))
    apply_reviewer_activity_runtime_liveness(
        bridge_liveness=bridge_liveness,
        output_root=output_root,
        reviewer_provider=reviewer_provider,
        capability_provider_fn=_liveness.capability_provider,
    )
    presence = runtime_presence_projection(
        bridge_liveness=bridge_liveness,
        active_providers=active_providers,
        output_root=output_root,
        capability_provider_fn=_liveness.capability_provider,
    )
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
    bridge_liveness["active_runtime_providers"] = presence.active_runtime_providers
    bridge_liveness["remote_control_active_providers"] = (
        presence.remote_control_active_providers
    )
    bridge_liveness["packet_activity_active_providers"] = (
        presence.packet_activity_active_providers
    )
    bridge_liveness["conductor_visibility"] = conductor_visibility(
        session_output_root=output_root
    )
    bridge_liveness["launch_truth"] = _liveness.classify_launch_truth(
        bridge_liveness
    ).value
    _liveness._degrade_active_dual_agent_freshness(bridge_liveness)
    write_effective_reviewer_mode(
        bridge_liveness,
        _liveness.effective_reviewer_mode(bridge_liveness),
    )
    if str(
        bridge_liveness.get("effective_reviewer_mode") or ""
    ).strip() == "single_agent" and single_agent_lane_has_live_typed_authority(
        bridge_liveness
    ):
        bridge_liveness["overall_state"] = (
            _liveness.OverallLivenessState.SINGLE_AGENT_ACTIVE
        )
    # Emit typed liveness signals (MP377-P1-T08)
    bridge_liveness["participant_liveness"] = _liveness._build_participant_liveness(
        bridge_liveness, active_providers
    )
