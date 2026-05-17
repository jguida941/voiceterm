"""Shared provider ids and validation for agent-facing devctl commands."""

from __future__ import annotations

import re

KNOWN_AGENT_PROVIDERS: tuple[str, ...] = (
    "codex",
    "claude",
    "cursor",
    "operator",
    "system",
    "human",
)
PROVIDER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def normalize_provider_id(value: object) -> str:
    """Normalize one provider id for typed runtime surfaces."""
    return str(value or "").strip().lower()


def is_valid_provider_id(value: object) -> bool:
    """Return whether value is a syntactically valid provider id."""
    return PROVIDER_ID_RE.fullmatch(normalize_provider_id(value)) is not None


def provider_id_error(flag: str = "--agent") -> str:
    """Return the shared provider-id validation error."""
    return f"error: {flag} must be a provider id using letters, digits, '.', '_', or '-'"


def known_provider_help() -> str:
    """Return a compact known-provider list for CLI help."""
    return ", ".join(KNOWN_AGENT_PROVIDERS)


__all__ = [
    "KNOWN_AGENT_PROVIDERS",
    "PROVIDER_ID_RE",
    "is_valid_provider_id",
    "known_provider_help",
    "normalize_provider_id",
    "provider_id_error",
]
