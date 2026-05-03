"""Source-identity projection helpers for packet events."""

from __future__ import annotations

from collections.abc import Mapping


def source_identity(packet: Mapping[str, object]) -> dict[str, object]:
    return source_identity_payload(packet.get("source_identity"))


def source_identity_payload(raw: object) -> dict[str, object]:
    if not isinstance(raw, Mapping):
        return {}
    return {
        str(key).strip(): str(value or "").strip()
        for key, value in raw.items()
        if str(key).strip() and str(value or "").strip()
    }
