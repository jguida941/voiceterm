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

# Dashboard total width for right-alignment
_WIDTH = 72


def render_json(snapshot: dict[str, Any]) -> str:
    """Raw DashboardSnapshot as formatted JSON."""
    return json.dumps(snapshot, indent=2)


def render_terminal(snapshot: dict[str, Any]) -> str:
    """ANSI-colored dense multi-column terminal dashboard output."""
    lines: list[str] = []
    _render_header_terminal(snapshot, lines)
    _render_now_terminal(snapshot, lines)
    _render_workers_terminal(snapshot, lines)
    _render_plan_terminal(snapshot, lines)
    _render_publication_terminal(snapshot, lines)
    _render_quality_terminal(snapshot, lines)
    _render_coordination_terminal(snapshot, lines)
    _render_flow_terminal(snapshot, lines)
    return "\n".join(lines)


def render_markdown(snapshot: dict[str, Any]) -> str:
    """Markdown-formatted dashboard output."""
    lines: list[str] = []
    _render_header_markdown(snapshot, lines)
    _render_now_markdown(snapshot, lines)
    _render_workers_markdown(snapshot, lines)
    _render_plan_markdown(snapshot, lines)
    _render_publication_markdown(snapshot, lines)
    _render_quality_markdown(snapshot, lines)
    _render_coordination_markdown(snapshot, lines)
    _render_flow_markdown(snapshot, lines)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Terminal renderers — dense multi-column layout
# ---------------------------------------------------------------------------

def _render_header_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """Header: title, repo identity, loop state — all on three lines."""
    repo = snapshot.get("repo", {})
    review = snapshot.get("review", {})
    mode = review.get("mode", "n/a")
    worktree = repo.get("worktree", "unknown")
    worktree_color = _GREEN if worktree == "CLEAN" else _YELLOW
    mode_color = _CYAN if mode == "active_dual_agent" else _DIM

    title = f"{_BOLD}GOVERNANCE DASHBOARD{_RESET}"
    refresh = f"{_DIM}refresh: --{_RESET}"
    lines.append(f"{title}{' ' * max(1, _WIDTH - 20 - 12)}{refresh}")
    lines.append(
        f"Repo: {repo.get('name', 'unknown')}   "
        f"Branch: {repo.get('branch', 'unknown')}   "
        f"HEAD: {repo.get('head', 'unknown')}"
    )
    mode_label = _mode_display(mode)
    lines.append(
        f"Loop: {mode_color}{_loop_label(mode)}{_RESET}      "
        f"Mode: {mode_label}      "
        f"Worktree: {worktree_color}{worktree}{_RESET}"
    )
    lines.append("")


def _render_now_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """NOW section: who owns the loop, what to do next, top blocker."""
    now = snapshot.get("now", {})
    if not now:
        return
    owner = now.get("owner", "n/a")
    provider = now.get("owner_provider", "")
    provider_label = f" ({provider.title()})" if provider and provider != "n/a" else ""

    lines.append(f"{_BOLD}NOW{_RESET}")
    lines.append(f"  Owner          {_CYAN}{owner}{_RESET}{_DIM}{provider_label}{_RESET}")
    lines.append(f"  Next action    {now.get('next_action', 'n/a')}")
    blocker = now.get("top_blocker", "none")
    blocker_color = _RED if blocker != "none" else _GREEN
    lines.append(f"  Top blocker    {blocker_color}{blocker}{_RESET}")
    lines.append(f"  Last change    {now.get('last_change_label', '--')}")
    lines.append("")


def _render_workers_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """WORKERS table: columnar display of all registered agents."""
    workers = snapshot.get("workers", [])
    if not workers:
        lines.append(f"{_BOLD}WORKERS{_RESET}")
        lines.append(f"  {_DIM}(no workers registered){_RESET}")
        lines.append("")
        return

    lines.append(f"{_BOLD}WORKERS{_RESET}")
    lines.append(
        f"  {'ID':<5}{'Scope':<35}{'State':<15}{'Age':<8}{'Last update'}"
    )
    for w in workers:
        state = w.get("state", "UNKNOWN")
        color = _state_color(state)
        lines.append(
            f"  {w.get('id', '?'):<5}"
            f"{w.get('scope', 'unknown'):<35}"
            f"{color}{state:<15}{_RESET}"
            f"{w.get('age', '--'):<8}"
            f"{w.get('last_update', '')}"
        )
    lines.append("")


def _render_plan_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """PLAN section: current slice, progress, findings count."""
    plan = snapshot.get("plan", {})
    lines.append(f"{_BOLD}PLAN{_RESET}")
    lines.append(f"  Slice          {plan.get('slice', 'n/a')}")
    lines.append(f"  Progress       {plan.get('progress', 'n/a')}")
    findings = plan.get("open_findings", 0)
    f_color = _YELLOW if findings > 0 else _GREEN
    lines.append(f"  Open findings  {f_color}{findings}{_RESET}")
    lines.append(f"  Pending        {plan.get('pending', 0)}")
    lines.append("")


