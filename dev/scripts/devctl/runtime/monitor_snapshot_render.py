"""Renderers for the monitor snapshot surface."""

from __future__ import annotations

from .monitor_snapshot_contracts import MonitorSnapshot


def render_monitor_snapshot_markdown(snapshot: MonitorSnapshot) -> str:
    """Render a mobile-safe markdown projection for one monitor snapshot."""
    summary = snapshot.summary
    audit = snapshot.self_audit
    sources = [
        f"- `{row.source_id}` [{row.classification}] `{row.path}` present={row.present}"
        for row in snapshot.source_labels
    ] or ["- none"]
    lines = [
        "## Remote Phone Monitor",
        "",
        f"- state: {summary.get('state', 'unknown')}",
        f"- main_problem: {summary.get('main_problem', 'none')}",
        f"- can_work_continue: {summary.get('can_work_continue', False)}",
        f"- can_code_be_pushed: {summary.get('can_code_be_pushed', False)}",
        f"- who_needs_to_act: {summary.get('who_needs_to_act', 'unknown')}",
        f"- what_should_happen_next: {summary.get('what_should_happen_next', 'n/a')}",
        f"- confidence: {summary.get('confidence', 'medium')}",
        "",
        "## Sources",
        *sources,
        "",
        "## Self Audit",
        f"- should_emit_finding: {audit.should_emit_finding}",
        f"- finding_type: {audit.finding_type}",
        "- reasons: " + ", ".join(audit.reasons) if audit.reasons else "- reasons: none",
    ]
    return "\n".join(lines)


def render_monitor_snapshot_terminal(snapshot: MonitorSnapshot) -> str:
    """Render a narrow terminal summary for phone-steered monitoring."""
    summary = snapshot.summary
    lines = [
        "REMOTE PHONE MONITOR",
        f"State: {summary.get('state', 'unknown')}",
        f"Main problem: {summary.get('main_problem', 'none')}",
        f"Can work continue: {summary.get('can_work_continue', False)}",
        f"Can code be pushed: {summary.get('can_code_be_pushed', False)}",
        f"Who needs to act: {summary.get('who_needs_to_act', 'unknown')}",
        f"What should happen next: {summary.get('what_should_happen_next', 'n/a')}",
        f"Confidence: {summary.get('confidence', 'medium')}",
        f"Self-audit: {snapshot.self_audit.should_emit_finding}",
    ]
    if snapshot.self_audit.reasons:
        lines.append(f"Reasons: {', '.join(snapshot.self_audit.reasons)}")
    return "\n".join(lines)
