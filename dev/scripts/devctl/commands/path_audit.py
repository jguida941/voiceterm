"""devctl path-audit command implementation."""

from __future__ import annotations

import json

from ..common import emit_output, pipe_output, write_output
from ..time_utils import utc_timestamp
from ..path_audit import scan_path_audit_references

MAX_MD_VIOLATIONS = 30


def _render_md(report: dict) -> str:
    lines = ["# devctl path-audit", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- checked_files: {report['checked_file_count']}")
    if "unique_checked_file_count" in report:
        lines.append(f"- unique_checked_files: {report['unique_checked_file_count']}")
    lines.append(f"- violations: {len(report['violations'])}")
    lines.append(f"- legacy_violations: {report.get('legacy_violation_count', 0)}")
    lines.append(
        f"- workspace_contract_violations: {report.get('workspace_contract_violation_count', 0)}"
    )
    lines.append(
        "- excluded_prefixes: "
        + (
            ", ".join(report["excluded_prefixes"])
            if report["excluded_prefixes"]
            else "none"
        )
    )
    if report.get("error"):
        lines.append(f"- error: {report['error']}")

    if report["violations"]:
        lines.append("")
        lines.append("## Stale References")
        for violation in report["violations"][:MAX_MD_VIOLATIONS]:
            violation_type = violation.get("violation_type", "legacy_check_path")
            lines.append(
                "- [{kind}] {file}:{line} references `{legacy}`; use `{replacement}`".format(
                    kind=violation_type,
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
    scan = scan_path_audit_references()
    ok = bool(scan.get("ok"))
    errors = _command_errors(scan)
    report = {
        "command": "path-audit",
        "timestamp": utc_timestamp(),
        **scan,
        "ok": ok,
        "exit_ok": ok,
        "exit_code": 0 if ok else 1,
        "status": "ok" if ok else "blocked",
        "errors": errors,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = _render_md(report)

    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_rc != 0:
        return pipe_rc
    return 0 if report["ok"] else 1


def _command_errors(scan: dict) -> list[str]:
    """Return command-level errors without dropping detailed violation rows."""
    errors: list[str] = []
    error = str(scan.get("error") or "").strip()
    if error:
        errors.append(error)
    violation_count = len(scan.get("violations") or [])
    if violation_count:
        errors.append(f"path_audit_violations={violation_count}")
    return errors
