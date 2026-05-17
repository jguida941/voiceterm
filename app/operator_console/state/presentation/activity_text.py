"""Activity-panel presentation helpers for the Operator Console."""

from __future__ import annotations

from ..core.models import AgentLaneData, OperatorConsoleSnapshot


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


def _lane_sections(
    snapshot: OperatorConsoleSnapshot,
) -> tuple[tuple[str, AgentLaneData | None], ...]:
    return (
        ("Codex - Reviewer", snapshot.codex_lane),
        ("Claude - Implementer", snapshot.claude_lane),
        ("Cursor - Editor", snapshot.cursor_lane),
        ("Operator - Bridge State", snapshot.operator_lane),
    )
