"""Markdown rendering helpers shared by `devctl status` and `devctl report`."""

from __future__ import annotations

from typing import Any

from .python_guard_report import render_python_guard_markdown
from .quality_backlog_report import render_quality_backlog_markdown
from .rust_audit_report import render_rust_audit_markdown


def render_project_markdown(
    report: dict,
    *,
    title: str,
    include_ci_details: bool,
    ci_details_limit: int = 5,
) -> str:
    """Render markdown once for both commands so wording stays aligned."""
    lines = [f"# {title}", ""]
    _append_git_lines(lines, report.get("git", {}))
    _append_mutation_lines(lines, report.get("mutants", {}))
    _append_ci_lines(
        lines,
        report.get("ci"),
        include_ci_details=include_ci_details,
        ci_details_limit=ci_details_limit,
    )
    _append_dev_log_lines(lines, report.get("dev_logs"))
    _append_pedantic_lines(lines, report.get("pedantic"))
    _append_quality_backlog_lines(lines, report.get("quality_backlog"))
    _append_python_guard_backlog_lines(lines, report.get("python_guard_backlog"))

    if "rust_audits" in report:
        rust_audits = report.get("rust_audits", {})
        if isinstance(rust_audits, dict):
            lines.append("")
            lines.extend(render_rust_audit_markdown(rust_audits))

    report_warnings = report.get("warnings")
    if isinstance(report_warnings, list) and report_warnings:
        lines.append("")
        lines.append("## Report Warnings")
        for warning in report_warnings:
            lines.append(f"- {warning}")

    bundle = report.get("bundle")
    if isinstance(bundle, dict) and bundle.get("written"):
        lines.append("")
        lines.append("## Bundle")
        lines.append(f"- markdown: {bundle.get('markdown_path')}")
        lines.append(f"- json: {bundle.get('json_path')}")

    return "\n".join(lines)


def _append_git_lines(lines: list[str], git_info: Any) -> None:
    if not isinstance(git_info, dict):
        lines.append("- Git: unavailable")
        return
    if "error" in git_info:
        lines.append(f"- Git: {git_info['error']}")
        return
    lines.append(f"- Branch: {git_info.get('branch', 'unknown')}")
    lines.append(f"- Changelog updated: {git_info.get('changelog_updated')}")
    lines.append(f"- Master plan updated: {git_info.get('master_plan_updated')}")
    lines.append(f"- Changed files: {len(git_info.get('changes', []))}")


def _append_mutation_lines(lines: list[str], mutants_info: Any) -> None:
    if not isinstance(mutants_info, dict):
        lines.append("- Mutation score: unavailable")
        return
    if "error" in mutants_info:
        lines.append("- Mutation score: unavailable")
        lines.append(f"- Mutation score note: {mutants_info['error']}")
        return
    results = mutants_info.get("results", {})
    if not isinstance(results, dict):
        results = {}
    score = results.get("score")
    updated_at = results.get("outcomes_updated_at", "unknown")
    age_hours = results.get("outcomes_age_hours")
    score_label = "unknown" if score is None else f"{float(score):.2f}%"
    age_label = "unknown" if age_hours is None else f"{float(age_hours):.2f}h"
    lines.append(f"- Mutation score: {score_label}")
    lines.append(f"- Mutation outcomes: {results.get('outcomes_path', 'unknown')}")
    lines.append(f"- Mutation outcomes updated: {updated_at} ({age_label} old)")
    warning = mutants_info.get("warning")
    if warning:
        lines.append(f"- Mutation score note: {warning}")


def _append_ci_lines(
    lines: list[str],
    ci_info: Any,
    *,
    include_ci_details: bool,
    ci_details_limit: int,
) -> None:
    if ci_info is None:
        return
    if not isinstance(ci_info, dict):
        lines.append("- CI: unavailable")
        return
    if "error" in ci_info:
        lines.append(f"- CI: error ({ci_info['error']})")
        return
    runs = ci_info.get("runs", [])
    lines.append(f"- CI runs: {len(runs)}")
    if not include_ci_details:
        return
    for run in runs[:ci_details_limit]:
        run_title = run.get("displayTitle", "unknown")
        status = run.get("status", "unknown")
        conclusion = run.get("conclusion") or "pending"
        lines.append(f"  - {run_title}: {status}/{conclusion}")


