"""Watchdog-specific Activity report assembly."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.models import OperatorConsoleSnapshot
from ..watchdog_presenter import (
    watchdog_available,
    watchdog_guard_family_lines,
    watchdog_note,
    watchdog_provider_lines,
    watchdog_provenance_lines,
    watchdog_summary_line,
    watchdog_topline_lines,
)


@dataclass(frozen=True)
class WatchdogReportContent:
    """Structured content for the Activity-tab watchdog report."""

    summary: str
    body: str
    provenance_note: str


def build_watchdog_report_content(
    snapshot: OperatorConsoleSnapshot,
    *,
    audience_mode: str,
    next_step: str,
) -> WatchdogReportContent:
    """Build the watchdog Activity report body from the shared summary artifact."""
    watchdog = snapshot.watchdog_snapshot
    if not watchdog_available(watchdog):
        note = watchdog_note(watchdog)
        body = (
            f"Watchdog analytics are not available: {note}\n\n"
            "Recommended next step:\n"
            f"- {next_step}"
        )
        return WatchdogReportContent(
            summary="Watchdog analytics are not available yet.",
            body=body,
            provenance_note=(
                "Script-derived watchdog summary from repo-owned data-science artifacts (no data)."
            ),
        )

    lines = [
        (
            "Watchdog metrics derived from the shared guarded-coding summary artifact."
            if audience_mode == "technical"
            else "This report shows the latest guarded-coding watchdog metrics."
        ),
        "",
    ]
    lines.extend(watchdog_topline_lines(watchdog))
    provider_lines = watchdog_provider_lines(watchdog, limit=4)
    if provider_lines:
        lines.extend(["", "Provider split:"])
        lines.extend(provider_lines)
    guard_family_lines = watchdog_guard_family_lines(watchdog, limit=4)
    if guard_family_lines:
        lines.extend(["", "Top guard families:"])
        lines.extend(guard_family_lines)
    lines.extend(["", "Artifact provenance:"])
    lines.extend(watchdog_provenance_lines(watchdog))
    lines.extend(["", "Recommended next step:", f"- {next_step}"])
    return WatchdogReportContent(
        summary=watchdog_summary_line(watchdog),
        body="\n".join(lines),
        provenance_note="Script-derived watchdog summary from the shared data-science artifact loader.",
    )
