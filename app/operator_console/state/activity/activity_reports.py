"""Human-readable Activity-tab report builders for the Operator Console."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.models import AgentLaneData, OperatorConsoleSnapshot
from ..core.readability import audience_mode_label, resolve_audience_mode


@dataclass(frozen=True)
class ReportOption:
    """Selectable report topic exposed in the Activity tab."""

    report_id: str
    label: str
    description: str


@dataclass(frozen=True)
class ActivityReport:
    """Readable report rendered from the current snapshot."""

    report_id: str
    title: str
    summary: str
    body: str
    provenance: tuple[str, ...]


REPORT_OPTIONS: tuple[ReportOption, ...] = (
    ReportOption("overview", "Overview", "Top-level system summary and next step."),
    ReportOption("blockers", "Blockers", "Warnings, approvals, and stale lanes."),
    ReportOption("codex", "Codex", "Reviewer lane state in plain language."),
    ReportOption("claude", "Claude", "Implementer lane state in plain language."),
    ReportOption("cursor", "Cursor", "Editor lane state in plain language."),
    ReportOption("operator", "Operator", "Operator lane, scope, and approvals."),
    ReportOption("approvals", "Approvals", "Pending approval queue and decisions needed."),
    ReportOption("quality", "Quality Backlog", "Prioritized code quality hotspots and guard findings."),
    ReportOption("guardrails", "Guardrails", "Ralph loop status, fix rate, and guard health."),
)


def available_report_options() -> tuple[ReportOption, ...]:
    """Return the report topics shown in the Activity tab."""
    return REPORT_OPTIONS


def resolve_report_option(report_id: str) -> ReportOption:
    """Return a report option, falling back to the overview topic."""
    normalized = report_id.strip().lower()
    for option in REPORT_OPTIONS:
        if option.report_id == normalized:
            return option
    return REPORT_OPTIONS[0]


def build_activity_report(
    snapshot: OperatorConsoleSnapshot,
    *,
    report_id: str,
    audience_mode: str = "simple",
) -> ActivityReport:
    """Build a human-readable report for the selected topic."""
    resolved_audience = resolve_audience_mode(audience_mode)
    option = resolve_report_option(report_id)
    if option.report_id == "blockers":
        return _build_blockers_report(snapshot, resolved_audience)
    if option.report_id == "codex":
        return _build_lane_report(snapshot, snapshot.codex_lane, option, resolved_audience)
    if option.report_id == "claude":
        return _build_lane_report(snapshot, snapshot.claude_lane, option, resolved_audience)
    if option.report_id == "cursor":
        return _build_lane_report(snapshot, snapshot.cursor_lane, option, resolved_audience)
    if option.report_id == "operator":
        return _build_lane_report(snapshot, snapshot.operator_lane, option, resolved_audience)
    if option.report_id == "approvals":
        return _build_approvals_report(snapshot, resolved_audience)
    if option.report_id == "quality":
        return _build_quality_report(snapshot, resolved_audience)
    if option.report_id == "guardrails":
        return _build_guardrails_report(snapshot, resolved_audience)
    return _build_overview_report(snapshot, resolved_audience)


def _build_overview_report(snapshot: OperatorConsoleSnapshot, audience_mode: str) -> ActivityReport:
    if audience_mode == "technical":
        lines = [
            _headline(snapshot),
            "",
            "What is happening now:",
            f"- {_lane_sentence(snapshot.codex_lane, fallback='Codex reviewer state is not visible yet.')}",
            f"- {_lane_sentence(snapshot.claude_lane, fallback='Claude implementer state is not visible yet.')}",
            f"- {_lane_sentence(snapshot.cursor_lane, fallback='Cursor editor state is not visible yet.')}",
            f"- {_lane_sentence(snapshot.operator_lane, fallback='Operator lane state is not visible yet.')}",
            "",
            "What needs attention:",
        ]
        attention = _attention_lines(snapshot)
        if attention:
            lines.extend(f"- {line}" for line in attention)
        else:
            lines.append("- No immediate blockers are visible in the current snapshot.")
        lines.extend(
            [
                "",
                "Recommended next step:",
                f"- {_recommended_next_step(snapshot)}",
                "",
                "Signals used:",
                f"- Last Codex poll: {snapshot.last_codex_poll or 'unknown'}",
                f"- Worktree hash: {snapshot.last_worktree_hash or 'unknown'}",
                f"- Review state artifact: {snapshot.review_state_path or 'not found; markdown bridge only'}",
            ]
        )
    else:
        lines = [
            _headline(snapshot),
            "",
            "Plain-language snapshot:",
            f"- {_simple_lane_sentence(snapshot.codex_lane, fallback='Codex is not visible yet.')}",
            f"- {_simple_lane_sentence(snapshot.claude_lane, fallback='Claude is not visible yet.')}",
            f"- {_simple_lane_sentence(snapshot.cursor_lane, fallback='Cursor is not visible yet.')}",
            f"- {_simple_lane_sentence(snapshot.operator_lane, fallback='Operator state is not visible yet.')}",
            "",
            "Recommended next step:",
            f"- {_recommended_next_step(snapshot)}",
        ]
        attention = _attention_lines(snapshot)
        if attention:
            lines.extend(
                [
                    "",
                    "Watch-outs:",
                ]
            )
            lines.extend(f"- {line}" for line in attention[:3])
        lines.extend(
            [
                "",
                "Behind this summary:",
                f"- Read mode: {audience_mode_label(audience_mode)}",
                f"- Last Codex poll: {snapshot.last_codex_poll or 'unknown'}",
                f"- Review state artifact: {snapshot.review_state_path or 'markdown bridge only'}",
            ]
        )
    return ActivityReport(
        report_id="overview",
        title="Executive Overview",
        summary=_headline(snapshot),
        body="\n".join(lines),
        provenance=_report_provenance(snapshot, "Script-derived overview from visible snapshot data."),
    )


def _build_blockers_report(snapshot: OperatorConsoleSnapshot, audience_mode: str) -> ActivityReport:
    lines = [
        (
            "This report focuses only on blockers, warnings, and items that can stop progress."
            if audience_mode == "technical"
            else "This report only shows things that can slow or stop the loop."
        ),
        "",
    ]
    attention = _attention_lines(snapshot)
    if attention:
        lines.append("Blocking or degraded signals:")
        lines.extend(f"- {line}" for line in attention)
    else:
        lines.append("Blocking or degraded signals:")
        lines.append("- No blocking signals are visible right now.")

    lines.extend(
        [
            "",
            "Most useful next move:",
            f"- {_recommended_next_step(snapshot)}",
        ]
    )
    return ActivityReport(
        report_id="blockers",
        title="Blockers Report",
        summary=_blocker_summary(snapshot),
        body="\n".join(lines),
        provenance=_report_provenance(snapshot, "Script-derived blocker summary from warnings, approvals, and lane health."),
    )


def _build_lane_report(
    snapshot: OperatorConsoleSnapshot,
    lane: AgentLaneData | None,
    option: ReportOption,
    audience_mode: str,
) -> ActivityReport:
    if lane is None:
        body = (
            f"{option.label} lane data is not available in the current snapshot.\n\n"
            "Recommended next step:\n"
            f"- {_recommended_next_step(snapshot)}"
        )
        return ActivityReport(
            report_id=option.report_id,
            title=f"{option.label} Report",
            summary=f"{option.label} lane data is not visible yet.",
            body=body,
            provenance=_report_provenance(snapshot, f"Script-derived {option.label.lower()} summary from the current snapshot."),
        )

    lines = [
        (
            f"{lane.provider_name} is currently {lane.state_label.lower()} with lane health `{lane.status_hint}`."
            if audience_mode == "technical"
            else f"{lane.provider_name} is {lane.state_label.lower()} right now."
        ),
        "",
        "Current understanding:" if audience_mode == "technical" else "What stands out:",
    ]
    for sentence in _lane_detail_lines(lane):
        lines.append(f"- {sentence}")
    if lane.risk_label or lane.confidence_label:
        lines.append("")
        lines.append("Assessment:")
        if lane.risk_label:
            lines.append(
                f"- {'Reported risk level' if audience_mode == 'technical' else 'Risk'}: {lane.risk_label}."
            )
        if lane.confidence_label:
            lines.append(
                f"- {'Reported confidence' if audience_mode == 'technical' else 'Confidence'}: {lane.confidence_label}."
            )
    lines.extend(
        [
            "",
            "Recommended next step:",
            f"- {_recommended_next_step(snapshot)}",
        ]
    )
    return ActivityReport(
        report_id=option.report_id,
        title=f"{option.label} Report",
        summary=f"{lane.provider_name} is {lane.state_label.lower()} ({lane.status_hint}).",
        body="\n".join(lines),
        provenance=_report_provenance(snapshot, f"Script-derived {option.label.lower()} lane summary from structured rows."),
    )


def _build_approvals_report(snapshot: OperatorConsoleSnapshot, audience_mode: str) -> ActivityReport:
    count = len(snapshot.pending_approvals)
    lines = [f"There {'is' if count == 1 else 'are'} {count} pending approval{'s' if count != 1 else ''}."]
    if count:
        lines.extend(["", "Pending approval queue:" if audience_mode == "technical" else "Approvals waiting:"])
        for approval in snapshot.pending_approvals:
            lines.append(
                f"- {approval.summary} ({approval.requested_action}) from {approval.from_agent} to {approval.to_agent}."
            )
    else:
        lines.extend(["", "Pending approval queue:", "- No approvals are waiting right now."])
    lines.extend(
        [
            "",
            "Recommended next step:",
            f"- {_recommended_next_step(snapshot)}",
        ]
    )
    return ActivityReport(
        report_id="approvals",
        title="Approvals Report",
        summary=(f"{count} approval{'s' if count != 1 else ''} waiting." if count else "No approvals are waiting."),
        body="\n".join(lines),
        provenance=_report_provenance(snapshot, "Script-derived approval queue summary from review_state and operator lane state."),
    )


def _build_quality_report(snapshot: OperatorConsoleSnapshot, audience_mode: str) -> ActivityReport:
    warnings_count = len(snapshot.warnings)
    approvals_count = len(snapshot.pending_approvals)
    degraded_lanes = _quality_degraded_lanes(snapshot)
    quality = snapshot.quality_backlog

    if audience_mode == "technical":
        lines = [
            "Quality signals visible in the current snapshot refresh cycle.",
            "",
            "Live quality indicators:",
            f"- Warnings: {warnings_count}",
            f"- Pending approvals: {approvals_count}",
            f"- Degraded lanes: {len(degraded_lanes)}",
        ]
        if quality is not None:
            lines.extend(
                [
                    f"- Guard failures: {quality.guard_failures}",
                    (
                        "- Ranked hotspots: "
                        f"{quality.ranked_paths} "
                        f"(critical={quality.critical_paths}, high={quality.high_paths}, "
                        f"medium={quality.medium_paths}, low={quality.low_paths})"
                    ),
                    f"- Source files scanned: {quality.source_files_scanned}",
                ]
            )
        if degraded_lanes:
            lines.append("")
            lines.append("Lane-level quality concerns:")
            for lane_name, hint, excerpt in degraded_lanes:
                lines.append(f"- {lane_name} ({hint}): {excerpt}")
        if snapshot.warnings:
            lines.append("")
            lines.append("Active warnings:")
            for warning in snapshot.warnings:
                lines.append(f"- {warning}")
        if quality is not None and quality.failing_checks:
            lines.append("")
            lines.append("Failing guard checks:")
            for check_key in quality.failing_checks:
                lines.append(f"- {check_key}")
        if quality is not None and quality.top_priorities:
            lines.append("")
            lines.append("Top scored hotspots:")
            for row in quality.top_priorities:
                lines.append(f"- {_quality_priority_line(row)}")
        if quality is not None and quality.warning:
            lines.extend(["", f"Collector warning: {quality.warning}"])
        lines.extend(
            [
                "",
                "Guard pipeline coverage (10 checks):",
                "- code_shape, rust_lint_debt, rust_best_practices, rust_runtime_panic_policy",
                "- rust_compiler_warnings, structural_similarity, facade_wrappers",
                "- serde_compatibility, function_duplication, rust_security_footguns",
                "",
                "Full prioritized backlog:",
                "- Run `python3 dev/scripts/devctl.py report --quality-backlog` for scored hotspots.",
                "- The full report ranks every source file by weighted severity across all 10 guards.",
                "",
                "Recommended next step:",
                f"- {_recommended_next_step(snapshot)}",
            ]
        )
    else:
        lines = [
            "This report shows code quality signals visible right now.",
            "",
            f"- {warnings_count} warning{'s' if warnings_count != 1 else ''} active",
            f"- {approvals_count} approval{'s' if approvals_count != 1 else ''} pending",
            f"- {len(degraded_lanes)} lane{'s' if len(degraded_lanes) != 1 else ''} showing quality concerns",
        ]
        if quality is not None:
            lines.append(
                (
                    f"- {quality.guard_failures} guard failure"
                    f"{'s' if quality.guard_failures != 1 else ''} across "
                    f"{quality.ranked_paths} ranked hotspot"
                    f"{'s' if quality.ranked_paths != 1 else ''}"
                )
            )
            if quality.critical_paths > 0:
                lines.append(
                    f"- {quality.critical_paths} critical hotspot"
                    f"{'s' if quality.critical_paths != 1 else ''} need review now"
                )
        if degraded_lanes:
            lines.append("")
            lines.append("Quality concerns by lane:")
            for lane_name, _hint, excerpt in degraded_lanes:
                lines.append(f"- {lane_name}: {excerpt}")
        if snapshot.warnings:
            lines.append("")
            lines.append("Watch-outs:")
            for warning in snapshot.warnings[:3]:
                lines.append(f"- {warning}")
        if quality is not None and quality.top_priorities:
            lines.extend(["", "Top hotspots right now:"])
            for row in quality.top_priorities[:3]:
                lines.append(f"- [{row.severity}] {row.path}")
        lines.extend(
            [
                "",
                "For the full quality backlog with scored hotspots and fix suggestions,",
                "run the devctl report command from the terminal.",
                "",
                "Recommended next step:",
                f"- {_recommended_next_step(snapshot)}",
            ]
        )

    total_concerns = warnings_count + len(degraded_lanes)
    if quality is not None:
        total_concerns += quality.critical_paths + quality.high_paths
    if total_concerns == 0:
        summary = "No quality concerns are visible in the current snapshot."
    else:
        summary = f"{total_concerns} quality signal{'s' if total_concerns != 1 else ''} visible in the current snapshot."

    return ActivityReport(
        report_id="quality",
        title="Quality Backlog",
        summary=summary,
        body="\n".join(lines),
        provenance=_report_provenance(
            snapshot,
            "Script-derived quality summary from warnings, lane health, and guard pipeline coverage.",
        ),
    )


def _build_guardrails_report(
    snapshot: OperatorConsoleSnapshot,
    audience_mode: str,
) -> ActivityReport:
    """Build a human-readable guardrails report from the Ralph snapshot."""
    from ..snapshots.ralph_guardrail_snapshot import load_ralph_guardrail_snapshot

    repo_root = _guardrails_repo_root(snapshot)
    ralph = load_ralph_guardrail_snapshot(repo_root) if repo_root else None

    if ralph is None or not ralph.available:
        note = ralph.note if ralph else "Ralph report root could not be determined."
        body = (
            f"Ralph guardrail data is not available: {note}\n\n"
            "Recommended next step:\n"
            f"- {_recommended_next_step(snapshot)}"
        )
        return ActivityReport(
            report_id="guardrails",
            title="Guardrails Report",
            summary="Ralph guardrail data is not available yet.",
            body=body,
            provenance=_report_provenance(snapshot, "Script-derived guardrails summary (no data)."),
        )

    lines = _guardrails_body_lines(ralph, audience_mode)
    lines.extend(
        [
            "",
            "Recommended next step:",
            f"- {_recommended_next_step(snapshot)}",
        ]
    )
    summary = (
        f"Ralph loop is {ralph.phase}: "
        f"{ralph.fixed_count}/{ralph.total_findings} fixed ({ralph.fix_rate_pct:.0f}%), "
        f"{ralph.pending_count} pending."
    )
    return ActivityReport(
        report_id="guardrails",
        title="Guardrails Report",
        summary=summary,
        body="\n".join(lines),
        provenance=_report_provenance(snapshot, "Script-derived guardrails summary from Ralph loop report."),
    )


def _guardrails_body_lines(ralph: object, audience_mode: str) -> list[str]:
    """Build the body lines for the guardrails report."""
    lines = [
        f"Ralph loop phase: {ralph.phase} (attempt {ralph.attempt}/{ralph.max_attempts})",
        "",
        "Finding summary:" if audience_mode == "technical" else "Findings:",
        f"- Total: {ralph.total_findings}",
        f"- Fixed: {ralph.fixed_count}",
        f"- False positives: {ralph.false_positive_count}",
        f"- Pending: {ralph.pending_count}",
        f"- Fix rate: {ralph.fix_rate_pct:.0f}%",
    ]
    if ralph.by_architecture:
        lines.extend(["", "By architecture:"])
        for name, total, fixed in ralph.by_architecture:
            lines.append(f"- {name}: {fixed}/{total} fixed")
    if ralph.by_severity:
        lines.extend(["", "By severity:"])
        for name, total, fixed in ralph.by_severity:
            lines.append(f"- {name}: {fixed}/{total} fixed")
    if ralph.branch:
        lines.extend(["", f"Branch: {ralph.branch}"])
    if ralph.last_run_timestamp:
        lines.append(f"Last run: {ralph.last_run_timestamp}")
    if ralph.approval_mode:
        lines.append(f"Approval mode: {ralph.approval_mode}")
    if ralph.note:
        lines.extend(["", f"Note: {ralph.note}"])
    return lines


def _guardrails_repo_root(snapshot: OperatorConsoleSnapshot) -> "Path | None":
    """Derive the repo root from the snapshot review state path."""
    from pathlib import Path

    review_path = snapshot.review_state_path
    if review_path:
        candidate = Path(review_path)
        while candidate != candidate.parent:
            candidate = candidate.parent
            if (candidate / ".git").exists():
                return candidate
    # Fallback: try cwd-based detection
    cwd = Path.cwd()
    if (cwd / ".git").exists():
        return cwd
    return None


def _quality_priority_line(row: object) -> str:
    if row is None:
        return "[unknown] (missing row)"
    path = getattr(row, "path", "(unknown)")
    severity = getattr(row, "severity", "unknown")
    score = getattr(row, "score", 0)
    signals = getattr(row, "signals", ())
    signal_text = ", ".join(tuple(signals)[:3]) if isinstance(signals, tuple) else ""
    return f"[{severity}] {path} score={score} signals={signal_text or 'none'}"


def _quality_degraded_lanes(
    snapshot: OperatorConsoleSnapshot,
) -> list[tuple[str, str, str]]:
    """Return (name, hint, excerpt) for lanes with quality-relevant degradation."""
    results: list[tuple[str, str, str]] = []
    for lane in _lanes(snapshot):
        if lane is None:
            continue
        if lane.status_hint in {"stale", "warning"}:
            excerpt = _lane_signal_excerpt(lane) or "no detail available"
            results.append((lane.provider_name, lane.status_hint, excerpt))
    return results


def _headline(snapshot: OperatorConsoleSnapshot) -> str:
    approvals = len(snapshot.pending_approvals)
    warnings = len(snapshot.warnings)
    if approvals:
        return f"The review loop is waiting on {approvals} operator approval{'s' if approvals != 1 else ''}."
    if warnings:
        return f"The review loop is degraded with {warnings} warning{'s' if warnings != 1 else ''}."
    if any(lane is not None and lane.status_hint == "active" for lane in _lanes(snapshot)):
        return "The review loop is running and no immediate blockers are visible."
    return "The review loop is visible, but the current snapshot is mostly idle or incomplete."


def _blocker_summary(snapshot: OperatorConsoleSnapshot) -> str:
    attention = _attention_lines(snapshot)
    if attention:
        return attention[0]
    return "No blocking signals are visible right now."


def _attention_lines(snapshot: OperatorConsoleSnapshot) -> list[str]:
    lines: list[str] = []
    if snapshot.pending_approvals:
        count = len(snapshot.pending_approvals)
        lines.append(f"{count} approval{'s' if count != 1 else ''} still need an operator decision.")
    for warning in snapshot.warnings:
        lines.append(warning)
    for lane in _lanes(snapshot):
        if lane is None:
            continue
        if lane.status_hint == "stale":
            lines.append(f"{lane.provider_name} looks stale and may need a refresh or relaunch.")
        elif lane.status_hint == "warning":
            lines.append(f"{lane.provider_name} is degraded: {_lane_signal_excerpt(lane)}")
    return lines


def _recommended_next_step(snapshot: OperatorConsoleSnapshot) -> str:
    if snapshot.pending_approvals:
        return "Review the pending approvals first so the loop can continue safely."
    quality = snapshot.quality_backlog
    if quality is not None and quality.critical_paths > 0:
        return "Escalate the top critical quality hotspot into a finding packet and assign an owner."
    if snapshot.warnings:
        return "Open the relevant monitor output, confirm the warning source, and clear the first blocker."
    claude_lane = snapshot.claude_lane
    if claude_lane is not None and claude_lane.status_hint == "warning":
        return "Focus on the Claude lane next and resolve the implementer-side blocker."
    cursor_lane = snapshot.cursor_lane
    if cursor_lane is not None and cursor_lane.status_hint in {"warning", "stale"}:
        return "Review Cursor lane state next and clear the editor-side blocker before new edits."
    codex_lane = snapshot.codex_lane
    if codex_lane is not None and codex_lane.status_hint == "stale":
        return "Refresh or relaunch the Codex reviewer lane before trusting the current state."
    return "Continue monitoring the shared screen and use a typed action only when the next real decision appears."


def _lane_sentence(lane: AgentLaneData | None, *, fallback: str) -> str:
    if lane is None:
        return fallback
    excerpt = _lane_signal_excerpt(lane)
    if excerpt:
        return f"{lane.provider_name} is {lane.state_label.lower()} and the strongest visible signal is: {excerpt}"
    return f"{lane.provider_name} is {lane.state_label.lower()} with lane health `{lane.status_hint}`."


def _simple_lane_sentence(lane: AgentLaneData | None, *, fallback: str) -> str:
    if lane is None:
        return fallback
    excerpt = _lane_signal_excerpt(lane)
    if excerpt:
        return f"{lane.provider_name} is {lane.state_label.lower()}. Main signal: {excerpt}"
    return f"{lane.provider_name} is {lane.state_label.lower()}."


def _lane_detail_lines(lane: AgentLaneData) -> list[str]:
    lines = []
    for key, value in lane.rows:
        clean = " ".join(value.split())
        if not clean or clean in {"(missing)", "(unknown)"}:
            continue
        lines.append(f"{key}: {clean}")
    return lines or ["No structured row details are available for this lane yet."]


def _lane_signal_excerpt(lane: AgentLaneData) -> str:
    for sentence in _lane_detail_lines(lane):
        return sentence
    return ""


def _lanes(snapshot: OperatorConsoleSnapshot) -> tuple[AgentLaneData | None, ...]:
    return (
        snapshot.codex_lane,
        snapshot.claude_lane,
        snapshot.cursor_lane,
        snapshot.operator_lane,
    )


def recommended_next_step(snapshot: OperatorConsoleSnapshot) -> str:
    """Expose the current recommended next step for callers outside this module."""
    return _recommended_next_step(snapshot)


def _report_provenance(
    snapshot: OperatorConsoleSnapshot,
    summary: str,
) -> tuple[str, ...]:
    return (
        summary,
        f"Last Codex poll: {snapshot.last_codex_poll or 'unknown'}",
        f"Worktree hash: {snapshot.last_worktree_hash or 'unknown'}",
        f"Review state: {snapshot.review_state_path or 'markdown bridge only'}",
    )
