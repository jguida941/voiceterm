"""Renderers for the DashboardSnapshot: terminal (ANSI), markdown, JSON."""

from __future__ import annotations

import json
import os
import re
from typing import Any

# Pre-compiled pattern for stripping ANSI escape sequences
_ANSI_RE = re.compile(r"\033\[[^m]*m")

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


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences (e.g. ``\\033[1m``) from *text*.

    Useful when piping terminal output to environments that render raw
    escape codes as visible text (mobile apps, log files, CI artifacts).
    """
    return _ANSI_RE.sub("", text)


def _should_strip_color(no_color: bool) -> bool:
    """Return True when ANSI codes should be stripped.

    Respects the ``--no-color`` CLI flag and the ``NO_COLOR`` environment
    variable (see https://no-color.org/).
    """
    if no_color:
        return True
    return os.environ.get("NO_COLOR", "") != ""


def render_terminal(snapshot: dict[str, Any], *, no_color: bool = False) -> str:
    """ANSI-colored dense multi-column terminal dashboard output.

    When *no_color* is ``True`` (or the ``NO_COLOR`` env var is set),
    all ANSI escape sequences are stripped from the result so the output
    is safe for environments that do not interpret them.
    """
    lines: list[str] = []
    _render_summary_terminal(snapshot, lines)
    _render_header_terminal(snapshot, lines)
    _render_now_terminal(snapshot, lines)
    _render_codex_activity_terminal(snapshot, lines)
    _render_health_terminal(snapshot, lines)
    _render_workers_terminal(snapshot, lines)
    _render_plan_terminal(snapshot, lines)
    _render_findings_terminal(snapshot, lines)
    _render_publication_terminal(snapshot, lines)
    _render_quality_terminal(snapshot, lines)
    _render_audit_terminal(snapshot, lines)
    _render_analytics_terminal(snapshot, lines)
    _render_coordination_terminal(snapshot, lines)
    _render_flow_terminal(snapshot, lines)
    _render_timeline_terminal(snapshot, lines)
    result = "\n".join(lines)
    if _should_strip_color(no_color):
        result = strip_ansi(result)
    return result


def render_markdown(snapshot: dict[str, Any]) -> str:
    """Markdown-formatted dashboard output."""
    lines: list[str] = []
    _render_summary_markdown(snapshot, lines)
    _render_header_markdown(snapshot, lines)
    _render_now_markdown(snapshot, lines)
    _render_codex_activity_markdown(snapshot, lines)
    _render_health_markdown(snapshot, lines)
    _render_workers_markdown(snapshot, lines)
    _render_plan_markdown(snapshot, lines)
    _render_findings_markdown(snapshot, lines)
    _render_publication_markdown(snapshot, lines)
    _render_quality_markdown(snapshot, lines)
    _render_audit_markdown(snapshot, lines)
    _render_analytics_markdown(snapshot, lines)
    _render_coordination_markdown(snapshot, lines)
    _render_flow_markdown(snapshot, lines)
    _render_timeline_markdown(snapshot, lines)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Terminal renderers — dense multi-column layout
# ---------------------------------------------------------------------------

def _render_summary_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """Summary band: compiled operator conclusions shown before everything else."""
    summary = snapshot.get("summary", {})
    if not summary:
        return

    one_line = summary.get("one_line", "")
    if one_line:
        lines.append(f"{_DIM}{one_line}{_RESET}")
        lines.append("")

    state = summary.get("overall_state", "healthy").upper()
    state_color = _summary_state_color(state)
    lines.append(f"{_BOLD}STATUS: {state_color}{state}{_RESET}")

    block_class = summary.get("block_class", "none")
    why_color = _YELLOW if block_class != "none" else _DIM
    lines.append(f"  Why:   {why_color}{block_class}{_RESET}")

    next_actor = summary.get("next_actor", "operator")
    hint = summary.get("next_command_hint", "")
    lines.append(f"  Owner: {_CYAN}{next_actor}{_RESET}   next: {hint}")

    pub = snapshot.get("publication", {})
    pub_effective = pub.get("effective", "n/a")
    lines.append(f"  Push:  {pub_effective}")

    infra = summary.get("infra_state", "unknown")
    infra_color = _GREEN if infra == "healthy" else (_YELLOW if infra == "degraded" else _RED)
    infra_label = summary.get("infra_label", "")
    lines.append(f"  Infra: {infra_color}{infra.title()}{_RESET} ({infra_label})")

    primary = summary.get("primary_blocker", "none")
    secondary = summary.get("secondary_blocker", "none")
    if primary != "none":
        lines.append(f"  Block: {_RED}{primary}{_RESET}")
    if secondary != "none":
        lines.append(f"         {_DIM}{secondary}{_RESET}")
    lines.append("")


def _summary_state_color(state: str) -> str:
    """Pick ANSI color for the summary overall_state label."""
    upper = state.upper()
    if upper == "BLOCKED":
        return _RED
    if upper == "WAITING":
        return _YELLOW
    if upper == "ACTIVE":
        return _CYAN
    return _GREEN


def _render_summary_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    """Summary card: compiled operator conclusions for mobile/markdown output."""
    summary = snapshot.get("summary", {})
    if not summary:
        return

    one_line = summary.get("one_line", "")
    if one_line:
        lines.append(f"> {one_line}")
        lines.append("")

    state = summary.get("overall_state", "healthy").upper()
    block_class = summary.get("block_class", "none")
    next_actor = summary.get("next_actor", "operator")
    hint = summary.get("next_command_hint", "")
    pub = snapshot.get("publication", {})
    pub_effective = pub.get("effective", "n/a")
    infra = summary.get("infra_state", "unknown")
    infra_label = summary.get("infra_label", "")

    lines.append(f"**Status**: {state}")
    lines.append(f"**Why**: {block_class}")
    lines.append(f"**Owner**: {next_actor}, next: {hint}")
    lines.append(f"**Push**: {pub_effective}")
    lines.append(f"**Infra**: {infra.title()} ({infra_label})")

    primary = summary.get("primary_blocker", "none")
    secondary = summary.get("secondary_blocker", "none")
    if primary != "none":
        lines.append(f"**Blocker**: {primary}")
    if secondary != "none":
        lines.append(f"**Secondary**: {secondary}")
    lines.append("")


def _render_header_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """Header: title, repo identity, git state, loop mode — dense layout."""
    repo = snapshot.get("repo", {})
    review = snapshot.get("review", {})
    mode = review.get("mode", "n/a")
    worktree = repo.get("worktree", "unknown")
    worktree_color = _GREEN if worktree == "CLEAN" else _YELLOW
    mode_color = _CYAN if mode == "active_dual_agent" else _DIM

    title = f"{_BOLD}GOVERNANCE DASHBOARD{_RESET}"
    refresh = f"{_DIM}refresh: --{_RESET}"
    lines.append(f"{title}{' ' * max(1, _WIDTH - 20 - 12)}{refresh}")

    # Row 1: repo name, branch, HEAD sha
    lines.append(
        f"Repo: {repo.get('name', 'unknown')}   "
        f"Branch: {repo.get('branch', 'unknown')}   "
        f"HEAD: {repo.get('head', 'unknown')}"
    )

    # Row 2: ahead/behind, dirty file count, worktree state
    ahead = repo.get("ahead", 0)
    behind = repo.get("behind", 0)
    dirty_files = repo.get("dirty_files", 0)
    ahead_label = f"{ahead}"
    if behind:
        ahead_label += f" / Behind: {behind}"
    dirty_label = f"{dirty_files} file{'s' if dirty_files != 1 else ''}"
    lines.append(
        f"Ahead: {ahead_label:<14}"
        f"Dirty: {dirty_label:<35}"
        f"Worktree: {worktree_color}{worktree}{_RESET}"
    )

    # Row 3: loop and mode
    session_label = repo.get("session", "--")
    mode_label = _mode_display(mode)
    lines.append(
        f"Loop: {mode_color}{_loop_label(mode)}{_RESET}      "
        f"Mode: {mode_label}      "
        f"Session: {_CYAN}{session_label}{_RESET}"
    )
    lines.append("")

    # Recent commits sub-section
    recent = repo.get("recent_commits", [])
    if recent:
        lines.append(f"{_BOLD}RECENT COMMITS{_RESET}")
        for commit in recent:
            sha = commit.get("sha", "???????")
            msg = commit.get("message", "")
            lines.append(f"  {_DIM}{sha}{_RESET}  {msg}")
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
    instr_text = now.get("instruction_text", "n/a")
    if instr_text and instr_text != "n/a":
        lines.append(f"  Instruction    {_DIM}{instr_text}{_RESET}")
    lines.append("")


def _render_codex_activity_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """REVIEWER (Codex): what Codex has been doing, parsed from bridge.md."""
    activity = snapshot.get("codex_activity", {})
    if not activity:
        return
    lines.append(f"{_BOLD}REVIEWER (Codex){_RESET}")
    lines.append(f"  Last poll      {activity.get('last_poll_age', '--')}")
    verdict = activity.get("last_verdict", "n/a")
    verdict_color = _CYAN if verdict != "n/a" else _DIM
    lines.append(f"  Verdict        {verdict_color}{verdict}{_RESET}")
    lines.append(f"  Reviewed       {activity.get('reviewed_files', 0)} files")
    instr = activity.get("instruction_summary", "n/a")
    instr_color = _CYAN if instr != "n/a" else _DIM
    lines.append(f"  Instruction    {instr_color}{instr}{_RESET}")
    findings = activity.get("findings_posted", 0)
    f_color = _YELLOW if findings > 0 else _GREEN
    lines.append(f"  Findings       {f_color}{findings} posted{_RESET}")
    lines.append("")


def _render_health_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """HEALTH: daemon liveness and attention state for operator visibility."""
    health = snapshot.get("health", {})
    if not health:
        return
    lines.append(f"{_BOLD}HEALTH{_RESET}")

    for label, key in (("Publisher", "publisher"), ("Supervisor", "supervisor")):
        daemon = health.get(key, {})
        running = daemon.get("running", False)
        state_label = "RUNNING" if running else "STOPPED"
        state_color = _GREEN if running else _RED
        pid = daemon.get("pid", 0)
        hb_age = daemon.get("last_heartbeat_age", "--")
        snaps = daemon.get("snapshots", 0)
        lines.append(
            f"  {label:<15}{state_color}{state_label:<10}{_RESET}"
            f"PID {pid:<8}"
            f"Last heartbeat {_DIM}{hb_age}{_RESET}    "
            f"{snaps} snapshots"
        )

    # Conductor process liveness (Codex / Claude)
    for label, key in (("Codex", "codex_conductor"), ("Claude", "claude_conductor")):
        conductor = health.get(key, {})
        pid = conductor.get("pid")
        alive = conductor.get("alive", False)
        if pid is not None:
            state_label = "RUNNING" if alive else "DEAD"
            state_color = _GREEN if alive else _RED
            detail = "" if alive else f"   {_DIM}(process not found){_RESET}"
            lines.append(
                f"  {label:<15}{state_color}{state_label:<10}{_RESET}"
                f"PID {pid:<8}{detail}"
            )
        else:
            lines.append(
                f"  {label:<15}{_DIM}{'NO SESSION':<10}{_RESET}"
                f"{_DIM}(no conductor session file){_RESET}"
            )

    attn_status = health.get("attention_status", "n/a")
    attn_summary = health.get("attention_summary", "n/a")
    attn_color = _GREEN if attn_status == "healthy" else _YELLOW
    summary_text = attn_summary if attn_summary != "n/a" else ""
    sep = " \u2014 " if summary_text else ""
    lines.append(
        f"  {'Attention':<15}{attn_color}{attn_status}{_RESET}"
        f"{sep}{_DIM}{summary_text}{_RESET}"
    )
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


def _render_findings_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """FINDINGS: structured bridge findings when available."""
    findings = snapshot.get("findings", [])
    if not findings:
        return
    lines.append(f"{_BOLD}FINDINGS{_RESET}")
    for f in findings:
        fid = f.get("id", "?")
        summary = f.get("summary", "")
        lines.append(f"  {_YELLOW}{fid}{_RESET}  {summary}")
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

    # Inline step timers from push report
    timers = pub.get("timers", {})
    timer_parts = []
    for label, key in (("Preflight", "preflight_s"), ("Push", "push_s"), ("Fetch", "fetch_s")):
        val = timers.get(key, "n/a")
        timer_parts.append(f"{label} {_fmt_timer(val)}")
    lines.append(f"  Timers         {'  '.join(timer_parts)}")

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

    # Probe quality summary
    probes = quality.get("probes", {})
    if probes and probes.get("probes_enabled") != "n/a":
        p_enabled = probes.get("probes_enabled", "n/a")
        hints = probes.get("risk_hints", "n/a")
        high = probes.get("high", 0)
        medium = probes.get("medium", 0)
        scanned = probes.get("files_scanned", "n/a")
        hint_color = _RED if high else (_YELLOW if medium else _GREEN)
        lines.append(
            f"  Probes {p_enabled}  "
            f"Hints {hint_color}{hints}{_RESET} "
            f"({high} high, {medium} medium)  "
            f"Files {scanned}"
        )
    lines.append("")


def _render_audit_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """AUDIT: governance cleanup metrics from review summary."""
    audit = snapshot.get("audit", {})
    if not audit or audit.get("total_findings") == "n/a":
        return
    total = audit.get("total_findings", "n/a")
    fixed = audit.get("fixed_count", "n/a")
    rate = audit.get("cleanup_rate_pct", "n/a")
    open_count = audit.get("open_finding_count", "n/a")
    rate_color = _GREEN if isinstance(rate, (int, float)) and rate >= 75 else _YELLOW
    lines.append(f"{_BOLD}AUDIT{_RESET}")
    lines.append(
        f"  Findings {total}  Fixed {fixed}  "
        f"Cleanup {rate_color}{_fmt_pct(rate)}{_RESET}  "
        f"Open {open_count}"
    )
    lines.append("")


def _render_analytics_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """ANALYTICS: time-to-green and event stats from data science summary."""
    analytics = snapshot.get("analytics", {})
    if not analytics or analytics.get("total_events") == "n/a":
        return
    events = analytics.get("total_events", "n/a")
    rate = analytics.get("command_success_rate_pct", "n/a")
    ttg = analytics.get("avg_time_to_green_s", "n/a")
    lines.append(f"{_BOLD}ANALYTICS{_RESET}")
    lines.append(
        f"  Events {events}  "
        f"Success {_fmt_pct(rate)}  "
        f"Avg TTG {_fmt_timer(ttg)}"
    )
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
    session_age = coord.get("session_age", "--")
    session_started = coord.get("session_started", "")
    started_suffix = f" (started {session_started} UTC)" if session_started else ""
    lines.append(f"  Session    {session_age}{started_suffix}")
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


def _render_timeline_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """TIMELINE: last N devctl events with command, result, and duration."""
    timeline = snapshot.get("timeline", [])
    if not timeline:
        return
    lines.append(f"{_BOLD}TIMELINE (last {len(timeline)}){_RESET}")
    for evt in timeline:
        result = evt.get("result", "FAIL")
        result_color = _GREEN if result == "PASS" else _RED
        lines.append(
            f"  {_DIM}{evt.get('time', '--:--:--')}{_RESET}  "
            f"{evt.get('command', 'unknown'):<22}"
            f"{result_color}{result:<8}{_RESET}"
            f"{evt.get('duration', 'n/a')}"
        )
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
    return len(_ANSI_RE.sub("", s))


# ---------------------------------------------------------------------------
# Markdown renderers
# ---------------------------------------------------------------------------

def _render_header_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    repo = snapshot.get("repo", {})
    review = snapshot.get("review", {})
    mode = review.get("mode", "n/a")
    ahead = repo.get("ahead", 0)
    behind = repo.get("behind", 0)
    dirty_files = repo.get("dirty_files", 0)
    ahead_label = str(ahead)
    if behind:
        ahead_label += f" / Behind: {behind}"

    lines.append("# Governance Dashboard")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| Repo | {repo.get('name', 'unknown')} |")
    lines.append(f"| Branch | {repo.get('branch', 'unknown')} |")
    lines.append(f"| HEAD | {repo.get('head', 'unknown')} |")
    lines.append(f"| Ahead | {ahead_label} |")
    lines.append(f"| Dirty | {dirty_files} file{'s' if dirty_files != 1 else ''} |")
    lines.append(f"| Loop | {_loop_label(mode)} |")
    lines.append(f"| Mode | {_mode_display(mode)} |")
    lines.append(f"| Session | {repo.get('session', '--')} |")
    lines.append(f"| Worktree | {repo.get('worktree', 'unknown')} |")
    lines.append("")

    recent = repo.get("recent_commits", [])
    if recent:
        lines.append("### Recent Commits")
        lines.append("")
        for commit in recent:
            sha = commit.get("sha", "???????")
            msg = commit.get("message", "")
            lines.append(f"- `{sha}` {msg}")
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
    instr_text = now.get("instruction_text", "n/a")
    if instr_text and instr_text != "n/a":
        lines.append(f"- **Instruction**: {instr_text}")
    lines.append("")


def _render_codex_activity_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    activity = snapshot.get("codex_activity", {})
    if not activity:
        return
    lines.append("## Reviewer (Codex)")
    lines.append("")
    lines.append(f"- **Last poll**: {activity.get('last_poll_age', '--')}")
    lines.append(f"- **Verdict**: {activity.get('last_verdict', 'n/a')}")
    lines.append(f"- **Reviewed**: {activity.get('reviewed_files', 0)} files")
    lines.append(f"- **Instruction**: {activity.get('instruction_summary', 'n/a')}")
    lines.append(f"- **Findings**: {activity.get('findings_posted', 0)} posted")
    lines.append("")


def _render_health_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    health = snapshot.get("health", {})
    if not health:
        return
    lines.append("## Health")
    lines.append("")
    for label, key in (("Publisher", "publisher"), ("Supervisor", "supervisor")):
        daemon = health.get(key, {})
        state = "RUNNING" if daemon.get("running") else "STOPPED"
        lines.append(
            f"- **{label}**: {state} | PID {daemon.get('pid', 0)} "
            f"| Last heartbeat {daemon.get('last_heartbeat', 'n/a')} "
            f"| {daemon.get('snapshots', 0)} snapshots"
        )
    for label, key in (("Codex", "codex_conductor"), ("Claude", "claude_conductor")):
        conductor = health.get(key, {})
        pid = conductor.get("pid")
        alive = conductor.get("alive", False)
        if pid is not None:
            state = "RUNNING" if alive else "DEAD"
            detail = "" if alive else " (process not found)"
            lines.append(f"- **{label}**: {state} | PID {pid}{detail}")
        else:
            lines.append(f"- **{label}**: NO SESSION (no conductor session file)")
    attn = health.get("attention_status", "n/a")
    summary = health.get("attention_summary", "n/a")
    lines.append(f"- **Attention**: {attn} — {summary}")
    lines.append(f"- **Active daemons**: {health.get('active_daemons', 0)}")
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


def _render_findings_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    """FINDINGS: structured bridge findings when available."""
    findings = snapshot.get("findings", [])
    if not findings:
        return
    lines.append("## Findings")
    lines.append("")
    for f in findings:
        fid = f.get("id", "?")
        summary = f.get("summary", "")
        lines.append(f"- **{fid}**: {summary}")
    lines.append("")


def _render_publication_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    pub = snapshot.get("publication", {})
    lines.append("## Publication")
    lines.append("")
    lines.append(f"- **State**: {pub.get('state', pub.get('effective', 'n/a'))}")
    tm = pub.get("target_match", {})
    match_parts = [f"{k}: {'yes' if v else 'no'}" for k, v in tm.items()]
    lines.append(f"- **Target match**: {', '.join(match_parts)}")
    timers = pub.get("timers", {})
    if timers:
        lines.append(
            f"- **Timers**: Preflight {_fmt_timer(timers.get('preflight_s'))}  "
            f"Push {_fmt_timer(timers.get('push_s'))}  "
            f"Fetch {_fmt_timer(timers.get('fetch_s'))}"
        )
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
    probes = quality.get("probes", {})
    if probes and probes.get("probes_enabled") != "n/a":
        lines.append("")
        lines.append(
            f"**Probes**: {probes.get('probes_enabled', 'n/a')} enabled, "
            f"{probes.get('risk_hints', 'n/a')} hints "
            f"({probes.get('high', 0)} high, {probes.get('medium', 0)} medium), "
            f"{probes.get('files_scanned', 'n/a')} files scanned"
        )
    lines.append("")


def _render_audit_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    audit = snapshot.get("audit", {})
    if not audit or audit.get("total_findings") == "n/a":
        return
    lines.append("## Audit")
    lines.append("")
    lines.append(f"- **Findings**: {audit.get('total_findings', 'n/a')}")
    lines.append(f"- **Fixed**: {audit.get('fixed_count', 'n/a')}")
    lines.append(f"- **Cleanup rate**: {_fmt_pct(audit.get('cleanup_rate_pct', 'n/a'))}")
    lines.append(f"- **Open**: {audit.get('open_finding_count', 'n/a')}")
    lines.append("")


def _render_analytics_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    analytics = snapshot.get("analytics", {})
    if not analytics or analytics.get("total_events") == "n/a":
        return
    lines.append("## Analytics")
    lines.append("")
    lines.append(f"- **Events**: {analytics.get('total_events', 'n/a')}")
    lines.append(f"- **Success rate**: {_fmt_pct(analytics.get('command_success_rate_pct', 'n/a'))}")
    lines.append(f"- **Avg TTG**: {_fmt_timer(analytics.get('avg_time_to_green_s', 'n/a'))}")
    lines.append("")


def _render_coordination_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    coord = snapshot.get("coordination", {})
    lines.append("## Coordination")
    lines.append("")
    lines.append(f"- **Packets**: {coord.get('pending_packets', 0)} pending")
    lines.append(f"- **Instruction rev**: `{coord.get('instruction_rev', 'n/a')}`")
    lines.append(f"- **Reviewer**: {coord.get('reviewer_age', '--')}")
    lines.append(f"- **Implementer**: {coord.get('implementer_state', 'n/a')}")
    session_age = coord.get("session_age", "--")
    session_started = coord.get("session_started", "")
    started_suffix = f" (started {session_started} UTC)" if session_started else ""
    lines.append(f"- **Session age**: {session_age}{started_suffix}")
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


def _render_timeline_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    timeline = snapshot.get("timeline", [])
    if not timeline:
        return
    lines.append(f"## Timeline (last {len(timeline)})")
    lines.append("")
    lines.append("| Time | Command | Result | Duration |")
    lines.append("|---|---|---|---|")
    for evt in timeline:
        lines.append(
            f"| {evt.get('time', '--:--:--')} "
            f"| {evt.get('command', 'unknown')} "
            f"| {evt.get('result', 'FAIL')} "
            f"| {evt.get('duration', 'n/a')} |"
        )
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


def _fmt_timer(val: Any) -> str:
    """Format a duration value as '71.1s' or 'pending' for display."""
    if val is None or val == "n/a":
        return "pending"
    if isinstance(val, (int, float)):
        return f"{val:.1f}s"
    return str(val)


def _fmt_pct(val: Any) -> str:
    """Format a percentage value as '56.2%' or 'n/a' for display."""
    if val is None or val == "n/a":
        return "n/a"
    if isinstance(val, (int, float)):
        return f"{val}%"
    return str(val)
