"""Render helpers for bootstrap quality-signal summaries."""

from __future__ import annotations

from typing import Any


def append_quality_signal_lines(
    lines: list[str],
    quality_signals: object,
) -> None:
    """Append one bounded quality-signal section when startup data is present."""
    if not isinstance(quality_signals, dict) or not quality_signals:
        return
    lines.append("## Quality Signals")
    lines.append("")
    _append_probe_report_summary(lines, quality_signals.get("probe_report"))
    _append_governance_review_summary(
        lines,
        quality_signals.get("governance_review"),
    )
    _append_guidance_hotspots(lines, quality_signals.get("guidance_hotspots"))
    _append_watchdog_summary(lines, quality_signals.get("watchdog"))
    _append_command_reliability_summary(
        lines,
        quality_signals.get("command_reliability"),
    )
    lines.append("")


def _append_probe_report_summary(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    lines.append(
        "- **probe-report** ({generated_at}): {risk_hints} hints across {files_with_hints} files".format(
            generated_at=payload.get("generated_at", "unknown"),
            risk_hints=payload.get("risk_hints", 0),
            files_with_hints=payload.get("files_with_hints", 0),
        )
    )
    top_files = payload.get("top_files")
    if isinstance(top_files, list) and top_files:
        rendered = ", ".join(
            "`{file}` ({hint_count})".format(
                file=row.get("file", "unknown"),
                hint_count=row.get("hint_count", 0),
            )
            for row in top_files
            if isinstance(row, dict)
        )
        if rendered:
            lines.append(f"- top hinted files: {rendered}")


def _append_governance_review_summary(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    lines.append(
        "- **governance-review** ({generated_at}): {total_findings} findings, {open_findings} open, {fixed_count} fixed, cleanup {cleanup_rate}%".format(
            generated_at=payload.get("generated_at_utc", "unknown"),
            total_findings=payload.get("total_findings", 0),
            open_findings=payload.get("open_finding_count", 0),
            fixed_count=payload.get("fixed_count", 0),
            cleanup_rate=payload.get("cleanup_rate_pct", 0),
        )
    )


def _append_guidance_hotspots(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, list) or not payload:
        return
    hotspot = payload[0]
    if not isinstance(hotspot, dict):
        return
    lines.append(
        "- **guidance hotspot**: `{file}` ({hint_count} hints)".format(
            file=hotspot.get("file", "unknown"),
            hint_count=hotspot.get("hint_count", 0),
        )
    )
    bounded_next_slice = str(hotspot.get("bounded_next_slice") or "").strip()
    if bounded_next_slice:
        lines.append(f"- next slice: {bounded_next_slice}")
    guidance = hotspot.get("guidance")
    if isinstance(guidance, list):
        for row in guidance[:2]:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- guidance: `{probe}` on `{symbol}` [{severity}] -> {instruction}".format(
                    probe=row.get("probe", "unknown"),
                    symbol=row.get("symbol", "(file-level)"),
                    severity=row.get("severity", "unknown"),
                    instruction=row.get("ai_instruction", ""),
                )
            )
            practice_title = str(row.get("practice_title") or "").strip()
            practice_explanation = str(row.get("practice_explanation") or "").strip()
            if practice_title and practice_explanation:
                lines.append(
                    f"- practice: {practice_title} -> {practice_explanation}"
                )


def _append_watchdog_summary(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    lines.append(
        "- **watchdog** ({generated_at}): {episodes} episodes, success {success_rate}%, false positives {false_positive_rate}%, top family `{top_family}`".format(
            generated_at=payload.get("generated_at", "unknown"),
            episodes=payload.get("total_episodes", 0),
            success_rate=payload.get("success_rate_pct", 0),
            false_positive_rate=payload.get("false_positive_rate_pct", 0),
            top_family=payload.get("top_guard_family", "unknown"),
        )
    )


def _append_command_reliability_summary(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    lines.append(
        "- **command reliability** ({generated_at}): {events} events, success {success_rate}%, p95 runtime {p95}s".format(
            generated_at=payload.get("generated_at", "unknown"),
            events=payload.get("total_events", 0),
            success_rate=payload.get("success_rate_pct", 0),
            p95=payload.get("p95_duration_seconds", 0),
        )
    )
    commands = payload.get("commands")
    if not isinstance(commands, list):
        return
    rendered = ", ".join(
        "`{command}` {success_rate}%/{duration}s".format(
            command=row.get("command", "unknown"),
            success_rate=row.get("success_rate_pct", 0),
            duration=row.get("avg_duration_seconds", 0),
        )
        for row in commands
        if isinstance(row, dict)
    )
    if rendered:
        lines.append(f"- command slice: {rendered}")
