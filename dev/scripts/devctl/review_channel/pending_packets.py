"""Pending review-packet helpers shared by projections and rewrite guards."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path

from ..repo_packs import active_path_config


def load_pending_packets(
    repo_root: Path,
    *,
    fail_closed: bool = False,
) -> tuple[dict[str, object], ...]:
    """Return the current pending review packets from the event log."""
    config = active_path_config()
    events_path = repo_root / config.review_event_log_rel
    if not events_path.is_file():
        return ()
    try:
        events = _load_events(events_path)
    except (OSError, ValueError) as exc:
        if fail_closed:
            raise ValueError(
                "Unable to verify pending review packets before rewriting "
                f"reviewer-owned instruction state: {events_path}"
            ) from exc
        return ()

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
    return tuple(
        packet
        for packet in packets.values()
        if str(packet.get("status") or "pending") == "pending"
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
