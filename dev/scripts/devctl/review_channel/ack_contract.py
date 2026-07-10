"""Shared implementer ACK parsing and wording for review-channel state."""

from __future__ import annotations

import re

ACK_CONTRACT_PRIMARY_EXAMPLE = (
    "- acknowledged current instruction revision: `<current revision>`"
)
ACK_CONTRACT_LEGACY_EXAMPLE = "- acknowledged; instruction-rev: `<current revision>`"
ACK_REVISION_REQUIREMENT_PREFIX = (
    "Live implementer ACK (`Claude Ack` compatibility heading) must acknowledge "
    "the current instruction revision"
)

_LEGACY_ACK_REVISION_RE = re.compile(
    r"(?i)\binstruction(?:[-_ ]rev(?:ision)?)?\s*:\s*`?(?P<value>[a-f0-9]{8,64})`?"
)
_SEMANTIC_ACK_REVISION_RE = re.compile(
    r"(?i)\b(?:ack(?:nowledg(?:e|ed|ement))?|acked|confirm(?:ed|s)?)\b"
    r"[^\n`]{0,48}\b(?:current\s+)?instruction(?:[-_ ]rev(?:ision)?|\s+revision)\b"
    r"(?:\s+is|\s*[:=])?\s*`?(?P<value>[a-f0-9]{8,64})`?"
)
_DIRECT_REVISION_RE = re.compile(
    r"(?i)\b(?:current\s+)?instruction\s+revision\b(?:\s+is|\s*[:=])\s*"
    r"`?(?P<value>[a-f0-9]{8,64})`?"
)
_ROLLOVER_ACK_RE = re.compile(r"(?i)\brollover ack\b")


def extract_implementer_ack_revision(text: str) -> str:
    """Return the first current instruction revision acknowledged in text."""
    for raw_line in text.splitlines():
        stripped = raw_line.strip().lstrip("-").strip()
        if not stripped or _ROLLOVER_ACK_RE.search(stripped):
            continue
        for pattern in (
            _LEGACY_ACK_REVISION_RE,
            _SEMANTIC_ACK_REVISION_RE,
            _DIRECT_REVISION_RE,
        ):
            match = pattern.search(stripped)
            if match is not None:
                return match.group("value").lower()
    return ""


def ack_revision_requirement_message() -> str:
    """Return the canonical validator error for missing ACK revision state."""
    return (
        f"{ACK_REVISION_REQUIREMENT_PREFIX} (for example "
        f"`{ACK_CONTRACT_PRIMARY_EXAMPLE}` or `{ACK_CONTRACT_LEGACY_EXAMPLE}`) "
        "in active bridge mode."
    )


def ack_contract_prompt_line() -> str:
    """Return the implementer-facing ACK wording shared by prompt surfaces."""
    return (
        "- Acknowledge the live `instruction_revision` before coding. In the "
        "implementer ACK section (`Claude Ack` compatibility heading), "
        "acknowledge the current instruction revision with one machine-readable "
        "line. Accepted forms include "
        f"`{ACK_CONTRACT_PRIMARY_EXAMPLE}` or "
        f"`{ACK_CONTRACT_LEGACY_EXAMPLE}`."
    )


def packet_ack_is_transport_lifecycle_line() -> str:
    """Return the packet-vs-implementer ACK invariant for prompt surfaces."""
    return (
        "- Packet `ack`/`apply`/`dismiss` is transport lifecycle only; it does "
        "not satisfy implementer ACK, does not write `Claude Ack`, and does "
        "not make `implementer_ack_state=current`."
    )
