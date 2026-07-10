"""Freeform packet-prompt heuristics for plan-authority promotion."""

from __future__ import annotations

import re
from collections.abc import Mapping

_DECISION_PROMPT_PATTERNS = (
    re.compile(r"\bwhich do you want\b", re.IGNORECASE),
    re.compile(r"\bdecision required\b", re.IGNORECASE),
    re.compile(r"\byour decide\b", re.IGNORECASE),
)
_TYPED_PLANNING_PACKET_KINDS = frozenset(
    {"decision", "plan_gap_review", "plan_patch_review", "plan_ready_gate"}
)


def contains_untyped_decision_prompt(
    packet: Mapping[str, object],
    *,
    flatten_text,
) -> bool:
    kind = str(packet.get("kind") or "").strip()
    if kind in _TYPED_PLANNING_PACKET_KINDS:
        return False
    text = " ".join(
        part
        for part in (
            flatten_text(packet.get("summary")),
            flatten_text(packet.get("body")),
            flatten_text(packet.get("requested_action")),
        )
        if part
    )
    if not text:
        return False
    if any(pattern.search(text) for pattern in _DECISION_PROMPT_PATTERNS):
        return True
    return has_enumerated_choice_block(text)


def has_enumerated_choice_block(text: str) -> bool:
    lines = [line.strip().lower() for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    starts = tuple(line_choice_marker(line) for line in lines)
    return "a" in starts and "b" in starts and "c" in starts


def line_choice_marker(line: str) -> str:
    for marker in (
        "option a",
        "option b",
        "option c",
        "a)",
        "b)",
        "c)",
        "a:",
        "b:",
        "c:",
    ):
        if line.startswith(marker):
            return marker[0]
    return ""
