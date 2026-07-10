"""Shared bridge-projection section constants."""

from __future__ import annotations

BRIDGE_SECTION_ORDER = (
    "Operator Direction",
    "Poll Status",
    "Current Verdict",
    "Open Findings",
    "Implementer Status",
    "Implementer Questions",
    "Implementer Ack",
    "Current Instruction For Implementer",
    "Last Reviewed Scope",
    "Action Requests",
)
_OPTIONAL_BRIDGE_SECTIONS = {"Operator Direction", "Action Requests"}
FLAT_BRIDGE_SECTION_ORDER = tuple(
    heading for heading in BRIDGE_SECTION_ORDER
    if heading not in _OPTIONAL_BRIDGE_SECTIONS
)
