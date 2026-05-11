"""Presentation-only labels for typed runtime compatibility vocabulary."""

from __future__ import annotations

_ACTION_LABELS = {
    "continue_to_goal": "Continue to typed goal",
    "Continue to goal": "Continue to typed goal",
    "Continue to the typed goal": "Continue to typed goal",
    "triage_pending_packet": "Continue to typed goal",
    "triage_packet": "Continue to typed goal",
    "pivot_to_packet": "Continue to typed goal",
    "manual-triage-required": "manual review required",
    "manual_triage_required": "manual review required",
    "operator_triage": "operator review",
    "operator_packet_triage": "operator packet review",
}

_REASON_LABELS = {
    "wake_required": "peer input pending",
    "pivot_required": "focus change required",
    "finding_pending": "review finding pending",
    "packet_pending": "inbox item pending",
    "packet_attention_required": "inbox attention required",
    "peer_input_required": "peer input pending",
    "peer_input_before_blocker": "peer input before blocker",
    "triage_pending_packet": "continue to typed goal",
    "triage_packet": "continue to typed goal",
    "pivot_to_packet": "continue to typed goal",
    "manual-triage-required": "manual review required",
    "manual_triage_required": "manual review required",
    "Active dual-agent mode still requires live reviewer and implementer conductor sessions.": (
        "Compatibility reviewer mode still requires live reviewer and implementer conductor sessions."
    ),
}


def action_label(value: object) -> str:
    """Return a human label for an action while keeping typed data unchanged."""
    text = _text(value)
    return _ACTION_LABELS.get(text, _humanize(text))


def reason_label(value: object) -> str:
    """Return a human label for a reason/status while keeping typed data unchanged."""
    text = _text(value)
    if text in _REASON_LABELS:
        return _REASON_LABELS[text]
    if ";" in text:
        return "; ".join(reason_label(part) for part in text.split(";"))
    if ":" in text:
        prefix, suffix = text.split(":", 1)
        return f"{_humanize(prefix)}: {reason_label(suffix)}"
    return _humanize(text)


def text_label(value: object) -> str:
    """Humanize a generic typed value for Markdown surfaces."""
    return _humanize(_text(value))


def _humanize(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if " " in text:
        return text
    return text.replace("_", " ").replace("-", " ")


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["action_label", "reason_label", "text_label"]
