"""Command routing helpers for `/develop` peer-mind context."""

from __future__ import annotations

from .lifecycle_commands import actor_inbox_command


def suggested_peer_mind_command(
    *,
    provider: str,
    actor: str,
    wake_hint: str,
) -> str:
    """Return the typed command suggested by a peer-mind wake hint."""
    if wake_hint == "peer_packet_activity":
        return actor_inbox_command(actor)
    if wake_hint == "refresh_agent_mind":
        return agent_mind_command(provider)
    return ""


def agent_mind_command(provider: str) -> str:
    return (
        "python3 dev/scripts/devctl.py agent-mind "
        f"--agent {provider} --since-cursor --project --format md --limit 20"
    )


__all__ = ["agent_mind_command", "suggested_peer_mind_command"]
