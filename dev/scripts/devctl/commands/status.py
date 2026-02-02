"""devctl status command implementation."""

import json
from datetime import datetime

from ..collect import collect_ci_runs, collect_git_status, collect_mutation_summary
from ..common import pipe_output, write_output


def run(args) -> int:
    """Render a status summary from git and mutation results."""
    report = {
        "command": "status",
        "timestamp": datetime.now().isoformat(),
        "git": collect_git_status(),
        "mutants": collect_mutation_summary(),
    }
    if args.ci:
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
        output = "\n".join(lines)
    else:
        output = json.dumps(report, indent=2)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0