def _append_dev_log_lines(lines: list[str], dev_info: Any) -> None:
    if dev_info is None:
        return
    if not isinstance(dev_info, dict):
        lines.append("- Dev logs: unavailable")
        return
    if "error" in dev_info:
        lines.append(f"- Dev logs: error ({dev_info['error']})")
        return
    lines.append(f"- Dev logs root: {dev_info.get('dev_root')}")
    lines.append(
        "- Dev sessions scanned: "
        f"{dev_info.get('sessions_scanned', 0)}/"
        f"{dev_info.get('session_files_total', 0)}"
    )
    lines.append(
        "- Dev events: "
        f"{dev_info.get('events_scanned', 0)} "
        f"(transcript={dev_info.get('transcript_events', 0)}, "
        f"empty={dev_info.get('empty_events', 0)}, "
        f"error={dev_info.get('error_events', 0)})"
    )
    lines.append(f"- Dev total words: {dev_info.get('total_words', 0)}")
    avg_latency = dev_info.get("avg_latency_ms")
    lines.append("- Dev avg latency: " + ("unknown" if avg_latency is None else f"{avg_latency} ms"))
    lines.append(f"- Dev parse errors: {dev_info.get('parse_errors', 0)}")
    latest_iso = dev_info.get("latest_event_iso")
    lines.append("- Dev latest event: " + (latest_iso if latest_iso else "none"))


def _append_pedantic_lines(lines: list[str], pedantic_info: Any) -> None:
    if pedantic_info is None:
        return
    if not isinstance(pedantic_info, dict):
        lines.append("- Pedantic advisory: unavailable")
        return
    refresh = pedantic_info.get("refresh")
    if "error" in pedantic_info:
        lines.append(f"- Pedantic advisory: error ({pedantic_info['error']})")
        return
    if not pedantic_info.get("artifact_found", False):
        lines.append("- Pedantic advisory: artifact unavailable")
        warning = pedantic_info.get("warning")
        if warning:
            lines.append(f"- Pedantic advisory note: {warning}")
        _append_pedantic_refresh_line(lines, refresh)
        return
    lines.append(
        "- Pedantic advisory: "
        f"{pedantic_info.get('observed_lints', 0)} lint ids / "
        f"{pedantic_info.get('warnings', 0)} warnings"
    )
    if int(pedantic_info.get("exit_code") or 0) != 0:
        lines.append(
            "- Pedantic advisory note: "
            f"last sweep failed (status={pedantic_info.get('status')}, "
            f"exit={pedantic_info.get('exit_code')})"
        )
    lines.append(
        "- Pedantic policy coverage: "
        f"reviewed={pedantic_info.get('reviewed_lints', 0)}, "
        f"unreviewed={pedantic_info.get('unreviewed_lints', 0)}"
    )
    top_candidates = pedantic_info.get("top_promote_candidates", [])
    if isinstance(top_candidates, list) and top_candidates:
        formatted = ", ".join(
            f"{row.get('lint')}={row.get('count')}"
            for row in top_candidates[:3]
            if isinstance(row, dict)
        )
        if formatted:
            lines.append(f"- Pedantic promote candidates: {formatted}")
    _append_pedantic_refresh_line(lines, refresh)
    policy_warnings = pedantic_info.get("policy_warnings", [])
    if isinstance(policy_warnings, list) and policy_warnings:
        lines.append(f"- Pedantic policy note: {policy_warnings[0]}")


def _append_pedantic_refresh_line(lines: list[str], refresh: Any) -> None:
    if isinstance(refresh, dict):
        lines.append(
            "- Pedantic refresh: "
            f"exit={refresh.get('returncode')} "
            f"skipped={refresh.get('skipped')}"
        )


def _append_quality_backlog_lines(lines: list[str], backlog: Any) -> None:
    if backlog is None:
        return
    if not isinstance(backlog, dict):
        lines.append("- Quality backlog: unavailable")
        return
    lines.append("")
    lines.extend(render_quality_backlog_markdown(backlog))


def _append_python_guard_backlog_lines(lines: list[str], backlog: Any) -> None:
    if backlog is None:
        return
    if not isinstance(backlog, dict):
        lines.append("- Python guard backlog: unavailable")
        return
    lines.append("")
    lines.extend(render_python_guard_markdown(backlog))
