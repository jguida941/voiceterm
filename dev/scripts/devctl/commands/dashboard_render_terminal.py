"""Terminal (ANSI) renderers for the DashboardSnapshot.

Each function renders one dashboard section into an ANSI-colored dense
multi-column layout suitable for terminal display.
"""

from __future__ import annotations

from typing import Any

from . import dashboard_render_attention as _attn
from .dashboard_render_helpers import (
    _BOLD,
    _CYAN,
    _DIM,
    _GREEN,
    _RED,
    _RESET,
    _WIDTH,
    _YELLOW,
    _JOB_STATE_COLORS,
    _fmt_pct,
    _fmt_timer,
    _gate_color,
    _loop_label,
    _mode_display,
)


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
    state_color = {"BLOCKED": _RED, "WAITING": _YELLOW, "ACTIVE": _CYAN}.get(state, _GREEN)
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


def _render_header_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """Header: title, repo identity, git state, loop mode -- dense layout."""
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


def _render_reviewer_activity_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """REVIEWER: what the reviewer has been doing, parsed from bridge.md."""
    activity = snapshot.get("reviewer_activity", {})
    if not activity:
        return
    provider = activity.get("provider", "unknown")
    provider_label = f" ({provider})" if provider and provider != "unknown" else ""
    lines.append(f"{_BOLD}REVIEWER{provider_label}{_RESET}")
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
        color = _JOB_STATE_COLORS.get(state.lower(), _DIM)
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

    # Per-check failure details from preflight output
    check_details = quality.get("check_details", [])
    for detail in check_details:
        check_name = detail.get("check", "unknown")
        violation = detail.get("violation", "")
        summary = f"  {_RED}FAIL{_RESET}  {check_name}"
        if violation:
            summary += f"  {_DIM}-- {violation}{_RESET}"
        lines.append(summary)

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
    """ANALYTICS: time-to-green, event stats, sparklines, and bar charts."""
    from .dashboard_charts import bar_chart, progress_bar, sparkline

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
    push_vals = analytics.get("push_success_values", [])
    if push_vals:
        spark = sparkline(push_vals)
        lines.append(f"  Push success: {spark} (last {len(push_vals)})")
    cleanup = analytics.get("cleanup_rate_pct", "n/a")
    if isinstance(cleanup, (int, float)):
        lines.append(f"  Cleanup:      {progress_bar(cleanup / 100)}")
    top_cmds = analytics.get("top_commands", [])
    if top_cmds:
        lines.append("")
        lines.append("  Top commands:")
        lines.append(bar_chart(top_cmds))
    lines.append("")


def _render_coordination_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """COORDINATION: compact 2-field-per-line layout with doctor and packets."""
    coord = snapshot.get("coordination", {})

    pending = coord.get("pending_packets", 0)
    instr_rev = coord.get("instruction_rev", "n/a")
    rev_age = coord.get("reviewer_age", "--")
    impl_state = coord.get("implementer_state", "n/a")
    impl_color = _GREEN if impl_state == "current" else _YELLOW
    lines.append(f"{_BOLD}COORDINATION{_RESET}")
    lines.append(
        f"  Packets    {_YELLOW if pending > 0 else _DIM}{pending} pending{_RESET}    "
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
    _attn.render_doctor_terminal(coord, lines)
    _attn.render_pending_packets_terminal(snapshot, lines)
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