def _render_publication_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """PUBLICATION: state, target match grid, why-not-green, evidence."""
    pub = snapshot.get("publication", {})
    state = pub.get("state", pub.get("effective", "n/a"))
    state_color = _GREEN if "CURRENT" in str(state) and "NOT" not in str(state) else _RED

    lines.append(f"{_BOLD}PUBLICATION{_RESET}")
    lines.append(f"  State          {state_color}{state}{_RESET}")

    # Target match line
    tm = pub.get("target_match", {})
    match_parts = []
    for key in ("branch", "head", "target", "remote"):
        val = tm.get(key, False)
        symbol = f"{_GREEN}\u2713{_RESET}" if val else f"{_RED}\u2717{_RESET}"
        match_parts.append(f"{key} {symbol}")
    lines.append(f"  Target match   {'  '.join(match_parts)}")

    why = pub.get("why", "n/a")
    if why != "n/a" and "CURRENT" not in str(state):
        lines.append(f"  Why not green  {_DIM}{why}{_RESET}")
    lines.append(f"  Evidence       {_DIM}{pub.get('evidence', 'n/a')}{_RESET}")
    lines.append("")


def _render_quality_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """QUALITY: multi-column gate display, 2-3 gates per line."""
    quality = snapshot.get("quality", {})

    # Gate layout: pairs of (label, key)
    gate_rows = [
        [("Docs", "docs_gate"), ("Plan sync", "plan_sync"), ("Bridge", "bridge")],
        [("Shape", "code_shape"), ("Instr sync", "instr_sync"), ("Clippy", "clippy")],
    ]

    lines.append(f"{_BOLD}QUALITY{_RESET}")
    for row in gate_rows:
        parts = []
        for label, key in row:
            val = quality.get(key, "n/a")
            color = _gate_color(val)
            parts.append(f"{label:<10}{color}{val:<8}{_RESET}")
        lines.append(f"  {''.join(parts)}")

    # Failing files
    failing = quality.get("failing", [])
    if failing:
        lines.append(f"  {_RED}Failing{_RESET}   {failing[0]}")
        for f in failing[1:3]:
            lines.append(f"            {f}")
    lines.append("")


def _render_coordination_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """COORDINATION: compact 2-field-per-line layout."""
    coord = snapshot.get("coordination", {})

    pending = coord.get("pending_packets", 0)
    instr_rev = coord.get("instruction_rev", "n/a")
    rev_age = coord.get("reviewer_age", "--")
    impl_state = coord.get("implementer_state", "n/a")
    impl_color = _GREEN if impl_state == "current" else _YELLOW

    lines.append(f"{_BOLD}COORDINATION{_RESET}")
    lines.append(
        f"  Packets    {pending} pending    "
        f"Instruction rev  {_DIM}{instr_rev}{_RESET}"
    )
    lines.append(
        f"  Reviewer   {rev_age}      "
        f"Implementer      {impl_color}{impl_state}{_RESET}"
    )
    lines.append("")


def _render_flow_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """FLOW: horizontal pipeline with status symbols underneath."""
    flow = snapshot.get("flow", {})
    stage_order = ["review", "implement", "verify", "checkpoint", "push"]

    # Build the pipeline labels with arrows
    label_parts = []
    for i, s in enumerate(stage_order):
        label_parts.append(s.title())
        if i < len(stage_order) - 1:
            label_parts.append(" \u2500\u2500> ")
    labels = "".join(label_parts)

    # Build symbols aligned under each label
    symbols = []
    for s in stage_order:
        state = flow.get(s, "unknown")
        sym = _FLOW_SYMBOLS.get(state, _FLOW_SYMBOLS["unknown"])
        symbols.append(sym)
    # Pad symbols to roughly align under stage names
    padded = _align_flow_symbols(stage_order, symbols)

    lines.append(f"{_BOLD}FLOW{_RESET}")
    lines.append(f"  {labels}")
    lines.append(f"    {padded}")
    lines.append("")


def _align_flow_symbols(stages: list[str], symbols: list[str]) -> str:
    """Pad flow symbols to align under their stage labels."""
    parts = []
    for i, (stage, sym) in enumerate(zip(stages, symbols)):
        parts.append(sym)
        if i < len(stages) - 1:
            # Pad to match label width plus arrow width
            gap = len(stage) + 5 - _visible_len(sym)
            parts.append(" " * max(1, gap))
    return "".join(parts)


def _visible_len(s: str) -> int:
    """Length of a string excluding ANSI escape sequences."""
    import re
    return len(re.sub(r"\033\[[^m]*m", "", s))


# ---------------------------------------------------------------------------
# Markdown renderers
# ---------------------------------------------------------------------------

