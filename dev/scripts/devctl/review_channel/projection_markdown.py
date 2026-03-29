"""Markdown helpers for review-channel projection bundles."""

from __future__ import annotations


def append_push_markdown(
    lines: list[str],
    push_enforcement: object,
    push_decision: object,
) -> None:
    """Append the push section to the latest review-channel markdown."""
    if not isinstance(push_enforcement, dict) and not isinstance(push_decision, dict):
        return
    lines.append("")
    lines.append("## Push")
    if isinstance(push_enforcement, dict):
        lines.append(
            f"- checkpoint_required: {bool(push_enforcement.get('checkpoint_required'))}"
        )
        lines.append(
            "- publication_backlog_state: "
            f"{push_enforcement.get('publication_backlog_state') or 'none'}"
        )
        summary = str(push_enforcement.get("publication_backlog_summary") or "").strip()
        if summary:
            lines.append(f"- publication_backlog_summary: {summary}")
    if isinstance(push_decision, dict):
        lines.append(f"- action: {push_decision.get('action') or 'n/a'}")
        guidance = str(push_decision.get("publication_guidance") or "").strip()
        if guidance:
            lines.append(f"- publication_guidance: {guidance}")
