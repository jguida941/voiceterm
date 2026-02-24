"""Parser registration helpers for status/report and operational tooling commands."""

from __future__ import annotations

import argparse


def add_reporting_parsers(
    sub: argparse._SubParsersAction,
    *,
    default_ci_limit: int,
) -> None:
    """Register status/report/list/audit-scaffold/hygiene parsers."""
    # status
    status_cmd = sub.add_parser("status", help="Summarize git + mutation status")
    status_cmd.add_argument(
        "--ci", action="store_true", help="Include recent GitHub runs"
    )
    status_cmd.add_argument("--ci-limit", type=int, default=default_ci_limit)
    status_cmd.add_argument(
        "--require-ci",
        action="store_true",
        help="Exit non-zero when CI fetch fails (implies --ci)",
    )
    status_cmd.add_argument("--format", choices=["json", "md", "text"], default="text")
    status_cmd.add_argument(
        "--dev-logs",
        action="store_true",
        help="Include guarded Dev Mode JSONL session summary",
    )
    status_cmd.add_argument(
        "--dev-root",
        help="Override dev-log root (default: $HOME/.voiceterm/dev)",
    )
    status_cmd.add_argument(
        "--dev-sessions-limit",
        type=int,
        default=5,
        help="Maximum recent session files to scan when --dev-logs",
    )
    status_cmd.add_argument(
        "--no-parallel",
        action="store_true",
        help="Run collection probes sequentially instead of in parallel",
    )
    status_cmd.add_argument("--output")
    status_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    status_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )

    # report
    report_cmd = sub.add_parser("report", help="Generate a JSON/MD report")
    report_cmd.add_argument(
        "--ci", action="store_true", help="Include recent GitHub runs"
    )
    report_cmd.add_argument("--ci-limit", type=int, default=default_ci_limit)
    report_cmd.add_argument("--format", choices=["json", "md"], default="md")
    report_cmd.add_argument(
        "--dev-logs",
        action="store_true",
        help="Include guarded Dev Mode JSONL session summary",
    )
    report_cmd.add_argument(
        "--dev-root",
        help="Override dev-log root (default: $HOME/.voiceterm/dev)",
    )
    report_cmd.add_argument(
        "--dev-sessions-limit",
        type=int,
        default=5,
        help="Maximum recent session files to scan when --dev-logs",
    )
    report_cmd.add_argument(
        "--no-parallel",
        action="store_true",
        help="Run collection probes sequentially instead of in parallel",
    )
    report_cmd.add_argument("--output")
    report_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    report_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )

    # list
    list_cmd = sub.add_parser("list", help="List devctl commands and profiles")
    list_cmd.add_argument("--format", choices=["json", "md"], default="md")
    list_cmd.add_argument("--output")

    # audit-scaffold
    audit_cmd = sub.add_parser(
        "audit-scaffold",
        help="Generate dev/active Rust remediation scaffold from guard findings",
    )
    audit_cmd.add_argument(
        "--since-ref", help="Optional base ref for changed-file guard scripts"
    )
    audit_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref used with --since-ref (default: HEAD)",
    )
    audit_cmd.add_argument(
        "--source-guards",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run guard scripts and embed findings in scaffold (default: enabled)",
    )
    audit_cmd.add_argument(
        "--output-path",
        default="dev/active/RUST_AUDIT_FINDINGS.md",
        help="Scaffold output path (must stay under dev/active/)",
    )
    audit_cmd.add_argument(
        "--template-path",
        default="dev/config/templates/rust_audit_findings_template.md",
        help="Template markdown path",
    )
    audit_cmd.add_argument(
        "--trigger",
        default="manual",
        help="Short trigger label (for example check-ai-guard or workflow lane name)",
    )
    audit_cmd.add_argument(
        "--trigger-steps",
        help="Comma-separated failing guard step names that triggered this scaffold",
    )
    audit_cmd.add_argument(
        "--force", action="store_true", help="Overwrite existing scaffold file"
    )
    audit_cmd.add_argument(
        "--yes", action="store_true", help="Skip overwrite confirmation"
    )
    audit_cmd.add_argument("--dry-run", action="store_true")
    audit_cmd.add_argument("--format", choices=["json", "md"], default="md")
    audit_cmd.add_argument("--output")
    audit_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    audit_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")

    # hygiene
    hygiene_cmd = sub.add_parser(
        "hygiene", help="Audit archive/ADR/scripts governance hygiene"
    )
    hygiene_cmd.add_argument(
        "--fix",
        action="store_true",
        help="Remove detected dev/scripts/**/__pycache__ directories after audit",
    )
    hygiene_cmd.add_argument("--format", choices=["json", "md"], default="md")
    hygiene_cmd.add_argument("--output")
    hygiene_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    hygiene_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )
