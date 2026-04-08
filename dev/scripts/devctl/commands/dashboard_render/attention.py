"""Extracted renderers for the DashboardSnapshot.

Contains attention, pending-packet, doctor, and flow renderers extracted
from ``dashboard_render.py`` to keep that file within its hard growth lock
and reduce its mixed-concern cluster count.
"""

from __future__ import annotations

import re
from typing import Any

# Reuse ANSI constants from the main render module.
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_CYAN = "\033[36m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def render_typed_attention_terminal(
    snapshot: dict[str, Any], lines: list[str],
) -> None:
    """ATTENTION: typed recovery/attention state from ReviewState when present."""
    attn = snapshot.get("typed_attention")
    if not attn or not isinstance(attn, dict):
        return
    status = attn.get("status", "n/a")
    if status in ("n/a", "healthy"):
        return
    owner = attn.get("owner", "n/a")
    summary = attn.get("summary", "")
    action = attn.get("recommended_action", "")
    command = attn.get("recommended_command", "")
    status_color = _RED if "recovery" in status or "relaunch" in status else _YELLOW
    lines.append(f"{_BOLD}ATTENTION{_RESET}")
    lines.append(f"  Status     {status_color}{status}{_RESET}")
    lines.append(f"  Owner      {owner}")
    if summary:
        lines.append(f"  Summary    {_DIM}{summary[:80]}{_RESET}")
    if action:
        lines.append(f"  Action     {action[:60]}")
    if command:
        lines.append(f"  Command    {_CYAN}{command}{_RESET}")
    lines.append("")


def render_typed_attention_markdown(
    snapshot: dict[str, Any], lines: list[str],
) -> None:
    """Markdown attention section from typed ReviewState when present."""
    attn = snapshot.get("typed_attention")
    if not attn or not isinstance(attn, dict):
        return
    status = attn.get("status", "n/a")
    if status in ("n/a", "healthy"):
        return
    lines.append("## Attention")
    lines.append("")
    lines.append(f"- **Status**: {status}")
    lines.append(f"- **Owner**: {attn.get('owner', 'n/a')}")
    summary = attn.get("summary", "")
    if summary:
        lines.append(f"- **Summary**: {summary[:80]}")
    action = attn.get("recommended_action", "")
    if action:
        lines.append(f"- **Action**: {action[:60]}")
    command = attn.get("recommended_command", "")
    if command:
        lines.append(f"- **Command**: `{command}`")
    lines.append("")


def render_pending_packets_terminal(
    snapshot: dict[str, Any], lines: list[str],
) -> None:
    """Inline pending packets under COORDINATION when present."""
    packets = snapshot.get("pending_packets", [])
    if not packets:
        return
    for pkt in packets[:5]:
        kind = pkt.get("kind", "?")
        summary = pkt.get("summary", "")[:60]
        to_agent = pkt.get("to_agent", "?")
        approval = f" {_RED}[approval]{_RESET}" if pkt.get("approval_required") else ""
        lines.append(
            f"  {_YELLOW}PKT{_RESET}  {kind} -> {to_agent}: {summary}{approval}"
        )


def render_doctor_terminal(
    coord: dict[str, Any], lines: list[str],
) -> None:
    """Doctor status and blocked reason under COORDINATION."""
    doctor_status = coord.get("doctor_status", "n/a")
    doctor_blocked = coord.get("doctor_blocked", "none")
    if doctor_status == "n/a":
        return
    doc_color = _GREEN if doctor_blocked == "none" else _RED
    lines.append(f"  Doctor     {doc_color}{doctor_status}{_RESET}")
    if doctor_blocked and doctor_blocked != "none":
        lines.append(f"  Blocked    {_RED}{doctor_blocked}{_RESET}")


def render_doctor_markdown(
    coord: dict[str, Any], lines: list[str],
) -> None:
    """Doctor status and blocked reason for markdown coordination section."""
    doctor_status = coord.get("doctor_status", "n/a")
    doctor_blocked = coord.get("doctor_blocked", "none")
    if doctor_status == "n/a":
        return
    lines.append(f"- **Doctor**: {doctor_status}")
    if doctor_blocked and doctor_blocked != "none":
        lines.append(f"- **Blocked**: {doctor_blocked}")


def render_pending_packets_markdown(
    snapshot: dict[str, Any], lines: list[str],
) -> None:
    """Pending packets for the markdown coordination section."""
    packets = snapshot.get("pending_packets", [])
    if not packets:
        return
    lines.append("")
    lines.append("**Pending packets**:")
    lines.append("")
    for pkt in packets[:5]:
        kind = pkt.get("kind", "?")
        summary = pkt.get("summary", "")[:60]
        to_agent = pkt.get("to_agent", "?")
        approval = " *[approval required]*" if pkt.get("approval_required") else ""
        lines.append(f"- `{kind}` -> {to_agent}: {summary}{approval}")


# ---------------------------------------------------------------------------
# Flow pipeline renderers (extracted from dashboard_render)
# ---------------------------------------------------------------------------

_ANSI_RE = re.compile(r"\033\[[^m]*m")

_FLOW_SYMBOLS = {
    "pass": f"{_GREEN}\u2713{_RESET}",
    "active": f"{_CYAN}ACTIVE{_RESET}",
    "blocked": f"{_RED}!{_RESET}",
    "unknown": f"{_DIM}\u00b7{_RESET}",
}


def visible_len(s: str) -> int:
    """Length of a string excluding ANSI escape sequences."""
    return len(_ANSI_RE.sub("", s))


def align_flow_symbols(stages: list[str], symbols: list[str]) -> str:
    """Pad flow symbols to align under their stage labels."""
    parts = []
    for i, (stage, sym) in enumerate(zip(stages, symbols)):
        parts.append(sym)
        if i < len(stages) - 1:
            gap = len(stage) + 5 - visible_len(sym)
            parts.append(" " * max(1, gap))
    return "".join(parts)


def render_flow_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """FLOW: horizontal pipeline with status symbols underneath."""
    flow = snapshot.get("flow", {})
    stage_order = ["review", "implement", "verify", "checkpoint", "push"]
    label_parts = []
    for i, s in enumerate(stage_order):
        label_parts.append(s.title())
        if i < len(stage_order) - 1:
            label_parts.append(" \u2500\u2500> ")
    labels = "".join(label_parts)
    symbols = [_FLOW_SYMBOLS.get(flow.get(s, "unknown"), _FLOW_SYMBOLS["unknown"]) for s in stage_order]
    padded = align_flow_symbols(stage_order, symbols)
    lines.append(f"{_BOLD}FLOW{_RESET}")
    lines.append(f"  {labels}")
    lines.append(f"    {padded}")
    lines.append("")


def render_flow_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    """FLOW: markdown table with stage status symbols."""
    flow = snapshot.get("flow", {})
    stage_order = ["review", "implement", "verify", "checkpoint", "push"]
    md_symbols = {"pass": "\u2705", "active": "\U0001f539", "blocked": "\u274c", "unknown": "\u00b7"}
    lines.append("## Flow")
    lines.append("")
    lines.append("| Stage | Status |")
    lines.append("|---|---|")
    for stage in stage_order:
        state = flow.get(stage, "unknown")
        symbol = md_symbols.get(state, "\u00b7")
        lines.append(f"| {stage.title()} | {symbol} {state} |")
    lines.append("")
