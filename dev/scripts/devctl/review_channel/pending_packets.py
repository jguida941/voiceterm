"""Pending review-packet helpers shared by projections and rewrite guards."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from ..repo_packs import active_path_config


@dataclass(frozen=True)
class PendingPacketQueueSnapshot:
    """Expiry-aware pending/stale packet view derived from the event log."""

    pending_packets: tuple[dict[str, object], ...]
    stale_packet_count: int = 0


def partition_live_pending_packets(
    packets: Iterable[object],
) -> tuple[list[object], list[object]]:
    """Split packets into live pending work and stale/history rows.

    Only packets with ``status == "pending"`` and a future expiry remain in the
    live actionable queue. Everything else stays in the history bucket so
    operator-facing projections can render it separately instead of mixing it
    back into the current work queue.
    """
    packet_list = list(packets)
    live_packets: list[object] = []
    stale_packets: list[object] = []
    resolved_approval_keys = {
        _approval_resolution_key(packet)
        for packet in packet_list
        if _is_applied_approval_decision(packet)
        and any(_approval_resolution_key(packet))
    }
    now = datetime.now(timezone.utc)
    for packet in packet_list:
        status = _packet_value(packet, "status")
        if str(status or "").strip() != "pending":
            continue
        if (
            _is_pending_approval_request(packet)
            and _approval_resolution_key(packet) in resolved_approval_keys
        ):
            continue
        expires_at = _parse_utc(
            str(_packet_value(packet, "expires_at_utc") or "").strip()
        )
        if expires_at is not None and expires_at <= now:
            stale_packets.append(packet)
            continue
        live_packets.append(packet)
    return live_packets, stale_packets


def _is_pending_approval_request(packet: object) -> bool:
    status = str(_packet_value(packet, "status") or "").strip()
    if status != "pending":
        return False
    if not bool(_packet_value(packet, "approval_required")):
        return False
    return _is_commit_approval_kind(packet)


def _is_applied_approval_decision(packet: object) -> bool:
    status = str(_packet_value(packet, "status") or "").strip()
    if status != "applied":
        return False
    if bool(_packet_value(packet, "approval_required")):
        return False
    return _is_commit_approval_kind(packet)


def _is_commit_approval_kind(packet: object) -> bool:
    return str(_packet_value(packet, "kind") or "").strip() == "commit_approval"


def _approval_resolution_key(packet: object) -> tuple[str, str, str, str]:
    return (
        str(_packet_value(packet, "trace_id") or "").strip(),
        str(_packet_value(packet, "kind") or "").strip(),
        str(_packet_value(packet, "target_ref") or "").strip(),
        str(_packet_value(packet, "pipeline_generation") or "").strip(),
    )


def live_pending_packets(
    packets: Iterable[object],
) -> tuple[object, ...]:
    """Return only the live actionable pending packets."""
    return tuple(partition_live_pending_packets(packets)[0])


def partition_live_packet_queue(
    packets: Iterable[object],
) -> tuple[list[object], list[object], list[object]]:
    """Split packets into live actionable rows, packet history, and stale pendings."""
    packet_list = list(packets)
    live_packets, stale_packets = partition_live_pending_packets(packet_list)
    history_packets = [
        packet
        for packet in packet_list
        if packet not in live_packets
    ]
    return live_packets, history_packets, stale_packets


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
            packets[packet_id] = dict(event)
        elif event_type in (
            "packet_acked",
            "packet_dismissed",
            "packet_expired",
            "packet_applied",
        ):
            existing = packets.get(packet_id)
            if existing is None:
                continue
            updated = dict(existing)
            updated["status"] = event_type.replace("packet_", "")
            packets[packet_id] = updated

    pending_packets, stale_packets = partition_live_pending_packets(packets.values())
    return PendingPacketQueueSnapshot(
        pending_packets=tuple(pending_packets),
        stale_packet_count=len(stale_packets),
    )


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


def _parse_utc(raw_value: str) -> datetime | None:
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _packet_value(packet: object, field_name: str) -> object:
    if isinstance(packet, Mapping):
        return packet.get(field_name)
    return getattr(packet, field_name, None)


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
