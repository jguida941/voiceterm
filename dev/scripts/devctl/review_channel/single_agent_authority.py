"""Shared single-agent typed-authority predicates."""

from __future__ import annotations

from collections.abc import Mapping


def single_agent_lane_has_live_typed_authority(
    bridge_liveness: Mapping[str, object],
) -> bool:
    providers = bridge_liveness.get("active_conductor_providers")
    if isinstance(providers, (list, tuple)):
        normalized = [
            str(provider).strip().lower()
            for provider in providers
            if str(provider).strip()
        ]
        if normalized:
            return True
    if bool(bridge_liveness.get("codex_conductor_active")):
        return True
    if bool(bridge_liveness.get("claude_conductor_active")):
        return True
    if str(bridge_liveness.get("implementer_ack_state") or "").strip().lower() == "current":
        return bool(bridge_liveness.get("claude_status_present"))
    return bool(bridge_liveness.get("claude_status_present")) and bool(
        bridge_liveness.get("claude_ack_current")
    )
