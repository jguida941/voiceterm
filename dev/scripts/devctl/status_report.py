"""Shared data collection + markdown rendering for `status` and `report`.

Why this exists:
- `status` and `report` should show the same fields in the same way
- one renderer prevents accidental output drift over time
"""

from __future__ import annotations

from datetime import datetime

from .collect import (
    collect_ci_runs,
    collect_dev_log_summary,
    collect_git_status,
    collect_mutation_summary,
)


def build_project_report(
    *,
    command: str,
    include_ci: bool,
    ci_limit: int,
    include_dev_logs: bool,
    dev_root: str | None,
    dev_sessions_limit: int,
) -> dict:
    """Collect the standard project snapshot used by both commands."""
    report = {
        "command": command,
        "timestamp": datetime.now().isoformat(),
        "git": collect_git_status(),
        "mutants": collect_mutation_summary(),
    }
    if include_ci:
        report["ci"] = collect_ci_runs(ci_limit)
    if include_dev_logs:
        report["dev_logs"] = collect_dev_log_summary(
            dev_root=dev_root,
            session_limit=dev_sessions_limit,
        )
    return report


def render_project_markdown(
    report: dict,
    *,
    title: str,
    include_ci_details: bool,
    ci_details_limit: int = 5,
) -> str:
    """Render markdown once for both commands so wording stays aligned."""
    lines = [f"# {title}", ""]
    git_info = report.get("git", {})
    if "error" in git_info:
        lines.append(f"- Git: {git_info['error']}")
    else:
        lines.append(f"- Branch: {git_info.get('branch', 'unknown')}")
        lines.append(f"- Changelog updated: {git_info.get('changelog_updated')}")
        lines.append(f"- Master plan updated: {git_info.get('master_plan_updated')}")
        lines.append(f"- Changed files: {len(git_info.get('changes', []))}")

    mutants_info = report.get("mutants", {})
    if "error" in mutants_info:
        lines.append(f"- Mutation score: error ({mutants_info['error']})")
    else:
        results = mutants_info.get("results", {})
        if not isinstance(results, dict):
            results = {}
        score = results.get("score")
        outcomes = results.get("outcomes_path", "unknown")
        updated_at = results.get("outcomes_updated_at", "unknown")
        age_hours = results.get("outcomes_age_hours")
        score_label = "unknown" if score is None else f"{float(score):.2f}%"
        age_label = "unknown" if age_hours is None else f"{float(age_hours):.2f}h"
        lines.append(f"- Mutation score: {score_label}")
        lines.append(f"- Mutation outcomes: {outcomes}")
        lines.append(f"- Mutation outcomes updated: {updated_at} ({age_label} old)")

    if "ci" in report:
        ci_info = report["ci"]
        if "error" in ci_info:
            lines.append(f"- CI: error ({ci_info['error']})")
        else:
            runs = ci_info.get("runs", [])
            lines.append(f"- CI runs: {len(runs)}")
            if include_ci_details:
                for run in runs[:ci_details_limit]:
                    run_title = run.get("displayTitle", "unknown")
                    status = run.get("status", "unknown")
                    conclusion = run.get("conclusion") or "pending"
                    lines.append(f"  - {run_title}: {status}/{conclusion}")

    if "dev_logs" in report:
        dev_info = report.get("dev_logs", {})
        if "error" in dev_info:
            lines.append(f"- Dev logs: error ({dev_info['error']})")
        else:
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
            lines.append(
                "- Dev avg latency: "
                + ("unknown" if avg_latency is None else f"{avg_latency} ms")
            )
            lines.append(f"- Dev parse errors: {dev_info.get('parse_errors', 0)}")
            latest_iso = dev_info.get("latest_event_iso")
            lines.append("- Dev latest event: " + (latest_iso if latest_iso else "none"))

    return "\n".join(lines)
