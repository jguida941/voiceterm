"""Human-readable Activity-tab report builders for the Operator Console."""

from __future__ import annotations

from dataclasses import dataclass

from .models import AgentLaneData, OperatorConsoleSnapshot
from .readability import audience_mode_label, resolve_audience_mode


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
    ReportOption("operator", "Operator", "Operator lane, scope, and approvals."),
    ReportOption("approvals", "Approvals", "Pending approval queue and decisions needed."),
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
    if option.report_id == "operator":
        return _build_lane_report(snapshot, snapshot.operator_lane, option, resolved_audience)
    if option.report_id == "approvals":
        return _build_approvals_report(snapshot, resolved_audience)
    return _build_overview_report(snapshot, resolved_audience)


def _build_overview_report(snapshot: OperatorConsoleSnapshot, audience_mode: str) -> ActivityReport:
    if audience_mode == "technical":
        lines = [
            _headline(snapshot),
            "",
            "What is happening now:",
            f"- {_lane_sentence(snapshot.codex_lane, fallback='Codex reviewer state is not visible yet.')}",
            f"- {_lane_sentence(snapshot.claude_lane, fallback='Claude implementer state is not visible yet.')}",
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
    if snapshot.warnings:
        return "Open the relevant monitor output, confirm the warning source, and clear the first blocker."
    claude_lane = snapshot.claude_lane
    if claude_lane is not None and claude_lane.status_hint == "warning":
        return "Focus on the Claude lane next and resolve the implementer-side blocker."
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
    return (snapshot.codex_lane, snapshot.claude_lane, snapshot.operator_lane)


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
