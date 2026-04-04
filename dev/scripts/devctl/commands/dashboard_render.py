"""Renderers for the DashboardSnapshot: terminal (ANSI), markdown, JSON."""

from __future__ import annotations

import json
from typing import Any

# ANSI escape helpers — semantic colors only
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_CYAN = "\033[36m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

# Flow stage display symbols
_FLOW_SYMBOLS = {
    "pass": f"{_GREEN}\u2713{_RESET}",
    "active": f"{_CYAN}ACTIVE{_RESET}",
    "blocked": f"{_RED}!{_RESET}",
    "unknown": f"{_DIM}\u00b7{_RESET}",
}


def render_json(snapshot: dict[str, Any]) -> str:
    """Raw DashboardSnapshot as formatted JSON."""
    return json.dumps(snapshot, indent=2)


def render_terminal(snapshot: dict[str, Any]) -> str:
    """ANSI-colored terminal dashboard output."""
    lines: list[str] = []
    _render_header_terminal(snapshot, lines)
    _render_review_terminal(snapshot, lines)
    _render_publication_terminal(snapshot, lines)
    _render_quality_terminal(snapshot, lines)
    _render_coordination_terminal(snapshot, lines)
    _render_flow_terminal(snapshot, lines)
    return "\n".join(lines)


def render_markdown(snapshot: dict[str, Any]) -> str:
    """Markdown-formatted dashboard output."""
    lines: list[str] = []
    _render_header_markdown(snapshot, lines)
    _render_review_markdown(snapshot, lines)
    _render_publication_markdown(snapshot, lines)
    _render_quality_markdown(snapshot, lines)
    _render_coordination_markdown(snapshot, lines)
    _render_flow_markdown(snapshot, lines)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Terminal renderers
# ---------------------------------------------------------------------------

def _render_header_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    repo = snapshot.get("repo", {})
    review = snapshot.get("review", {})
    mode = review.get("mode", "n/a")
    worktree = repo.get("worktree", "unknown")
    worktree_color = _GREEN if worktree == "CLEAN" else _YELLOW
    mode_color = _CYAN if mode == "active_dual_agent" else _DIM

    lines.append(f"{_BOLD}GOVERNANCE DASHBOARD{_RESET}")
    lines.append(
        f"Repo: {repo.get('name', 'unknown')}   "
        f"Branch: {repo.get('branch', 'unknown')}   "
        f"HEAD: {repo.get('head', 'unknown')}"
    )
    lines.append(
        f"Loop: {mode_color}{_loop_label(mode)}{_RESET}      "
        f"Mode: {mode}      "
        f"Worktree: {worktree_color}{worktree}{_RESET}"
    )
    lines.append("")


def _render_review_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    review = snapshot.get("review", {})
    r_state = review.get("reviewer_state", "n/a")
    i_state = review.get("implementer_state", "n/a")
    lines.append(f"{_BOLD}REVIEW{_RESET}")
    lines.append(
        f"  Reviewer       {_state_color(r_state)}{r_state.upper()}{_RESET}"
        f"       Provider: {review.get('reviewer_provider', 'n/a').title()}"
        f"      Last poll: {review.get('last_poll', 'n/a')}"
    )
    lines.append(
        f"  Implementer    {_state_color(i_state)}{i_state.upper()}{_RESET}"
        f"  Provider: {review.get('implementer_provider', 'n/a').title()}"
    )
    lines.append(f"  Current turn   {review.get('current_turn', 'n/a')}")
    instruction = review.get("instruction", "n/a")
    if instruction and instruction != "n/a":
        lines.append(f"  Instruction    {_DIM}{instruction}{_RESET}")
    lines.append("")


def _render_publication_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    pub = snapshot.get("publication", {})
    eff = pub.get("effective", "n/a")
    eff_color = _GREEN if eff == "CURRENT" else (_RED if eff in ("NOT CURRENT", "STALE") else _DIM)
    post = pub.get("post_push", "n/a")
    post_color = _GREEN if post == "PASS" else (_RED if post == "FAIL" else _DIM)

    lines.append(f"{_BOLD}PUBLICATION{_RESET}")
    lines.append(f"  Effective      {eff_color}{eff}{_RESET}")
    lines.append(f"  Why            {_DIM}{pub.get('why', 'n/a')}{_RESET}")
    lines.append(f"  Post-push      {post_color}{post}{_RESET}")
    lines.append(f"  Evidence       {_DIM}{pub.get('evidence', 'n/a')}{_RESET}")
    lines.append("")


def _render_quality_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    quality = snapshot.get("quality", {})
    lines.append(f"{_BOLD}QUALITY{_RESET}")
    for key in ("docs_gate", "plan_sync", "code_shape"):
        label = key.replace("_", " ").title()
        val = quality.get(key, "n/a")
        color = _GREEN if val == "PASS" else (_RED if val == "FAIL" else _DIM)
        lines.append(f"  {label:<14} {color}{val}{_RESET}")
    lines.append("")


def _render_coordination_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    coord = snapshot.get("coordination", {})
    findings = coord.get("pending_findings", "None")
    stripped = findings.lstrip("- ").strip()
    pending_label = "0 findings" if stripped.lower().startswith("none") else findings[:80]

    lines.append(f"{_BOLD}COORDINATION{_RESET}")
    lines.append(f"  Pending        {pending_label}")
    lines.append(f"  Next action    {coord.get('next_action', 'n/a')}")
    lines.append(f"  Instruction rev {_DIM}{coord.get('instruction_rev', 'n/a')}{_RESET}")
    lines.append("")