def _render_header_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    repo = snapshot.get("repo", {})
    review = snapshot.get("review", {})
    mode = review.get("mode", "n/a")
    lines.append("# Governance Dashboard")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| Repo | {repo.get('name', 'unknown')} |")
    lines.append(f"| Branch | {repo.get('branch', 'unknown')} |")
    lines.append(f"| HEAD | {repo.get('head', 'unknown')} |")
    lines.append(f"| Loop | {_loop_label(mode)} |")
    lines.append(f"| Mode | {_mode_display(mode)} |")
    lines.append(f"| Worktree | {repo.get('worktree', 'unknown')} |")
    lines.append("")


def _render_now_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    now = snapshot.get("now", {})
    if not now:
        return
    lines.append("## Now")
    lines.append("")
    lines.append(f"- **Owner**: {now.get('owner', 'n/a')}")
    lines.append(f"- **Next action**: {now.get('next_action', 'n/a')}")
    lines.append(f"- **Top blocker**: {now.get('top_blocker', 'none')}")
    lines.append(f"- **Last change**: {now.get('last_change_label', '--')}")
    lines.append("")


def _render_workers_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    workers = snapshot.get("workers", [])
    lines.append("## Workers")
    lines.append("")
    if not workers:
        lines.append("_(no workers registered)_")
        lines.append("")
        return
    lines.append("| ID | Scope | State | Age | Last update |")
    lines.append("|---|---|---|---|---|")
    for w in workers:
        lines.append(
            f"| {w.get('id', '?')} | {w.get('scope', 'unknown')} "
            f"| {w.get('state', 'UNKNOWN')} | {w.get('age', '--')} "
            f"| {w.get('last_update', '')} |"
        )
    lines.append("")


def _render_plan_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    plan = snapshot.get("plan", {})
    lines.append("## Plan")
    lines.append("")
    lines.append(f"- **Slice**: {plan.get('slice', 'n/a')}")
    lines.append(f"- **Progress**: {plan.get('progress', 'n/a')}")
    lines.append(f"- **Open findings**: {plan.get('open_findings', 0)}")
    lines.append(f"- **Pending**: {plan.get('pending', 0)}")
    lines.append("")


def _render_publication_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    pub = snapshot.get("publication", {})
    lines.append("## Publication")
    lines.append("")
    lines.append(f"- **State**: {pub.get('state', pub.get('effective', 'n/a'))}")
    tm = pub.get("target_match", {})
    match_parts = [f"{k}: {'yes' if v else 'no'}" for k, v in tm.items()]
    lines.append(f"- **Target match**: {', '.join(match_parts)}")
    lines.append(f"- **Why**: {pub.get('why', 'n/a')}")
    lines.append(f"- **Evidence**: `{pub.get('evidence', 'n/a')}`")
    lines.append("")


def _render_quality_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    quality = snapshot.get("quality", {})
    lines.append("## Quality")
    lines.append("")
    lines.append("| Gate | Status |")
    lines.append("|---|---|")
    for key in ("docs_gate", "plan_sync", "bridge", "code_shape", "instr_sync", "clippy"):
        label = key.replace("_", " ").title()
        lines.append(f"| {label} | {quality.get(key, 'n/a')} |")
    failing = quality.get("failing", [])
    if failing:
        lines.append("")
        lines.append(f"**Failing**: {', '.join(failing)}")
    lines.append("")


def _render_coordination_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    coord = snapshot.get("coordination", {})
    lines.append("## Coordination")
    lines.append("")
    lines.append(f"- **Packets**: {coord.get('pending_packets', 0)} pending")
    lines.append(f"- **Instruction rev**: `{coord.get('instruction_rev', 'n/a')}`")
    lines.append(f"- **Reviewer**: {coord.get('reviewer_age', '--')}")
    lines.append(f"- **Implementer**: {coord.get('implementer_state', 'n/a')}")
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


def _mode_display(mode: str) -> str:
    """Human-readable mode label."""
    mapping = {
        "active_dual_agent": "Dual-agent",
        "single_agent": "Single-agent",
        "tools_only": "Tools-only",
        "paused": "Paused",
        "offline": "Offline",
    }
    return mapping.get(mode, mode)


def _state_color(state: str) -> str:
    """Pick ANSI color for a job/review state string."""
    lower = state.lower()
    if lower in ("implementing", "active", "running"):
        return _CYAN
    if lower in ("review_needed", "stale", "waiting"):
        return _YELLOW
    if lower in ("idle", "pass", "done"):
        return _GREEN
    if lower in ("blocked", "failed", "error", "fail"):
        return _RED
    return _DIM


def _gate_color(val: str) -> str:
    """Pick ANSI color for a quality gate value."""
    upper = val.upper()
    if upper == "PASS":
        return _GREEN
    if upper == "FAIL":
        return _RED
    return _DIM
