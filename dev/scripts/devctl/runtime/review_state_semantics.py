"""Shared semantics for typed review-state placeholder and pending values."""

from __future__ import annotations

from collections.abc import Callable


def normalize_instruction_markdown(text: str) -> str:
    """Return the canonical markdown form for live instruction text."""
    if text == "(missing)":
        return text
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not lines or not any(line.lstrip().startswith("- ") for line in lines):
        return text
    normalized: list[str] = []
    seen_bullet = False
    for line in lines:
        stripped = line.strip()
        if line.lstrip().startswith("- "):
            normalized.append(line)
            seen_bullet = True
            continue
        if not seen_bullet:
            normalized.append(f"- {stripped}")
            continue
        normalized.append(line)
    return "\n".join(normalized)


_MISSING_INSTRUCTION_MARKERS = {
    "await reviewer instruction refresh",
    "relaunch before compaction",
    "stop at a safe boundary",
}


def is_missing_instruction(text: str | None) -> bool:
    """Return True when instruction text represents no live instruction."""
    normalized = str(text or "").strip()
    if normalized in {"", "(missing)"}:
        return True
    placeholder = normalized.lstrip("-").strip().lower().rstrip(".")
    return placeholder in _MISSING_INSTRUCTION_MARKERS


def is_pending_placeholder(text: str | None) -> bool:
    """Return True when text is the canonical pending placeholder."""
    if not text:
        return False
    return text.strip().lstrip("-").strip().lower() == "pending"


def is_pending_implementer_state(
    *,
    implementer_status: str | None,
    implementer_ack: str | None,
    implementer_ack_state: str | None = "",
) -> bool:
    """Return True when the implementer was freshly reset to pending."""
    if str(implementer_ack_state or "").strip().lower() == "pending":
        return True
    return is_pending_placeholder(implementer_status) and is_pending_placeholder(
        implementer_ack
    )


def classify_implementer_ack_state(
    *,
    implementer_status: str,
    implementer_ack: str,
    implementer_ack_state: str = "",
    ack_current: bool,
    stale_label: str,
    is_substantive_text: Callable[[str | None], bool],
) -> str:
    """Return the shared typed ACK-state label for current-session consumers."""
    if is_pending_implementer_state(
        implementer_status=implementer_status,
        implementer_ack=implementer_ack,
        implementer_ack_state=implementer_ack_state,
    ):
        return "pending"
    if not is_substantive_text(implementer_ack):
        return "missing"
    if ack_current:
        return "current"
    return stale_label
