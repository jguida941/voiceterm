"""devctl report command implementation."""

import json
from datetime import datetime

from ..collect import (
    collect_ci_runs,
    collect_dev_log_summary,
    collect_git_status,
    collect_mutation_summary,
)
from ..common import pipe_output, write_output


def run(args) -> int:
    """Generate a JSON or Markdown report."""
    report = {
        "command": "report",
        "timestamp": datetime.now().isoformat(),
        "git": collect_git_status(),
        "mutants": collect_mutation_summary(),
    }
    if args.ci:
        report["ci"] = collect_ci_runs(args.ci_limit)
    if getattr(args, "dev_logs", False):
        report["dev_logs"] = collect_dev_log_summary(
            dev_root=getattr(args, "dev_root", None),
            session_limit=getattr(args, "dev_sessions_limit", 5),
        )

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        lines = ["# devctl report", ""]
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
            lines.append(f"- Mutants: {mutants_info['error']}")
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
        if args.ci and "ci" in report:
            ci_info = report["ci"]
            if "error" in ci_info:
                lines.append(f"- CI: {ci_info['error']}")
            else:
                lines.append(f"- CI runs: {len(ci_info.get('runs', []))}")
        if getattr(args, "dev_logs", False):
            dev_info = report.get("dev_logs", {})
            if "error" in dev_info:
                lines.append(f"- Dev logs: {dev_info['error']}")
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
                lines.append(
                    "- Dev latest event: "
                    + (latest_iso if latest_iso else "none")
                )
        output = "\n".join(lines)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0
