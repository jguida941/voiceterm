"""Shared loop-autonomy projection for control-plane surfaces."""

from __future__ import annotations

from collections.abc import Mapping

from .collaboration_wake_contract import LoopAutonomyState, normalize_wake_mode
from .reviewer_runtime_models import (
    RemoteControlAttachmentState,
    has_active_remote_control_attachment,
)
from .value_coercion import coerce_int, coerce_string

ControlPlaneLoopWakeState = LoopAutonomyState


def resolve_control_plane_loop_wake(
    *,
    review_state_payload: Mapping[str, object] | None,
    reviewer_mode: str,
    remote_control_attachment: RemoteControlAttachmentState | None,
    codex_conductor_alive: bool,
    claude_conductor_alive: bool,
) -> ControlPlaneLoopWakeState:
    collaboration = _mapping(
        _mapping(review_state_payload).get("collaboration")
    )
    from_collaboration = _state_from_mapping(collaboration)
    if from_collaboration is not None:
        return from_collaboration

    authority_snapshot = _mapping(
        _mapping(review_state_payload).get("authority_snapshot")
    )
    from_authority = _state_from_mapping(authority_snapshot)
    if from_authority is not None:
        return from_authority

    normalized_mode = str(reviewer_mode or "").strip() or "single_agent"
    if normalized_mode == "active_dual_agent":
        return ControlPlaneLoopWakeState(
            loop_wake_mode="unknown",
            loop_wake_interval_seconds=0,
            loop_driver_agent="multi_lane",
            loop_autonomy_ok=False,
            loop_gap_summary=(
                "active_dual_agent loop has no shared typed loop-autonomy contract yet."
            ),
        )

    if has_active_remote_control_attachment(remote_control_attachment):
        mode = normalize_wake_mode(remote_control_attachment.host_wake_mode)
        driver = (
            str(remote_control_attachment.provider or "").strip()
            or str(remote_control_attachment.role or "").strip()
        )
        if mode in {"continuous", "tick_based"}:
            return ControlPlaneLoopWakeState(
                loop_wake_mode=mode,
                loop_wake_interval_seconds=(
                    max(0, int(remote_control_attachment.wake_interval_seconds or 0))
                    if mode == "tick_based"
                    else 0
                ),
                loop_driver_agent=driver,
                loop_autonomy_ok=True,
                loop_gap_summary="",
            )
        return ControlPlaneLoopWakeState(
            loop_wake_mode=mode,
            loop_wake_interval_seconds=0,
            loop_driver_agent=driver,
            loop_autonomy_ok=False,
            loop_gap_summary=(
                f"{normalized_mode} loop depends on {driver or 'remote attachment'} "
                f"but the declared wake mode is {mode}."
            ),
        )

    if codex_conductor_alive:
        return ControlPlaneLoopWakeState(
            loop_wake_mode="continuous",
            loop_wake_interval_seconds=0,
            loop_driver_agent="codex",
            loop_autonomy_ok=True,
            loop_gap_summary="",
        )
    if claude_conductor_alive:
        return ControlPlaneLoopWakeState(
            loop_wake_mode="continuous",
            loop_wake_interval_seconds=0,
            loop_driver_agent="claude",
            loop_autonomy_ok=True,
            loop_gap_summary="",
        )

    return ControlPlaneLoopWakeState(
        loop_wake_mode="unknown",
        loop_wake_interval_seconds=0,
        loop_driver_agent="",
        loop_autonomy_ok=False,
        loop_gap_summary=(
            f"{normalized_mode} loop has no typed wake-capable owner or scheduler."
        ),
    )


def _state_from_mapping(value: Mapping[str, object]) -> ControlPlaneLoopWakeState | None:
    return ControlPlaneLoopWakeState.from_mapping(value)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
