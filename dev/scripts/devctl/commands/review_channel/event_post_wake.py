"""Typed-attention helpers for event-backed review-channel packet posts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .event_post_wake_reports import (
    packet_delivery_recorded_without_wake,
    wake_skipped,
)


@dataclass(frozen=True)
class EventPostWakeDeps:
    """Compatibility seams retained for tests and legacy callers.

    Packet posts no longer call these dependencies. The fields stay available
    so older unit fixtures can keep proving that packet delivery does not reach
    wake/launch paths.
    """

    refresh_status_snapshot_fn: object | None = None
    scan_repo_governance_fn: object | None = None
    derive_operator_interaction_mode_fn: object | None = None
    maybe_wake_waiting_reviewer_conductor_fn: object | None = None
    maybe_wake_waiting_agent_conductor_fn: object | None = None
    load_or_refresh_event_bundle_fn: object | None = None
    append_event_fn: object | None = None
    load_events_fn: object | None = None
    refresh_event_bundle_fn: object | None = None


NON_CONDUCTOR_WAKE_TARGETS = {"", "operator", "system"}


def maybe_wake_posted_reviewer_packet(
    *,
    args,
    repo_root: Path,
    paths: Mapping[str, object],
    packet: Mapping[str, object],
    posted_review_state_payload: Mapping[str, object] | None = None,
    deps: EventPostWakeDeps | None = None,
) -> dict[str, object] | None:
    """Record packet attention without launching or replacing sessions.

    Packets are communication/provenance and plan-intake inputs. They are not
    host process authority. Session creation belongs to scheduler/runtime
    controllers after explicit task boundaries, so this legacy hook now returns
    a no-wake scheduling receipt for all provider targets.
    """

    _ = (args, repo_root, paths, posted_review_state_payload, deps)
    target_agent = str(packet.get("to_agent") or "").strip()
    skip_reason = _wake_skip_reason(packet)
    if skip_reason:
        return wake_skipped(packet=packet, reason=skip_reason)
    return packet_delivery_recorded_without_wake(
        packet=packet,
        target_agent=target_agent,
        posted_review_state_payload=posted_review_state_payload,
    )


def _wake_skip_reason(packet: Mapping[str, object]) -> str:
    target_agent = str(packet.get("to_agent") or "").strip().lower()
    if target_agent in NON_CONDUCTOR_WAKE_TARGETS:
        return "non_conductor_target"
    status = str(packet.get("status") or "").strip().lower()
    if status and status != "pending":
        return "non_pending_packet"
    return ""
