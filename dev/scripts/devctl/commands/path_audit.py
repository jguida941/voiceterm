"""devctl path-audit command implementation."""

from __future__ import annotations

import json
from datetime import datetime

from ..common import pipe_output, write_output
from ..path_audit import scan_legacy_path_references

MAX_MD_VIOLATIONS = 30


def _render_md(report: dict) -> str:
    lines = ["# devctl path-audit", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- checked_files: {report['checked_file_count']}")
    lines.append(f"- violations: {len(report['violations'])}")
    lines.append(
        "- excluded_prefixes: "
        + (", ".join(report["excluded_prefixes"]) if report["excluded_prefixes"] else "none")
    )
    if report.get("error"):
        lines.append(f"- error: {report['error']}")

    if report["violations"]:
        lines.append("")
        lines.append("## Stale References")
        for violation in report["violations"][:MAX_MD_VIOLATIONS]:
            lines.append(
                "- {file}:{line} references `{legacy}`; use `{replacement}`".format(
                    file=violation["file"],
                    line=violation["line"],
                    legacy=violation["legacy_path"],
                    replacement=violation["replacement_path"],
                )
            )
        remaining = len(report["violations"]) - MAX_MD_VIOLATIONS
        if remaining > 0:
            lines.append(f"- ... and {remaining} more")
    return "\n".join(lines)


def run(args) -> int:
    """Scan for legacy script-path references and fail when any are found."""
    scan = scan_legacy_path_references()
    report = {
        "command": "path-audit",
        "timestamp": datetime.now().isoformat(),
        **scan,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = _render_md(report)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0 if report["ok"] else 1
