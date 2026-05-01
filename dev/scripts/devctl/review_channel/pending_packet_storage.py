"""Event-log and reviewer guard helpers for pending packets."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path

from ..repo_packs import active_path_config
from ..runtime.review_packet_inbox_liveness import is_live_control_packet
from .action_request_delivery import attach_action_request_delivery_receipts
from .packet_lifecycle import (
    ACTION_REQUEST_LIFECYCLE_EVENT_TYPES,
    apply_lifecycle_transition,
)
from .pending_packet_core import partition_live_pending_packets
from .pending_packet_models import PendingPacketQueueSnapshot


def load_pending_packets(
    repo_root: Path,
    *,
    fail_closed: bool = False,
) -> tuple[dict[str, object], ...]:
    """Return the current pending review packets from the event log."""
    return load_pending_packet_queue(
        repo_root,
        fail_closed=fail_closed,
    ).pending_packets


def load_pending_packet_queue(
    repo_root: Path,
    *,
    fail_closed: bool = False,
) -> PendingPacketQueueSnapshot:
    """Return the current pending and stale review packets from the event log."""
    config = active_path_config()
    events_path = repo_root / config.review_event_log_rel
    if not events_path.is_file():
        return PendingPacketQueueSnapshot(pending_packets=())
    try:
        events = _load_events(events_path)
    except (OSError, ValueError) as exc:
        if fail_closed:
            raise ValueError(
                "Unable to verify pending review packets before rewriting "
                f"reviewer-owned instruction state: {events_path}"
            ) from exc
        return PendingPacketQueueSnapshot(pending_packets=())

    packets: dict[str, dict[str, object]] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        packet_id = str(event.get("packet_id") or "").strip()
        event_type = str(event.get("event_type") or "").strip()
        if not packet_id:
            continue
        if event_type == "packet_posted":
            packets[packet_id] = _packet_post_snapshot(event)
        elif event_type in (
            "packet_acked",
            "packet_dismissed",
            "packet_expired",
            "packet_applied",
            *ACTION_REQUEST_LIFECYCLE_EVENT_TYPES,
        ):
            existing = packets.get(packet_id)
            if existing is None:
                continue
            packets[packet_id] = _apply_packet_transition_snapshot(
                existing,
                event,
                event_type=event_type,
            )

    hydrated_packets = attach_action_request_delivery_receipts(
        packets=tuple(packets.values()),
        artifact_root=repo_root / config.review_artifact_root_rel,
    )
    pending_packets, stale_packets = partition_live_pending_packets(hydrated_packets)
    control_packets = [
        dict(packet)
        for packet in hydrated_packets
        if is_live_control_packet(packet) or _is_recovery_control_packet(packet)
    ]
    return PendingPacketQueueSnapshot(
        pending_packets=tuple(pending_packets),
        stale_packet_count=len(stale_packets),
        control_packets=tuple(control_packets),
    )


def _packet_post_snapshot(event: Mapping[str, object]) -> dict[str, object]:
    """Normalize post rows so fast queue readers keep the event clock."""
    packet = dict(event)
    event_id = str(event.get("event_id") or "").strip()
    if event_id and not str(packet.get("latest_event_id") or "").strip():
        packet["latest_event_id"] = event_id
    timestamp = str(event.get("timestamp_utc") or "").strip()
    if timestamp and not str(packet.get("posted_at") or "").strip():
        packet["posted_at"] = timestamp
    return packet


def _apply_packet_transition_snapshot(
    packet: dict[str, object],
    event: dict[str, object],
    *,
    event_type: str,
) -> dict[str, object]:
    updated = dict(packet)
    updated.update(event)
    updated["latest_event_id"] = event.get("event_id") or packet.get("latest_event_id")
    updated["status"] = (
        _action_request_lifecycle_status(event_type)
        or event_type.replace("packet_", "")
    )
    actor = str((event.get("metadata") or {}).get("actor") or "").strip()
    transition_time = (
        event.get("timestamp_utc")
        or event.get("acked_at_utc")
        or event.get("execution_started_at_utc")
        or event.get("applied_at_utc")
    )
    if event_type == "packet_acked":
        updated["acked_by"] = actor or packet.get("to_agent")
        updated["acked_at_utc"] = transition_time
    if event_type == "packet_applied":
        updated["applied_at_utc"] = transition_time
    if str(packet.get("kind") or "").strip() == "action_request":
        if not str(updated.get("delivery_emitted_at_utc") or "").strip():
            updated["delivery_emitted_at_utc"] = (
                packet.get("delivery_emitted_at_utc")
                or packet.get("posted_at")
                or packet.get("timestamp_utc")
            )
        if event_type == "packet_acked":
            updated["execution_started_at_utc"] = transition_time
            updated["execution_started_by"] = actor or packet.get("to_agent")
        if event_type == "action_request_execution_failed":
            updated["execution_failed_at_utc"] = transition_time
            updated["execution_failed_by"] = actor or packet.get("to_agent")
            updated["execution_failed_reason"] = _event_reason(event)
        if event_type == "action_request_apply_pending_after_execution":
            updated["apply_pending_after_execution_at_utc"] = transition_time
            updated["apply_pending_after_execution_by"] = actor or packet.get("to_agent")
            updated["apply_pending_after_execution_reason"] = _event_reason(event)
        if (
            event_type == "packet_applied"
            and not str(updated.get("execution_started_at_utc") or "").strip()
        ):
            updated["execution_started_at_utc"] = transition_time
            updated["execution_started_by"] = actor or packet.get("to_agent")
    return apply_lifecycle_transition(updated, event)


def _is_recovery_control_packet(packet: Mapping[str, object]) -> bool:
    return (
        str(packet.get("kind") or "").strip() == "action_request"
        and str(packet.get("lifecycle_current_state") or "").strip()
        in {"failed", "apply_pending_after_execution"}
    )


def _event_reason(event: Mapping[str, object]) -> str:
    metadata = event.get("metadata")
    if not isinstance(metadata, Mapping):
        return ""
    return str(metadata.get("reason") or "").strip()


def _action_request_lifecycle_status(event_type: str) -> str:
    if event_type == "action_request_execution_failed":
        return "failed"
    if event_type == "action_request_apply_pending_after_execution":
        return "apply_pending_after_execution"
    return ""


def assert_no_pending_instruction_rewrite(
    *,
    repo_root: Path,
    action_label: str,
) -> None:
    """Fail closed when pending packets would be overwritten by an instruction rewrite."""
    assert_no_pending_reviewer_packets(
        repo_root=repo_root,
        action_label=action_label,
    )


def load_pending_reviewer_packets(
    repo_root: Path,
    *,
    fail_closed: bool = False,
    reviewer_agent: str = "codex",
) -> tuple[dict[str, object], ...]:
    """Return only pending packets that still target the reviewer."""
    pending_packets = load_pending_packets(repo_root, fail_closed=fail_closed)
    target = reviewer_agent.strip()
    if not target:
        return ()
    return tuple(
        packet
        for packet in pending_packets
        if _packet_target(packet) == target
    )


def assert_no_pending_reviewer_packets(
    *,
    repo_root: Path,
    action_label: str,
    reviewer_agent: str = "codex",
) -> None:
    """Fail closed when reviewer-targeted packets would be overwritten."""
    pending_packets = load_pending_reviewer_packets(
        repo_root,
        fail_closed=True,
        reviewer_agent=reviewer_agent,
    )
    if not pending_packets:
        return
    pending_summary = summarize_pending_packets(pending_packets)
    raise ValueError(
        f"Refusing {action_label} because {len(pending_packets)} pending review "
        f"packet(s) still exist for {reviewer_agent.title()} and "
        "reviewer-owned state would be overwritten. Inspect or resolve them first with "
        "`python3 dev/scripts/devctl.py review-channel --action inbox --status pending --format json`. "
        f"Pending: {pending_summary}"
    )


def summarize_pending_packets(
    packets: Iterable[dict[str, object]],
    *,
    limit: int = 3,
) -> str:
    """Return a compact operator-facing summary of pending review packets."""
    rows: list[str] = []
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        packet_id = str(packet.get("packet_id") or "").strip() or "packet"
        kind = str(packet.get("kind") or "").strip() or "packet"
        from_agent = str(packet.get("from_agent") or "").strip() or "unknown"
        to_agent = str(packet.get("to_agent") or "").strip() or "unknown"
        summary = str(packet.get("summary") or "").strip() or "(no summary)"
        rows.append(f"{packet_id} [{kind}] {from_agent}->{to_agent}: {summary}")
        if len(rows) >= limit:
            break
    if not rows:
        return "pending packet details unavailable"
    return "; ".join(rows)


def _packet_target(packet: Mapping[str, object]) -> str:
    return str(packet.get("to_agent") or "").strip()


def _load_events(events_path: Path) -> list[dict[str, object]]:
    """Load the append-only review-channel event log without importing event_store."""
    events: list[dict[str, object]] = []
    for line_number, raw_line in enumerate(
        events_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid review-channel trace event at line "
                f"{line_number}: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise ValueError(
                "Invalid review-channel trace event at line "
                f"{line_number}: expected top-level object"
            )
        events.append(payload)
    return events
