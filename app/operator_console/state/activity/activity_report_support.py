"""Shared helpers for Operator Console Activity-tab reports."""

from __future__ import annotations

from pathlib import Path

from ..core.models import OperatorConsoleSnapshot, QualityPrioritySignal


def build_guardrails_body_lines(ralph: object, audience_mode: str) -> list[str]:
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


def resolve_guardrails_repo_root(snapshot: OperatorConsoleSnapshot) -> Path | None:
    """Derive the repo root from the snapshot review state path."""
    review_path = snapshot.review_state_path
    if review_path:
        candidate = Path(review_path)
        while candidate != candidate.parent:
            candidate = candidate.parent
            if (candidate / ".git").exists():
                return candidate
    cwd = Path.cwd()
    if (cwd / ".git").exists():
        return cwd
    return None


def format_quality_priority_line(row: QualityPrioritySignal | None, *, max_signals: int = 3) -> str:
    if row is None:
        return "[unknown] (missing row)"
    signal_text = ", ".join(row.signals[:max_signals]) or "none"
    return f"[{row.severity}] {row.path} score={row.score} signals={signal_text}"


def collect_quality_degraded_lanes(
    snapshot: OperatorConsoleSnapshot,
) -> list[tuple[str, str, str]]:
    """Return (name, hint, excerpt) for lanes with quality-relevant degradation."""
    results: list[tuple[str, str, str]] = []
    for lane in (
        snapshot.codex_lane,
        snapshot.claude_lane,
        snapshot.cursor_lane,
        snapshot.operator_lane,
    ):
        if lane is None or lane.status_hint not in {"stale", "warning"}:
            continue
        excerpt = "no detail available"
        for key, value in lane.rows:
            clean = " ".join(value.split())
            if clean and clean not in {"(missing)", "(unknown)"}:
                excerpt = f"{key}: {clean}"
                break
        results.append((lane.provider_name, lane.status_hint, excerpt))
    return results
