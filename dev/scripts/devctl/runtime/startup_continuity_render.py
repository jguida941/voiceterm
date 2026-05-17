"""Render compact startup/session continuity attention packets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def append_continuity_attention_lines(
    lines: list[str],
    attention: Mapping[str, object] | None,
    *,
    startup_command: str = "",
    session_resume_command: str = "",
    status_command: str = "",
    context_graph_command: str = "",
) -> None:
    """Append a concise post-compaction attention section when state exists."""
    if not isinstance(attention, Mapping) or not attention:
        return
    lines.extend(["", "### Continuity Attention"])
    message = str(attention.get("message") or "").strip()
    if message:
        lines.append(f"- **message**: {message}")
    lines.append(
        "- **runtime_spine**: "
        f"{'ok' if bool(attention.get('runtime_spine_ok', False)) else 'attention'}; "
        f"risky_items={int(attention.get('runtime_spine_risky_item_count') or 0)}; "
        f"violations={int(attention.get('runtime_spine_violation_count') or 0)}"
    )
    packet_debt_count = int(attention.get("packet_debt_count") or 0)
    packet_ids = _string_sequence(attention.get("packet_debt_ids"))
    debt_suffix = f" ids={', '.join(packet_ids)}" if packet_ids else ""
    lines.append(
        f"- **packet_carry_forward_debt**: {packet_debt_count}{debt_suffix}"
    )
    sink_counts = attention.get("packet_continuity_sink_counts")
    if isinstance(sink_counts, Mapping) and sink_counts:
        counts_text = ", ".join(
            f"{key}={int(value or 0)}"
            for key, value in sorted(sink_counts.items())
        )
        digest = str(attention.get("packet_continuity_digest") or "").strip()
        digest_text = f" digest={digest[:24]}" if digest else ""
        lines.append(f"- **packet_continuity**: {counts_text}{digest_text}")
    for item in _mapping_sequence(attention.get("runtime_spine_attention_items")):
        name = str(item.get("name") or "").strip()
        status = str(item.get("status") or "").strip()
        owner_refs = _string_sequence(item.get("owner_refs"))
        if not name:
            continue
        owner_text = ", ".join(owner_refs) if owner_refs else "unowned"
        lines.append(f"- **runtime_spine_item**: `{name}` {status} owner={owner_text}")
    commands = tuple(
        command
        for command in (
            startup_command,
            session_resume_command,
            status_command,
            context_graph_command,
        )
        if command
    )
    if commands:
        lines.append("- **resume_order**:")
        for index, command in enumerate(commands, start=1):
            lines.append(f"  {index}. `{command}`")


def continuity_attention_summary(attention: Mapping[str, object] | None) -> str:
    """Return one terminal-summary line for continuity attention."""
    if not isinstance(attention, Mapping) or not attention:
        return "continuity_attention=none"
    return (
        "continuity_attention="
        f"{bool(attention.get('requires_attention', False))}:"
        f"runtime_risky={int(attention.get('runtime_spine_risky_item_count') or 0)}:"
        f"packet_debt={int(attention.get('packet_debt_count') or 0)}:"
        f"packet_sinks={_sink_summary(attention.get('packet_continuity_sink_counts'))}"
    )


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(row for row in value if isinstance(row, Mapping))


def _string_sequence(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _sink_summary(value: object) -> str:
    if not isinstance(value, Mapping) or not value:
        return "none"
    return ",".join(f"{key}:{int(count or 0)}" for key, count in sorted(value.items()))


__all__ = ["append_continuity_attention_lines", "continuity_attention_summary"]
