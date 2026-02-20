"""devctl status command implementation."""

import json
from datetime import datetime

from ..collect import collect_ci_runs, collect_git_status, collect_mutation_summary
from ..common import pipe_output, write_output


def run(args) -> int:
    """Render a status summary from git and mutation results."""
    ci_requested = bool(args.ci or getattr(args, "require_ci", False))
    report = {
        "command": "status",
        "timestamp": datetime.now().isoformat(),
        "git": collect_git_status(),
        "mutants": collect_mutation_summary(),
    }
    if ci_requested:
        report["ci"] = collect_ci_runs(args.ci_limit)

    if args.format == "json":
        output = json.dumps(report, indent=2)
    elif args.format == "md":
        lines = ["# devctl status", ""]
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
            lines.append(f"- Mutation score: {score_label}")
            lines.append(f"- Mutation outcomes: {outcomes}")
            age_label = "unknown" if age_hours is None else f"{float(age_hours):.2f}h"
            lines.append(f"- Mutation outcomes updated: {updated_at} ({age_label} old)")
        if ci_requested:
            ci_info = report.get("ci", {})
            if "error" in ci_info:
                lines.append(f"- CI: error ({ci_info['error']})")
            else:
                runs = ci_info.get("runs", [])
                lines.append(f"- CI runs: {len(runs)}")
                for run in runs[:5]:
                    title = run.get("displayTitle", "unknown")
                    status = run.get("status", "unknown")
                    conclusion = run.get("conclusion") or "pending"
                    lines.append(f"  - {title}: {status}/{conclusion}")
        output = "\n".join(lines)
    else:
        output = json.dumps(report, indent=2)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    if getattr(args, "require_ci", False):
        ci_info = report.get("ci", {})
        if "error" in ci_info:
            return 2
    return 0
