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
    _append_contract_connectivity_summary(
        lines,
        quality_signals.get("contract_connectivity"),
    )
    _append_code_shape_clusters(lines, quality_signals.get("code_shape_clusters"))
    _append_split_advisor(lines, quality_signals.get("split_advisor"))
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


def _append_contract_connectivity_summary(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    current_counts = payload.get("current_counts")
    new_counts = payload.get("new_counts")
    if not isinstance(current_counts, dict):
        current_counts = {}
    if not isinstance(new_counts, dict):
        new_counts = {}
    lines.append(
        "- **contract-connectivity** [{severity}]: {current_total} current debt findings, {new_total} new".format(
            severity=payload.get("severity", "unknown"),
            current_total=payload.get("current_debt_count", 0),
            new_total=payload.get("new_debt_count", 0),
        )
    )
    cache_state = str(payload.get("cache_state") or "").strip()
    if cache_state and cache_state not in {"fresh", "live_scan"}:
        lines.append(f"- contract cache: {cache_state}")
    lines.append(
        "- contract debt mix: orphaned={orphaned}, duplicates={duplicates}, stranded={stranded}, bidirectional={bidirectional}".format(
            orphaned=current_counts.get("orphaned", 0),
            duplicates=current_counts.get("duplicates", 0),
            stranded=current_counts.get("stranded", 0),
            bidirectional=current_counts.get("bidirectional", 0),
        )
    )
    if any(new_counts.values()):
        lines.append(
            "- new contract debt: orphaned={orphaned}, duplicates={duplicates}, stranded={stranded}, bidirectional={bidirectional}".format(
                orphaned=new_counts.get("orphaned", 0),
                duplicates=new_counts.get("duplicates", 0),
                stranded=new_counts.get("stranded", 0),
                bidirectional=new_counts.get("bidirectional", 0),
            )
        )
    instruction = str(payload.get("ai_instruction") or "").strip()
    if instruction:
        lines.append(f"- contract action: {instruction}")


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
    severity_counts = payload.get("open_by_severity")
    if isinstance(severity_counts, dict) and severity_counts:
        rendered = ", ".join(
            f"{severity}={severity_counts.get(severity, 0)}"
            for severity in ("critical", "high", "medium", "low")
        )
        lines.append(f"- open severity mix: {rendered}")


def _append_code_shape_clusters(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, list) or not payload:
        return
    rendered = ", ".join(
        "`{file}` ({cluster_count}, {severity})".format(
            file=row.get("file", "unknown"),
            cluster_count=row.get("cluster_count", "?"),
            severity=row.get("severity", "unknown"),
        )
        for row in payload[:3]
        if isinstance(row, dict)
    )
    if rendered:
        lines.append(f"- **code-shape clusters**: {rendered}")


def _append_split_advisor(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, list) or not payload:
        return
    for row in payload[:2]:
        if not isinstance(row, dict):
            continue
        lines.append(
            "- **split advisor**: `{file}` [{severity}] -> {instruction}".format(
                file=row.get("file", "unknown"),
                severity=row.get("severity", "unknown"),
                instruction=row.get("ai_instruction", ""),
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
