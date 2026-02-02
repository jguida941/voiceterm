"""devctl report command implementation."""

import json
from datetime import datetime

from ..collect import collect_ci_runs, collect_git_status, collect_mutation_summary
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
            score = mutants_info.get("results", {}).get("score")
            lines.append(f"- Mutation score: {score}%")
        if args.ci and "ci" in report:
            ci_info = report["ci"]
            if "error" in ci_info:
                lines.append(f"- CI: {ci_info['error']}")
            else:
                lines.append(f"- CI runs: {len(ci_info.get('runs', []))}")
        output = "\n".join(lines)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0
