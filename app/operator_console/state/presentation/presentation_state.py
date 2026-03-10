"""Pure snapshot-derived presentation state for the Operator Console."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from ..snapshots.analytics_snapshot import RepoAnalyticsSnapshot
from ..core.models import AgentLaneData, OperatorConsoleSnapshot
from ..snapshots.phone_status_snapshot import PhoneControlSnapshot
from ..core.readability import audience_mode_label, resolve_audience_mode
from ..repo.repo_state import RepoStateSnapshot

_RISK_HIGH_KEYWORDS = frozenset(
    {"critical", "security", "destructive", "dangerous", "force", "delete"}
)
_RISK_MEDIUM_KEYWORDS = frozenset(
    {"review", "approval", "staging", "merge", "deploy", "push"}
)


@dataclass(frozen=True)
class SystemBannerState:
    """Operator-facing health summary rendered under the toolbar."""

    health_label: str
    health_level: str
    detail_text: str
    agent_summary: str
    review_mode_text: str
    approvals_text: str
    risk_text: str
    confidence_text: str


@dataclass(frozen=True)
class AnalyticsViewState:
    """Pre-rendered analytics sections plus KPI values for the dashboard."""

    text: str
    repo_text: str
    quality_text: str
    phone_text: str
    kpi_values: dict[str, str]


def build_status_bar_text(
    snapshot: OperatorConsoleSnapshot,
    *,
    audience_mode: str,
    repo_state: RepoStateSnapshot | None = None,
) -> str:
    """Render the footer text for the selected audience mode."""
    resolved_audience = resolve_audience_mode(audience_mode)
    banner = build_system_banner_state(snapshot)
    if resolved_audience == "technical":
        bits = []
        if repo_state and repo_state.branch:
            dirty_marker = "*" if repo_state.is_dirty else ""
            sha = repo_state.head_short or "?"
            bits.append(f"{repo_state.branch}{dirty_marker}@{sha}")
            if repo_state.is_dirty:
                bits.append(f"dirty:{repo_state.dirty_file_count} risk:{repo_state.risk_summary}")
        if snapshot.review_state_path:
            bits.append(f"review_state: {snapshot.review_state_path}")
        else:
            bits.append("markdown bridge only; live terminal telemetry unavailable")
        if snapshot.last_codex_poll:
            bits.append(f"Last Codex poll: {snapshot.last_codex_poll}")
        if snapshot.last_worktree_hash:
            bits.append(f"Worktree hash: {snapshot.last_worktree_hash}")
        if snapshot.warnings:
            bits.append("warnings: " + " | ".join(snapshot.warnings))
        return " | ".join(bits)

    bits = [
        banner.health_label,
        banner.detail_text,
        f"Read mode: {audience_mode_label(resolved_audience)}",
    ]
    if repo_state and repo_state.branch:
        dirty_marker = " (dirty)" if repo_state.is_dirty else ""
        bits.append(f"Branch: {repo_state.branch}{dirty_marker}")
    if snapshot.review_state_path:
        bits.append("Structured state available")
    else:
        bits.append("Markdown bridge only")
    if snapshot.last_worktree_hash:
        bits.append(f"Tree: {snapshot.last_worktree_hash[:8]}")
    return " | ".join(bits)


def build_system_banner_state(snapshot: OperatorConsoleSnapshot) -> SystemBannerState:
    """Derive the top-level system status banner from the current snapshot."""
    lanes = _present_lanes(snapshot)
    health_label, health_level = _system_health(snapshot, lanes)
    approvals = len(snapshot.pending_approvals)

    detail_bits: list[str] = []
    if approvals > 0:
        suffix = "s" if approvals != 1 else ""
        detail_bits.append(f"{approvals} approval{suffix} waiting")
    elif snapshot.warnings:
        detail_bits.append(snapshot.warnings[0])
    else:
        detail_bits.append("review loop healthy")

    if snapshot.last_codex_poll:
        detail_bits.append(f"last poll {snapshot.last_codex_poll}")

    codex_lane = snapshot.codex_lane
    risk_text = (
        f"Risk: {codex_lane.risk_label or 'Unknown'}"
        if codex_lane
        else "Risk: Unknown"
    )
    confidence_text = (
        f"Confidence: {codex_lane.confidence_label or 'Unknown'}"
        if codex_lane
        else "Confidence: Unknown"
    )
    mode_text = snapshot.review_mode or "markdown-only"
    agent_summary = " | ".join(_lane_chip_text(lane) for lane in lanes) or "No lanes detected"

    return SystemBannerState(
        health_label=health_label,
        health_level=health_level,
        detail_text=" | ".join(detail_bits),
        agent_summary=agent_summary,
        review_mode_text=f"Mode: {mode_text}",
        approvals_text=f"Approvals: {approvals}",
        risk_text=risk_text,
        confidence_text=confidence_text,
    )


def build_activity_text(snapshot: OperatorConsoleSnapshot) -> str:
    """Render the Activity page text from the current snapshot."""
    lines: list[str] = []

    for label, lane in _lane_sections(snapshot):
        lines.append("─" * 40)
        lines.append(f"  {label}")
        if lane is None:
            lines.append("  Status: no data")
        else:
            lines.append(f"  Status: {lane.status_hint}")
            for key, value in lane.rows:
                lines.append(f"    {key}: {value}")
        lines.append("")

    if snapshot.warnings:
        lines.append("─" * 40)
        lines.append("  Warnings")
        for warning in snapshot.warnings:
            lines.append(f"    ⚠ {warning}")
        lines.append("")

    lines.append("─" * 40)
    lines.append("  Bridge File")
    if snapshot.review_state_path:
        lines.append(f"    Path: {snapshot.review_state_path}")
    if snapshot.last_worktree_hash:
        lines.append(f"    Worktree: {snapshot.last_worktree_hash}")
    if snapshot.last_codex_poll:
        lines.append(f"    Last poll: {snapshot.last_codex_poll}")

    return "\n".join(lines)


def build_analytics_view_state(
    snapshot: OperatorConsoleSnapshot,
    *,
    repo_analytics: RepoAnalyticsSnapshot | None = None,
    phone_snapshot: PhoneControlSnapshot | None = None,
) -> AnalyticsViewState:
    """Render analytics sections and KPI values from repo-visible state."""
    overview_lines = [
        "REPO-VISIBLE REVIEW SIGNALS",
        "─" * 50,
        (
            "Repo-owned signals from the bridge state, working tree, mutation "
            "summary, recent CI runs, and phone-status artifacts."
        ),
        "",
    ]

    banner = build_system_banner_state(snapshot)
    for label, lane in (
        ("Codex", snapshot.codex_lane),
        ("Claude", snapshot.claude_lane),
        ("Cursor", snapshot.cursor_lane),
        ("Operator", snapshot.operator_lane),
    ):
        if lane is None:
            overview_lines.append(f"  {label:12s}  status=offline")
        else:
            overview_lines.append(
                f"  {label:12s}  status={lane.status_hint:8s}  rows={len(lane.rows)}"
            )
    overview_lines.append("")
    overview_lines.append("─" * 50)
    overview_lines.append(f"  SYSTEM HEALTH: {banner.health_label}")
    overview_lines.append(f"    {banner.detail_text}")
    if snapshot.review_state_path:
        overview_lines.append(f"    Review state: {snapshot.review_state_path}")
    if snapshot.last_worktree_hash:
        overview_lines.append(f"    Worktree:     {snapshot.last_worktree_hash}")
    if snapshot.last_codex_poll:
        overview_lines.append(f"    Last poll:    {snapshot.last_codex_poll}")
    if repo_analytics is not None and repo_analytics.branch:
        overview_lines.append(f"    Branch:       {repo_analytics.branch}")
    if phone_snapshot is not None:
        overview_lines.append(f"    Phone relay:  {_title_case(phone_snapshot.phase)}")
    overview_lines.append("")

    if snapshot.warnings:
        overview_lines.append("─" * 50)
        overview_lines.append(f"  WARNINGS ({len(snapshot.warnings)})")
        for warning in snapshot.warnings:
            overview_lines.append(f"    ⚠ {warning}")
        overview_lines.append("")

    overview_lines.append("─" * 50)
    overview_lines.append(f"  PENDING APPROVALS: {len(snapshot.pending_approvals)}")
    for approval in snapshot.pending_approvals:
        overview_lines.append(f"    [{approval.policy_hint}] {approval.summary}")
    overview_lines.append("")

    return AnalyticsViewState(
        text="\n".join(overview_lines),
        repo_text=_build_repo_text(repo_analytics),
        quality_text=_build_quality_text(snapshot, repo_analytics),
        phone_text=_build_phone_text(phone_snapshot),
        kpi_values={
            "dirty_files": _format_kpi_number(
                repo_analytics.changed_files if repo_analytics is not None else None
            ),
            "mutation_score": _format_percent_value(
                repo_analytics.mutation_score_pct if repo_analytics is not None else None
            ),
            "ci_runs": _format_ci_kpi(repo_analytics),
            "warnings": str(len(snapshot.warnings)),
            "pending_approvals": str(len(snapshot.pending_approvals)),
            "phone_phase": _title_case(phone_snapshot.phase)
            if phone_snapshot is not None
            else "\u2014",
        },
    )


def snapshot_digest(snapshot: OperatorConsoleSnapshot) -> str:
    """Return a digest that changes when visible snapshot state changes."""
    payload = "\n".join(
        [
            snapshot.codex_panel_text,
            snapshot.claude_panel_text,
            snapshot.operator_panel_text,
            snapshot.raw_bridge_text,
            snapshot.last_codex_poll or "",
            snapshot.last_worktree_hash or "",
            snapshot.review_state_path or "",
            "|".join(snapshot.warnings),
            "|".join(approval.packet_id for approval in snapshot.pending_approvals),
            "|".join(_serialize_lane(lane) for lane in _present_lanes(snapshot)),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def classify_approval_risk(policy_hint: str) -> str:
    """Derive approval severity from a policy-hint string."""
    lower = policy_hint.lower()
    if any(keyword in lower for keyword in _RISK_HIGH_KEYWORDS):
        return "high"
    if any(keyword in lower for keyword in _RISK_MEDIUM_KEYWORDS):
        return "medium"
    if any(keyword in lower for keyword in ("info", "advisory", "notice")):
        return "low"
    return "unknown"


def _build_repo_text(repo_analytics: RepoAnalyticsSnapshot | None) -> str:
    lines = ["WORKING TREE & HOTSPOTS", ""]
    if repo_analytics is None:
        lines.append("- Repo analytics are unavailable in this view.")
        return "\n".join(lines)
    if repo_analytics.collection_note:
        lines.append(f"- Repo analytics note: {repo_analytics.collection_note}")
        return "\n".join(lines)

    lines.append(f"- Branch: {repo_analytics.branch or 'unknown'}")
    lines.append(
        "- Dirty files: "
        f"{repo_analytics.changed_files} total "
        f"(A{repo_analytics.added_files} "
        f"M{repo_analytics.modified_files} "
        f"D{repo_analytics.deleted_files} "
        f"R{repo_analytics.renamed_files} "
        f"?{repo_analytics.untracked_files} "
        f"U{repo_analytics.conflicted_files})"
    )
    lines.append(
        "- Change mix: "
        + _change_mix_bar(
            repo_analytics.added_files,
            repo_analytics.modified_files,
            repo_analytics.deleted_files,
            repo_analytics.untracked_files,
            repo_analytics.conflicted_files,
        )
    )
    lines.append(
        "- Governance touchpoints: "
        + (
            "MASTER_PLAN touched"
            if repo_analytics.master_plan_updated
            else "MASTER_PLAN unchanged"
        )
        + " | "
        + (
            "CHANGELOG touched"
            if repo_analytics.changelog_updated
            else "CHANGELOG unchanged"
        )
    )
    lines.append("- Hotspots:")
    if repo_analytics.top_paths:
        for path in repo_analytics.top_paths:
            lines.append(f"  - {path}")
    else:
        lines.append("  - none")
    return "\n".join(lines)


def _build_quality_text(
    snapshot: OperatorConsoleSnapshot,
    repo_analytics: RepoAnalyticsSnapshot | None,
) -> str:
    lines = ["QUALITY & CI", ""]
    lines.append(
        f"- Warnings: {len(snapshot.warnings)} | Pending approvals: {len(snapshot.pending_approvals)}"
    )
    quality = snapshot.quality_backlog
    if quality is not None:
        lines.append(
            (
                "- Guard backlog: "
                f"{quality.guard_failures} failures | "
                f"critical={quality.critical_paths} high={quality.high_paths} "
                f"medium={quality.medium_paths} low={quality.low_paths}"
            )
        )
        if quality.top_priorities:
            lines.append("- Top hotspots:")
            for row in quality.top_priorities[:3]:
                lines.append(f"  - [{row.severity}] {row.path}")
        if quality.warning:
            lines.append(f"- Collector warning: {quality.warning}")
    if repo_analytics is None:
        lines.append("- Repo quality collectors are unavailable in this view.")
        return "\n".join(lines)

    if repo_analytics.mutation_score_pct is None:
        lines.append(
            f"- Mutation: {repo_analytics.mutation_note or 'mutation score unavailable'}"
        )
    else:
        lines.append(
            "- Mutation score: "
            f"{repo_analytics.mutation_score_pct:.1f}% "
            f"{_ratio_bar(repo_analytics.mutation_score_pct, 100.0)}"
        )
        if repo_analytics.mutation_age_hours is not None:
            lines.append(
                f"- Mutation age: {repo_analytics.mutation_age_hours:.1f}h since latest outcomes"
            )
    if repo_analytics.ci_runs_total is None:
        lines.append(f"- Recent CI: {repo_analytics.ci_note or 'CI data unavailable'}")
    else:
        success = repo_analytics.ci_success_runs
        failed = repo_analytics.ci_failed_runs
        pending = repo_analytics.ci_pending_runs
        total = max(repo_analytics.ci_runs_total, success + failed + pending, 1)
        lines.append(
            "- Recent CI: "
            f"{success} green / {failed} failing / {pending} pending "
            f"{_ratio_bar(success, total)}"
        )
        if repo_analytics.ci_note:
            lines.append(f"- CI note: {repo_analytics.ci_note}")
    return "\n".join(lines)


def _build_phone_text(phone_snapshot: PhoneControlSnapshot | None) -> str:
    lines = ["MOBILE RELAY", ""]
    lines.append(
        "- This panel prefers the repo-owned merged `mobile-status` view and falls back to raw `phone-status` when review bridge state is unavailable."
    )
    if phone_snapshot is None:
        lines.append("- Mobile relay is unavailable in this view.")
        return "\n".join(lines)

    lines.append(
        f"- Phase: {_title_case(phone_snapshot.phase)} | Risk: {phone_snapshot.risk} | Unresolved: {phone_snapshot.unresolved_count}"
    )
    lines.append(
        f"- Mode: {phone_snapshot.mode_effective} | Reason: {phone_snapshot.reason}"
    )
    if phone_snapshot.review_bridge_state:
        lines.append(
            f"- Review bridge: {_title_case(phone_snapshot.review_bridge_state)}"
        )
    if phone_snapshot.latest_working_branch:
        lines.append(f"- Working branch: {phone_snapshot.latest_working_branch}")
    if phone_snapshot.last_worktree_hash:
        lines.append(f"- Worktree hash: {phone_snapshot.last_worktree_hash}")
    if phone_snapshot.age_minutes is not None:
        lines.append(f"- Snapshot age: {phone_snapshot.age_minutes:.1f} minutes")
    if phone_snapshot.source_run_url:
        lines.append(f"- Source run: {phone_snapshot.source_run_url}")
    if phone_snapshot.current_instruction:
        lines.append(f"- Current instruction: {phone_snapshot.current_instruction}")
    if phone_snapshot.next_actions:
        lines.append("- Next actions:")
        for action in phone_snapshot.next_actions[:4]:
            lines.append(f"  - {action}")
    else:
        lines.append("- Next actions: none recorded")
    if phone_snapshot.note:
        lines.append(f"- Note: {phone_snapshot.note}")
    return "\n".join(lines)


def _format_ci_kpi(repo_analytics: RepoAnalyticsSnapshot | None) -> str:
    if repo_analytics is None or repo_analytics.ci_runs_total is None:
        return "\u2014"
    success = repo_analytics.ci_success_runs
    total = max(repo_analytics.ci_runs_total, 1)
    return f"{success}/{total}"


def _format_kpi_number(value: int | None) -> str:
    if value is None:
        return "\u2014"
    return str(value)


def _format_percent_value(value: float | None) -> str:
    if value is None:
        return "\u2014"
    return f"{value:.0f}%"


def _ratio_bar(value: float, total: float, width: int = 10) -> str:
    if total <= 0:
        return "[..........]"
    ratio = max(0.0, min(1.0, float(value) / float(total)))
    filled = int(round(ratio * width))
    return "[" + ("#" * filled) + ("." * max(0, width - filled)) + "]"


def _change_mix_bar(
    added: int,
    modified: int,
    deleted: int,
    untracked: int,
    conflicted: int,
) -> str:
    total = max(1, added + modified + deleted + untracked + conflicted)
    return (
        f"A{_ratio_bar(added, total, width=4)} "
        f"M{_ratio_bar(modified, total, width=4)} "
        f"D{_ratio_bar(deleted, total, width=4)} "
        f"?{_ratio_bar(untracked, total, width=4)} "
        f"U{_ratio_bar(conflicted, total, width=4)}"
    )


def _title_case(value: str | None) -> str:
    if value is None or not value.strip():
        return "\u2014"
    return value.replace("_", " ").title()


def _present_lanes(snapshot: OperatorConsoleSnapshot) -> list[AgentLaneData]:
    return [
        lane
        for lane in (
            snapshot.codex_lane,
            snapshot.operator_lane,
            snapshot.claude_lane,
            snapshot.cursor_lane,
        )
        if lane is not None
    ]


def _lane_sections(
    snapshot: OperatorConsoleSnapshot,
) -> tuple[tuple[str, AgentLaneData | None], ...]:
    return (
        ("Codex - Reviewer", snapshot.codex_lane),
        ("Claude - Implementer", snapshot.claude_lane),
        ("Cursor - Editor", snapshot.cursor_lane),
        ("Operator - Bridge State", snapshot.operator_lane),
    )


def _system_health(
    snapshot: OperatorConsoleSnapshot,
    lanes: list[AgentLaneData],
) -> tuple[str, str]:
    if snapshot.warnings or any(lane.status_hint == "stale" for lane in lanes):
        return ("BLOCKED", "stale")
    if len(snapshot.pending_approvals) > 0 or any(
        lane.status_hint == "warning" for lane in lanes
    ):
        return ("DEGRADED", "warning")
    if any(lane.status_hint == "active" for lane in lanes):
        return ("RUNNING", "active")
    return ("IDLE", "idle")


def _lane_chip_text(lane: AgentLaneData) -> str:
    return f"{lane.provider_name} {lane.state_label}"


def _serialize_lane(lane: AgentLaneData) -> str:
    return "|".join(
        [
            lane.provider_name,
            lane.lane_title,
            lane.role_label,
            lane.status_hint,
            lane.state_label,
            lane.risk_label or "",
            lane.confidence_label or "",
            ";".join(f"{key}={value}" for key, value in lane.rows),
            lane.raw_text,
        ]
    )
