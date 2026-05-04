"""Next-command helpers for packet and peer attention."""

from __future__ import annotations

from .peer_mind_wake import ATTENTION_COMMAND_HINTS


def next_commands_with_attention(
    base_commands: tuple[str, ...],
    *,
    packet_attention,
    peer_minds: tuple[object, ...],
) -> tuple[str, ...]:
    commands = list(base_commands)
    if packet_attention.attention_required and packet_attention.required_command:
        commands.insert(0, packet_attention.required_command)
    for peer in peer_minds:
        command = str(getattr(peer, "suggested_command", "") or "").strip()
        hint = peer_attention_hint(peer)
        if not command or hint not in ATTENTION_COMMAND_HINTS:
            continue
        commands.append(command)
    return tuple(dict.fromkeys(commands))


def peer_attention_hint(peer: object) -> str:
    return str(
        getattr(peer, "attention_hint", "")
        or getattr(peer, "wake_hint", "")
        or ""
    ).strip()


def peer_mind_alias_warnings(peer_minds: tuple[object, ...]) -> tuple[str, ...]:
    warnings: list[str] = []
    for peer in peer_minds:
        attention_hint = str(getattr(peer, "attention_hint", "") or "").strip()
        wake_hint = str(getattr(peer, "wake_hint", "") or "").strip()
        if not attention_hint or not wake_hint or attention_hint == wake_hint:
            continue
        provider = str(getattr(peer, "provider", "") or "unknown").strip()
        warnings.append(
            "peer_mind_hint_alias_diverged:"
            f"{provider}:attention_hint={attention_hint}:wake_hint={wake_hint}"
        )
    return tuple(warnings)
