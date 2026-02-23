"""devctl path-rewrite command implementation."""

from __future__ import annotations

import json
from datetime import datetime

from ..common import pipe_output, write_output
from ..path_audit import rewrite_legacy_path_references

MAX_MD_CHANGES = 30


def _render_md(report: dict) -> str:
    lines = ["# devctl path-rewrite", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- dry_run: {report['dry_run']}")
    lines.append(f"- checked_files: {report['checked_file_count']}")
    lines.append(f"- changed_files: {report['changed_file_count']}")
    lines.append(f"- replacements: {report['replacement_count']}")
    if report.get("error"):
        lines.append(f"- error: {report['error']}")

    if report["changes"]:
        lines.append("")
        lines.append("## Updated Files")
        for item in report["changes"][:MAX_MD_CHANGES]:
            lines.append(f"- {item['file']} ({item['replacements']} replacements)")
        remaining = len(report["changes"]) - MAX_MD_CHANGES
        if remaining > 0:
            lines.append(f"- ... and {remaining} more")

    post_scan = report.get("post_scan")
    if post_scan is not None:
        lines.append("")
        lines.append("## Post-Scan")
        lines.append(f"- ok: {post_scan['ok']}")
        lines.append(f"- violations: {len(post_scan['violations'])}")
    return "\n".join(lines)


def run(args) -> int:
    """Rewrite stale legacy check-script references."""
    rewrite_report = rewrite_legacy_path_references(dry_run=args.dry_run)
    report = {
        "command": "path-rewrite",
        "timestamp": datetime.now().isoformat(),
        **rewrite_report,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = _render_md(report)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0 if report["ok"] else 1
