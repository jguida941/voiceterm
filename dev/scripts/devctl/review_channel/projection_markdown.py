"""Markdown helpers for review-channel projection bundles."""

from __future__ import annotations

from ..runtime.project_governance_push import push_enforcement_from_mapping
from ..runtime.startup_push_recovery import artifact_publication_truth


def _append_latest_push_receipt(
    lines: list[str],
    push_enforcement: dict[str, object],
) -> None:
    latest_push_path = str(push_enforcement.get("latest_push_report_path") or "").strip()
    latest_push_status = str(
        push_enforcement.get("latest_push_report_status") or ""
    ).strip()
    latest_push_reason = str(
        push_enforcement.get("latest_push_report_reason") or ""
    ).strip()
    latest_push_seen = bool(latest_push_path or latest_push_status or latest_push_reason)
    if not latest_push_seen:
        return
    published_remote, post_push_green = artifact_publication_truth(
        push_enforcement_from_mapping(push_enforcement)
    )
    lines.append(f"- latest_push_report: `{latest_push_path or 'n/a'}`")
    lines.append(
        "- latest_push_matches_current_branch: "
        f"{bool(push_enforcement.get('latest_push_report_matches_current_branch'))}"
    )
    lines.append(
        "- latest_push_matches_current_head: "
        f"{bool(push_enforcement.get('latest_push_report_matches_current_head'))}"
    )
    lines.append(
        "- latest_push_matches_current_approved_target: "
        f"{bool(push_enforcement.get('latest_push_report_matches_current_approved_target'))}"
    )
    lines.append(
        "- latest_push_report_published_remote: "
        f"{bool(push_enforcement.get('latest_push_report_published_remote'))}"
    )
    lines.append(f"- latest_push_receipt_current: {published_remote}")
    lines.append(f"- published_remote: {published_remote}")
    lines.append(f"- post_push_green: {post_push_green}")
    if latest_push_status:
        lines.append(f"- latest_push_status: `{latest_push_status}`")
    if latest_push_reason:
        lines.append(f"- latest_push_reason: `{latest_push_reason}`")


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
        _append_latest_push_receipt(lines, push_enforcement)
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
