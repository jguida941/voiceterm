"""Typed launch-truth classification for the active review loop."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Union

from ..runtime.enum_compat import StrEnum
from .conductor_authority import (
    conductor_signal_present,
    live_reviewer_conductor_present,
)
from .peer_liveness import (
    CodexPollState,
    ReviewerFreshness,
    ReviewerMode,
    normalize_reviewer_mode,
    reviewer_mode_is_active,
)


class LaunchTruthState(StrEnum):
    """Validated launchability of the active review loop."""

    INACTIVE = "inactive"
    LIVE = "live"
    RUNTIME_MISSING = "runtime_missing"
    DETACHED_RUNTIME_ONLY = "detached_runtime_only"
    HYBRID_CLAUDE_ONLY = "hybrid_claude_only"
    AUTOMATION_ONLY = "automation_only"


def classify_launch_truth(bridge_liveness: dict[str, object]) -> LaunchTruthState:
    """Classify whether the declared dual-agent loop is actually launch-valid."""
    reviewer_mode = _declared_reviewer_mode(bridge_liveness)
    if not reviewer_mode_is_active(reviewer_mode):
        if _typed_dual_agent_runtime_promotes_mode(
            bridge_liveness,
            reviewer_mode=reviewer_mode,
        ):
            return LaunchTruthState.LIVE
        return LaunchTruthState.INACTIVE
    if _typed_dual_agent_runtime_is_live(bridge_liveness):
        return LaunchTruthState.LIVE
    if not (
        bool(bridge_liveness.get("publisher_running"))
        or bool(bridge_liveness.get("reviewer_supervisor_running"))
    ):
        return LaunchTruthState.RUNTIME_MISSING
    if not conductor_signal_present(bridge_liveness):
        return LaunchTruthState.LIVE
    codex_conductor_active = live_reviewer_conductor_present(bridge_liveness)
    claude_conductor_active = bool(bridge_liveness.get("claude_conductor_active"))
    if not codex_conductor_active and not claude_conductor_active:
        return LaunchTruthState.DETACHED_RUNTIME_ONLY
    if claude_conductor_active and not codex_conductor_active:
        return LaunchTruthState.HYBRID_CLAUDE_ONLY
    if codex_conductor_active and bool(
        bridge_liveness.get("poll_status_automation_only")
    ):
        return LaunchTruthState.AUTOMATION_ONLY
    return LaunchTruthState.LIVE


def _typed_dual_agent_runtime_is_live(
    bridge_liveness: Mapping[str, object],
) -> bool:
    providers = set(_string_values(bridge_liveness.get("active_runtime_providers")))
    remote_control_providers = set(
        _string_values(bridge_liveness.get("remote_control_active_providers"))
    )
    providers.update(remote_control_providers)
    providers.update(
        _string_values(bridge_liveness.get("packet_activity_active_providers"))
    )
    reviewer_authority_providers = set(
        _string_values(bridge_liveness.get("active_conductor_providers"))
    )
    reviewer_authority_providers.update(remote_control_providers)
    reviewer_provider = (
        capability_provider(bridge_liveness, "reviewer_capability") or "codex"
    )
    if (
        _declared_reviewer_mode(bridge_liveness) == ReviewerMode.TOOLS_ONLY.value
        and bool(bridge_liveness.get("reviewer_activity_active"))
    ):
        reviewer_activity_provider = str(
            bridge_liveness.get("reviewer_activity_provider") or ""
        ).strip().lower()
        if reviewer_activity_provider:
            reviewer_authority_providers.add(reviewer_activity_provider)
    implementer_provider = (
        capability_provider(bridge_liveness, "implementer_capability") or "claude"
    )
    if reviewer_provider not in reviewer_authority_providers:
        return False
    reviewer_live = bool(bridge_liveness.get("reviewer_activity_active")) or (
        reviewer_provider in providers
    )
    implementer_live = implementer_provider in providers or bool(
        _string_values(bridge_liveness.get("remote_control_active_providers"))
    )
    if not reviewer_live or not implementer_live:
        return False
    freshness = str(bridge_liveness.get("reviewer_freshness") or "").strip()
    poll_state = str(bridge_liveness.get("codex_poll_state") or "").strip()
    return (
        freshness
        not in {
            ReviewerFreshness.MISSING.value,
            ReviewerFreshness.OVERDUE.value,
        }
        and poll_state != CodexPollState.MISSING.value
    )


def _string_values(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple, set)):
        return ()
    result: list[str] = []
    for item in value:
        text = str(item or "").strip().lower()
        if text and text not in result:
            result.append(text)
    return tuple(result)


def capability_provider(
    payload: Mapping[str, object],
    field_name: str,
) -> str:
    capability = payload.get(field_name)
    if not isinstance(capability, Mapping):
        return ""
    return str(capability.get("provider") or "").strip().lower()


def build_launch_probe_state(
    bridge_liveness,
    active_providers: set[str],
    status_dir: Union[str, Path],
) -> dict[str, object]:
    """Assemble the dict that :func:`classify_launch_truth` reads.

    Kept next to the classifier so schema changes stay co-located.
    """
    from .lifecycle_state import read_publisher_state, read_reviewer_supervisor_state

    return dict(
        reviewer_mode=bridge_liveness.reviewer_mode,
        poll_status_automation_only=bridge_liveness.poll_status_automation_only,
        publisher_running=bool(read_publisher_state(status_dir).get("running")),
        reviewer_supervisor_running=bool(
            read_reviewer_supervisor_state(status_dir).get("running")
        ),
        active_conductor_providers=list(active_providers),
        codex_conductor_active="codex" in active_providers,
        claude_conductor_active="claude" in active_providers,
    )


def effective_reviewer_mode(bridge_liveness: Mapping[str, object]) -> str:
    """Return the validated reviewer mode for live-authority consumers."""

    reviewer_mode = _declared_reviewer_mode(bridge_liveness)
    if not reviewer_mode_is_active(reviewer_mode):
        if _typed_dual_agent_runtime_promotes_mode(
            bridge_liveness,
            reviewer_mode=reviewer_mode,
        ):
            return ReviewerMode.ACTIVE_DUAL_AGENT.value
        return reviewer_mode

    launch_truth = str(
        bridge_liveness.get("launch_truth")
        or classify_launch_truth(dict(bridge_liveness)).value
    )
    if launch_truth == LaunchTruthState.LIVE.value:
        return reviewer_mode
    return ReviewerMode.TOOLS_ONLY.value


def _declared_reviewer_mode(bridge_liveness: Mapping[str, object]) -> str:
    raw_mode = str(
        bridge_liveness.get("declared_reviewer_mode")
        or bridge_liveness.get("reviewer_mode")
        or ""
    ).strip()
    if not raw_mode:
        return ReviewerMode.TOOLS_ONLY.value
    return normalize_reviewer_mode(raw_mode).value


def _typed_dual_agent_runtime_promotes_mode(
    bridge_liveness: Mapping[str, object],
    *,
    reviewer_mode: str,
) -> bool:
    if reviewer_mode != ReviewerMode.TOOLS_ONLY.value:
        return False
    return _typed_dual_agent_runtime_is_live(bridge_liveness)
