"""Markdown renderers for the DashboardSnapshot.

Each function renders one dashboard section into plain markdown suitable
for documentation, mobile output, or non-terminal consumption.
"""

from __future__ import annotations

from typing import Any

from . import attention as _attn
from .helpers import (
    _append_markdown_agent_counts,
    _fmt_pct,
    _fmt_timer,
    _loop_label,
    _mode_display,
)


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


def _render_header_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    """Header: repo identity, git state, and loop mode as a markdown table."""
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
    """NOW section: owner, next action, blocker, last change."""
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


def _render_reviewer_activity_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    """REVIEWER: bridge-parsed reviewer activity summary."""
    activity = snapshot.get("reviewer_activity", {})
    if not activity:
        return
    provider = activity.get("provider", "unknown")
    provider_label = f" ({provider})" if provider and provider != "unknown" else ""
    lines.append(f"## Reviewer{provider_label}")
    lines.append("")
    lines.append(f"- **Last poll**: {activity.get('last_poll_age', '--')}")
    lines.append(f"- **Verdict**: {activity.get('last_verdict', 'n/a')}")
    lines.append(f"- **Reviewed**: {activity.get('reviewed_files', 0)} files")
    lines.append(f"- **Instruction**: {activity.get('instruction_summary', 'n/a')}")
    lines.append(f"- **Findings**: {activity.get('findings_posted', 0)} posted")
    lines.append("")


def _render_health_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    """HEALTH: daemon liveness and conductor status."""
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
    agent_counts = health.get("agent_counts", {})
    if agent_counts:
        _append_markdown_agent_counts(lines, agent_counts)
    lines.append("")


def _render_workers_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    """WORKERS: table of all registered agents."""
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
    """PLAN: current slice, progress, findings, and pending items."""
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
    """PUBLICATION: state, target match, timers, and evidence."""
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
    """QUALITY: gate status table with optional failing files and probes."""
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
    check_details = quality.get("check_details", [])
    if check_details:
        lines.append("")
        lines.append("| Check | Status | Violation |")
        lines.append("|---|---|---|")
        for detail in check_details:
            name = detail.get("check", "unknown")
            status = detail.get("status", "FAIL")
            violation = detail.get("violation", "")
            lines.append(f"| {name} | {status} | {violation} |")
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
    """AUDIT: governance cleanup metrics."""
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
    """ANALYTICS: event stats, sparklines, and bar charts."""
    from ..dashboard_charts import bar_chart, progress_bar, sparkline

    analytics = snapshot.get("analytics", {})
    if not analytics or analytics.get("total_events") == "n/a":
        return
    lines.append("## Analytics")
    lines.append("")
    lines.append(f"- **Events**: {analytics.get('total_events', 'n/a')}")
    lines.append(f"- **Success rate**: {_fmt_pct(analytics.get('command_success_rate_pct', 'n/a'))}")
    lines.append(f"- **Avg TTG**: {_fmt_timer(analytics.get('avg_time_to_green_s', 'n/a'))}")
    push_vals = analytics.get("push_success_values", [])
    if push_vals:
        lines.append(f"- **Push success**: `{sparkline(push_vals)}` (last {len(push_vals)})")
    cleanup = analytics.get("cleanup_rate_pct", "n/a")
    if isinstance(cleanup, (int, float)):
        lines.append(f"- **Cleanup**: `{progress_bar(cleanup / 100)}`")
    top_cmds = analytics.get("top_commands", [])
    if top_cmds:
        lines.append("")
        lines.append("**Top commands**:")
        lines.append("```")
        lines.append(bar_chart(top_cmds))
        lines.append("```")
    lines.append("")


def _render_coordination_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    """COORDINATION: packets, instruction rev, session age."""
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
    _attn.render_doctor_markdown(coord, lines)
    _attn.render_pending_packets_markdown(snapshot, lines)
    lines.append("")


def _render_timeline_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    """TIMELINE: last N devctl events as a markdown table."""
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
