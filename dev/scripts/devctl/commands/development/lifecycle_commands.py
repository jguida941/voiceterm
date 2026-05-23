"""Command templates for `/develop` lifecycle previews."""

from __future__ import annotations

from ...runtime.typed_ids import PacketId, as_packet_id, id_text


def packet_show_command(packet_id: PacketId | str) -> str:
    """Return the exact typed packet-read command."""
    typed_packet_id = as_packet_id(packet_id)
    packet_id_text = id_text(typed_packet_id)
    if not packet_id_text:
        return ""
    return (
        "python3 dev/scripts/devctl.py review-channel --action show "
        f"--packet-id {packet_id_text} --terminal none --format md"
    )


def actor_inbox_command(actor: str) -> str:
    """Return the actor-scoped inbox command."""
    return (
        "python3 dev/scripts/devctl.py review-channel --action inbox "
        f"--target {actor} --actor {actor} --status pending --terminal none --format md"
    )


def sync_status_command() -> str:
    """Return the compact typed sync-status command."""
    return (
        "python3 dev/scripts/devctl.py review-channel --action sync-status "
        "--terminal none --format md"
    )


__all__ = ["actor_inbox_command", "packet_show_command", "sync_status_command"]
