"""Packet-attention checks for session termination policy."""

from __future__ import annotations

from collections.abc import Mapping


def packet_attention_blocks_task_complete(attention: Mapping[str, object]) -> bool:
    return (
        _int(attention.get("pending_packet_count")) > 0
        or truthy(attention.get("wake_required"))
        or truthy(attention.get("pivot_required"))
    )


def truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value).lower() in {"1", "true", "yes", "on"}


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
