"""Typed wake-receipt models and constructors.

Extracted from `reviewer_follow_guard` so the wake-receipt schema and
its serializer can grow new optional fields without inflating the
function signature or the host file beyond shape limits.
`wake_report` is re-exported from `reviewer_follow_guard` for
backward-compatible imports.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .session_id_extractors import mapping_int_ids


@dataclass(frozen=True)
class WakeReceiptExtras:
    """Optional fields a wake report may carry beyond the core outcome.

    The core outcome (attempted/woke/reason/packet_id/requested_action)
    is always rendered. Extras are only rendered when the wake path has
    a real value to report; absent fields stay out of the JSON envelope
    so consumers can tell "not applicable in this mode" from "explicitly
    false".
    """

    target_agent: str = ""
    target_role: str = ""
    target_session_id: str = ""
    dashboard_session_id: str = ""
    wake_method: str = ""
    requested_session_visibility: str = ""
    delegated: bool | None = None
    visible_session_woke: bool | None = None
    spawned_pids: tuple[int, ...] = ()
    delivered_to_pids: tuple[int, ...] = ()
    replaced_pids: tuple[int, ...] = ()
    terminal_window_ids: tuple[int, ...] = ()
    warnings: tuple[str, ...] = ()


def wake_report(
    *,
    packet: Mapping[str, object],
    attempted: bool,
    woke: bool,
    reason: str,
    target_agent: str = "",
    extras: WakeReceiptExtras | None = None,
) -> dict[str, object]:
    """Build a typed wake-receipt envelope.

    `target_agent` stays at the top level for ergonomic call sites that
    only need provider routing. Anything else (mode, role, PIDs,
    warnings) goes into `extras` so this function stays at the
    parameter-count threshold even as the receipt schema grows.
    """
    payload = extras or WakeReceiptExtras()
    report: dict[str, object] = {
        "attempted": attempted,
        "woke": woke,
        "reason": reason,
        "packet_id": str(packet.get("packet_id") or "").strip(),
        "requested_action": str(packet.get("requested_action") or "").strip(),
    }
    if target_agent:
        report["target_agent"] = target_agent
    elif payload.target_agent:
        report["target_agent"] = payload.target_agent
    if payload.target_role:
        report["target_role"] = payload.target_role
    if payload.target_session_id:
        report["target_session_id"] = payload.target_session_id
    if payload.dashboard_session_id:
        report["dashboard_session_id"] = payload.dashboard_session_id
    if payload.wake_method:
        report["wake_method"] = payload.wake_method
    if payload.requested_session_visibility:
        report["requested_session_visibility"] = payload.requested_session_visibility
    if payload.delegated is not None:
        report["delegated"] = bool(payload.delegated)
    if payload.visible_session_woke is not None:
        report["visible_session_woke"] = bool(payload.visible_session_woke)
    if payload.spawned_pids:
        report["spawned_pids"] = list(payload.spawned_pids)
    if payload.delivered_to_pids:
        report["delivered_to_pids"] = list(payload.delivered_to_pids)
    if payload.replaced_pids:
        report["replaced_pids"] = list(payload.replaced_pids)
    if payload.terminal_window_ids:
        report["terminal_window_ids"] = list(payload.terminal_window_ids)
    if payload.warnings:
        report["warnings"] = list(payload.warnings)
    return report


def headless_launch_pids(sessions: list[dict[str, object]]) -> tuple[int, ...]:
    """Extract dedup'd headless-launch PIDs from a session list."""
    return mapping_int_ids(sessions, "headless_launch_pid")