def _render_flow_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    flow = snapshot.get("flow", {})
    stage_order = ["review", "implement", "verify", "checkpoint", "push"]
    labels = " -> ".join(s.title() for s in stage_order)
    symbols = "    ".join(_FLOW_SYMBOLS.get(flow.get(s, "unknown"), _FLOW_SYMBOLS["unknown"]) for s in stage_order)

    lines.append(f"{_BOLD}FLOW{_RESET}")
    lines.append(f"  {labels}")
    lines.append(f"    {symbols}")
    lines.append("")


# ---------------------------------------------------------------------------
# Markdown renderers
# ---------------------------------------------------------------------------

def _render_header_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    repo = snapshot.get("repo", {})
    review = snapshot.get("review", {})
    mode = review.get("mode", "n/a")
    lines.append("# Governance Dashboard")
    lines.append("")
    lines.append(f"| Field | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Repo | {repo.get('name', 'unknown')} |")
    lines.append(f"| Branch | {repo.get('branch', 'unknown')} |")
    lines.append(f"| HEAD | {repo.get('head', 'unknown')} |")
    lines.append(f"| Loop | {_loop_label(mode)} |")
    lines.append(f"| Mode | {mode} |")
    lines.append(f"| Worktree | {repo.get('worktree', 'unknown')} |")
    lines.append("")


def _render_review_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    review = snapshot.get("review", {})
    lines.append("## Review")
    lines.append("")
    lines.append("| Role | State | Provider | Detail |")
    lines.append("|---|---|---|---|")
    lines.append(
        f"| Reviewer | {review.get('reviewer_state', 'n/a')} "
        f"| {review.get('reviewer_provider', 'n/a').title()} "
        f"| Last poll: {review.get('last_poll', 'n/a')} |"
    )
    lines.append(
        f"| Implementer | {review.get('implementer_state', 'n/a')} "
        f"| {review.get('implementer_provider', 'n/a').title()} | |"
    )
    lines.append("")
    lines.append(f"- **Current turn**: {review.get('current_turn', 'n/a')}")
    instruction = review.get("instruction", "n/a")
    if instruction and instruction != "n/a":
        lines.append(f"- **Instruction**: {instruction}")
    lines.append("")


def _render_publication_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    pub = snapshot.get("publication", {})
    lines.append("## Publication")
    lines.append("")
    lines.append(f"- **Effective**: {pub.get('effective', 'n/a')}")
    lines.append(f"- **Why**: {pub.get('why', 'n/a')}")
    lines.append(f"- **Post-push**: {pub.get('post_push', 'n/a')}")
    lines.append(f"- **Evidence**: `{pub.get('evidence', 'n/a')}`")
    lines.append("")


def _render_quality_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    quality = snapshot.get("quality", {})
    lines.append("## Quality")
    lines.append("")
    lines.append("| Gate | Status |")
    lines.append("|---|---|")
    for key in ("docs_gate", "plan_sync", "code_shape"):
        label = key.replace("_", " ").title()
        lines.append(f"| {label} | {quality.get(key, 'n/a')} |")
    lines.append("")


def _render_coordination_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    coord = snapshot.get("coordination", {})
    findings = coord.get("pending_findings", "None")
    stripped = findings.lstrip("- ").strip()
    pending_label = "0 findings" if stripped.lower().startswith("none") else findings[:80]

    lines.append("## Coordination")
    lines.append("")
    lines.append(f"- **Pending**: {pending_label}")
    lines.append(f"- **Next action**: {coord.get('next_action', 'n/a')}")
    lines.append(f"- **Instruction rev**: `{coord.get('instruction_rev', 'n/a')}`")
    lines.append("")


def _render_flow_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    flow = snapshot.get("flow", {})
    stage_order = ["review", "implement", "verify", "checkpoint", "push"]
    md_symbols = {
        "pass": "\u2705",
        "active": "\U0001f539",
        "blocked": "\u274c",
        "unknown": "\u00b7",
    }
    lines.append("## Flow")
    lines.append("")
    lines.append("| Stage | Status |")
    lines.append("|---|---|")
    for stage in stage_order:
        state = flow.get(stage, "unknown")
        symbol = md_symbols.get(state, "\u00b7")
        lines.append(f"| {stage.title()} | {symbol} {state} |")
    lines.append("")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _loop_label(mode: str) -> str:
    """Translate reviewer mode to a loop activity label."""
    if mode == "active_dual_agent":
        return "ACTIVE"
    if mode in ("single_agent", "tools_only"):
        return "INACTIVE"
    if mode in ("paused", "offline"):
        return "PAUSED"
    return "UNKNOWN"


def _state_color(state: str) -> str:
    """Pick ANSI color for a job/review state string."""
    lower = state.lower()
    if lower in ("implementing", "active", "running"):
        return _CYAN
    if lower in ("review_needed", "stale", "waiting"):
        return _YELLOW
    if lower in ("idle", "pass", "done"):
        return _GREEN
    if lower in ("blocked", "failed", "error"):
        return _RED
    return _DIM
