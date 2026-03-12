"""Renderer implementation for human-readable probe reports."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from dev.scripts.checks.probe_report_practices import match_best_practice
    from dev.scripts.checks.probe_report_support import (
        ALLOWLIST_FILENAME,
        AllowlistEntry,
        aggregate_probe_results,
        extract_source_snippet,
        filter_findings,
        get_git_diff_for_file,
        load_allowlist,
    )
except ModuleNotFoundError:  # pragma: no cover
    from probe_report_practices import match_best_practice
    from probe_report_support import (
        ALLOWLIST_FILENAME,
        AllowlistEntry,
        aggregate_probe_results,
        extract_source_snippet,
        filter_findings,
        get_git_diff_for_file,
        load_allowlist,
    )


def _append_diff_section(
    *,
    lines: list[str],
    file_path: str,
    repo_root: Path | None,
) -> None:
    if repo_root is None:
        return
    diff = get_git_diff_for_file(file_path, repo_root)
    if not diff:
        return
    lines.extend(["<details>", "<summary>Git diff for this file</summary>", "", "```diff"])
    diff_lines = diff.splitlines()
    if len(diff_lines) > 60:
        lines.extend(diff_lines[:60])
        lines.append(f"... ({len(diff_lines) - 60} more lines)")
    else:
        lines.append(diff)
    lines.extend(["```", "</details>", ""])


def _append_practice_section(
    *,
    lines: list[str],
    hint: dict[str, Any],
) -> None:
    practice = match_best_practice(hint)
    if not practice:
        return
    lines.append(f"**Best practice: {practice['title']}**")
    lines.extend(
        [
            "",
            practice["explanation"],
            "",
            "**How to fix:**",
            "",
            practice["fix_pattern"],
            "",
        ]
    )
    if practice.get("example_before"):
        lines.extend(
            [
                "<details>",
                "<summary>Example (click to expand)</summary>",
                "",
                "Before:",
                "```",
                practice["example_before"],
                "```",
                "",
                "After:",
                "```",
                practice["example_after"],
                "```",
                "</details>",
                "",
            ]
        )
    if practice.get("references"):
        lines.append("**References:**")
        lines.extend(f"- {reference}" for reference in practice["references"])
        lines.append("")


def _append_rich_findings_for_file(
    *,
    lines: list[str],
    file_path: str,
    hints: list[dict[str, Any]],
    repo_root: Path | None,
    show_source: bool,
) -> None:
    lines.extend([f"### `{file_path}`", ""])
    _append_diff_section(lines=lines, file_path=file_path, repo_root=repo_root)
    for index, hint in enumerate(hints, 1):
        severity = hint.get("severity", "medium").upper()
        symbol = hint.get("symbol", "unknown")
        probe = hint.get("probe", "unknown")
        signals = hint.get("signals", [])
        ai_instruction = hint.get("ai_instruction", "")

        lines.extend(
            [
                f"#### Finding {index}: [{severity}] `{symbol}`",
                "",
                f"*Detected by `{probe}`*",
                "",
            ]
        )
        if show_source and repo_root and symbol != "(file-level)":
            snippet = extract_source_snippet(file_path, symbol, repo_root)
            if snippet:
                lines.extend(["**Source context:**", snippet, ""])
        lines.append("**What was detected:**")
        lines.extend(f"- {signal}" for signal in signals)
        lines.extend(["", "**Recommended action:**", f"> {ai_instruction}", ""])
        _append_practice_section(lines=lines, hint=hint)
        template = AllowlistEntry.from_hint(hint)
        lines.extend(
            [
                (f"*To suppress: add to `{ALLOWLIST_FILENAME}`: " f"`{json.dumps(template.to_dict())}`*"),
                "",
                "---",
                "",
            ]
        )


def render_rich_report(
    reports: list[dict[str, Any]],
    *,
    repo_root: Path | str | None = None,
    show_source: bool = True,
    show_diffs: bool = True,
    show_suppressed: bool = True,
) -> str:
    """Render a comprehensive human-readable markdown report."""
    root = Path(repo_root) if repo_root else None
    aggregated = aggregate_probe_results(reports)
    allowlist = load_allowlist(root)
    findings = filter_findings(aggregated.hints_by_file, allowlist)
    suppressed_count = len(findings.suppressed) + len(findings.design_decisions)
    active_count = aggregated.total_hints - suppressed_count
    lines = ["# Code Quality Review Report", "", "## Executive Summary", ""]

    if active_count == 0:
        lines.append("No design-quality issues detected. All probes passed clean.")
        lines.extend(
            [
                "",
                f"- Files scanned: {aggregated.total_files_scanned}",
                f"- Probes run: {len(aggregated.probe_results)}",
            ]
        )
        if suppressed_count:
            lines.append(f"- Allowlisted findings: {suppressed_count} (via `{ALLOWLIST_FILENAME}`)")
        return "\n".join(lines)

    active_severity: dict[str, int] = defaultdict(int)
    for hints in findings.active.values():
        for hint in hints:
            active_severity[hint.get("severity", "medium")] += 1

    lines.extend(
        [
            (
                f"Found **{active_count} design-quality findings** across "
                f"**{len(findings.active)} files** "
                f"({aggregated.total_files_scanned} files scanned by "
                f"{len(aggregated.probe_results)} probes)."
            ),
            "",
        ]
    )
    for severity in ("high", "medium", "low"):
        count = active_severity.get(severity, 0)
        if count:
            lines.append(
                f"- **{count} {severity.upper()}** — "
                + {
                    "high": "fix before merge",
                    "medium": "fix or document in handoff",
                    "low": "informational",
                }[severity]
            )
    if findings.suppressed:
        lines.append(f"- **{len(findings.suppressed)} SUPPRESSED** — marked intentional in `{ALLOWLIST_FILENAME}`")
    if findings.design_decisions:
        lines.append(f"- **{len(findings.design_decisions)} DESIGN DECISIONS** — visible for senior review")
    lines.extend(["", "## Findings by File", ""])

    def file_sort_key(item: tuple[str, list[dict[str, Any]]]) -> tuple[int, str]:
        severity_order = {"high": 0, "medium": 1, "low": 2}
        minimum = min(severity_order.get(hint.get("severity", "low"), 3) for hint in item[1])
        return minimum, item[0]

    effective_repo_root = root if show_diffs else None
    for file_path, hints in sorted(findings.active.items(), key=file_sort_key):
        _append_rich_findings_for_file(
            lines=lines,
            file_path=file_path,
            hints=hints,
            repo_root=effective_repo_root,
            show_source=show_source,
        )

    if show_suppressed and findings.design_decisions:
        lines.extend(
            [
                "## Design Decisions for Senior Review",
                "",
                (
                    "The following findings were marked as intentional design "
                    "decisions. They remain visible so senior engineers can review "
                    "the trade-offs."
                ),
                "",
            ]
        )
        for hint, entry in findings.design_decisions:
            severity = hint.get("severity", "medium").upper()
            symbol = hint.get("symbol", "unknown")
            probe = hint.get("probe", "unknown")
            lines.extend(
                [
                    f"#### [{severity}] `{hint.get('file')}::{symbol}`",
                    "",
                    f"*Detected by `{probe}`*",
                    "",
                ]
            )
            lines.extend(f"- {signal}" for signal in hint.get("signals", []))
            lines.extend(["", f"**Design rationale:** *{entry.reason}*", ""])
            if entry.research_instruction:
                lines.extend([f"**AI research task:** {entry.research_instruction}", ""])
            lines.extend(["---", ""])

    if show_suppressed and findings.suppressed:
        lines.extend(
            [
                "## Suppressed Findings",
                "",
                (f"The following {len(findings.suppressed)} findings are suppressed " f"via `{ALLOWLIST_FILENAME}`:"),
                "",
            ]
        )
        for hint, entry in findings.suppressed:
            lines.append(f"- `{hint.get('file')}::{hint.get('symbol')}` — {hint.get('signals', [''])[0]}")
            if entry.reason:
                lines.append(f"  Reason: *{entry.reason}*")
        lines.append("")

    lines.extend(["## Probe Execution Summary", "", "| Probe | Files Scanned | Hints Found |", "|---|---|---|"])
    for report in aggregated.probe_results:
        lines.append(
            f"| `{report.get('command', 'unknown')}` | "
            f"{report.get('files_scanned', 0)} | "
            f"{len(report.get('risk_hints', []))} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_terminal_report(
    reports: list[dict[str, Any]],
    *,
    repo_root: Path | str | None = None,
) -> str:
    """Render a compact terminal-friendly report."""
    root = Path(repo_root) if repo_root else None
    aggregated = aggregate_probe_results(reports)
    findings = filter_findings(aggregated.hints_by_file, load_allowlist(root))
    allowlisted = len(findings.suppressed) + len(findings.design_decisions)
    active_count = aggregated.total_hints - allowlisted
    lines = ["=" * 60, "  CODE QUALITY REVIEW REPORT", "=" * 60, ""]

    if active_count == 0:
        lines.append("  All clear — no active design-quality issues.")
        lines.append(f"  ({aggregated.total_files_scanned} files scanned)")
        if allowlisted:
            lines.append(f"  ({allowlisted} allowlisted via {ALLOWLIST_FILENAME})")
        return "\n".join(lines)

    active_severity: dict[str, int] = defaultdict(int)
    for hints in findings.active.values():
        for hint in hints:
            active_severity[hint.get("severity", "medium")] += 1

    summary_parts = [
        f"{active_severity[severity]} {severity.upper()}"
        for severity in ("high", "medium", "low")
        if active_severity.get(severity, 0)
    ]
    lines.extend(
        [
            f"  {active_count} findings: {', '.join(summary_parts)}",
            f"  {len(findings.active)} files affected",
            f"  {aggregated.total_files_scanned} files scanned",
        ]
    )
    if allowlisted:
        lines.append(f"  {allowlisted} allowlisted via {ALLOWLIST_FILENAME}")
    lines.append("")
    lines.append("-" * 60)

    for file_path, hints in sorted(findings.active.items()):
        lines.append(f"\n  {file_path}")
        for hint in hints:
            severity = hint.get("severity", "medium").upper()
            marker = {"HIGH": "!!", "MEDIUM": " !", "LOW": "  "}.get(severity, "  ")
            lines.append(f"  {marker} [{severity:6s}] {hint.get('symbol', 'unknown')}")
            lines.extend(f"               {signal}" for signal in hint.get("signals", []))

    if findings.design_decisions:
        lines.extend(["", "-" * 60, "  DESIGN DECISIONS (for senior review)", ""])
        for hint, entry in findings.design_decisions:
            severity = hint.get("severity", "medium").upper()
            symbol = hint.get("symbol", "unknown")
            lines.append(f"  DD [{severity:6s}] {hint.get('file')}::{symbol}")
            lines.append(f"               {entry.reason}")

    lines.extend(["", "-" * 60, "  Run with --format md for detailed remediation guidance.", "=" * 60])
    return "\n".join(lines)
