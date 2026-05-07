"""Command rendering for packet attention follow-ups."""

from __future__ import annotations


def required_command_for_record(
    record,
    *,
    pending_packet_ids: tuple[str, ...],
    latest_finding_packet_id: str,
    fallback_command: str = "",
) -> str:
    command = fallback_command or str(record.required_command or "").strip()
    if record.wake_reason == "finding_pending":
        packet_id = latest_finding_packet_id or (
            pending_packet_ids[0] if pending_packet_ids else ""
        )
        if packet_id:
            return show_packet_command(packet_id)
    if record.wake_reason != "expired_unresolved_packet":
        return command
    if pending_packet_ids or latest_finding_packet_id:
        return command
    return "python3 dev/scripts/devctl.py develop audit-packets --format md"


def show_packet_command(packet_id: str) -> str:
    return (
        "python3 dev/scripts/devctl.py review-channel --action show "
        f"--packet-id {packet_id} --terminal none --format md"
    )


__all__ = ["required_command_for_record", "show_packet_command"]
