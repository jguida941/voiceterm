"""Mandate timestamp enforcement helpers for substrate commit checks."""

from __future__ import annotations

from datetime import datetime, timezone

from dev.scripts.devctl.runtime.repo_portability import GuardMandate


def commit_is_enforced(committed_at: str, *, mandate: GuardMandate) -> bool:
    if not mandate.observed_at_utc:
        return True
    if not committed_at:
        return True
    return normalize_timestamp(committed_at) >= normalize_timestamp(
        mandate.observed_at_utc
    )


def normalize_timestamp(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
