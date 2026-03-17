"""Rendering helpers for probe design-decision packets."""

from __future__ import annotations

from typing import Any

try:
    from dev.scripts.checks.probe_report.support import (
        AllowlistEntry,
        build_design_decision_packet,
    )
except ModuleNotFoundError:  # pragma: no cover
    from probe_report.support import AllowlistEntry, build_design_decision_packet


def append_design_decision_packets_rich(
    *,
    lines: list[str],
    design_decisions: list[tuple[dict[str, Any], AllowlistEntry]],
) -> None:
    lines.extend(
        [
            "## Design Decision Packets",
            "",
            (
                "These findings stay visible because repo policy marked them as "
                "intentional design boundaries. AI agents and human reviewers "
                "should consume the same packet; `decision_mode` only controls "
                "whether the agent may auto-apply, should recommend, or must "
                "explain and wait for approval."
            ),
            "",
        ]
    )
    for hint, entry in design_decisions:
        packet = build_design_decision_packet(hint=hint, entry=entry)
        lines.extend(
            [
                f"#### [`{packet['decision_mode']}`] `{packet['file']}::{packet['symbol']}`",
                "",
                f"*Detected by `{packet['probe']}` ({packet['severity'].upper()})*",
                "",
                f"**Why it stays visible:** *{packet['rationale']}*",
                "",
            ]
        )
        lines.append("**Signals:**")
        lines.extend(f"- {signal}" for signal in packet["signals"])
        lines.extend(["", f"**AI action:** {packet['ai_instruction'] or 'Review the signals and rationale before changing this boundary.'}", ""])
        if packet["invariants"]:
            lines.append("**Invariants:**")
            lines.extend(f"- {item}" for item in packet["invariants"])
            lines.append("")
        if packet["precedent"]:
            lines.extend([f"**Precedent:** {packet['precedent']}", ""])
        if packet["research_instruction"]:
            lines.extend([f"**Follow-up question:** {packet['research_instruction']}", ""])
        if packet["validation_plan"]:
            lines.append("**Validation plan:**")
            lines.extend(f"- {step}" for step in packet["validation_plan"])
            lines.append("")
        lines.extend(["---", ""])


def append_design_decision_packets_terminal(
    *,
    lines: list[str],
    design_decisions: list[tuple[dict[str, Any], AllowlistEntry]],
) -> None:
    lines.extend(["", "-" * 60, "  DESIGN DECISION PACKETS", ""])
    for hint, entry in design_decisions:
        packet = build_design_decision_packet(hint=hint, entry=entry)
        lines.append(
            "  DP "
            + f"[{packet['decision_mode']}] "
            + f"{packet['file']}::{packet['symbol']} "
            + f"({packet['severity'].upper()})"
        )
        lines.append(f"               {packet['rationale']}")
