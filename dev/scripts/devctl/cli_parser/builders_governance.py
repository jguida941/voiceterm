"""Parser builders for list, audit-scaffold, and hygiene devctl commands."""

from __future__ import annotations

import argparse

from ..common import add_standard_output_arguments


def add_list_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `list` parser."""
    list_cmd = sub.add_parser("list", help="List devctl commands and profiles")
    list_cmd.add_argument("--format", choices=["json", "md"], default="md")
    list_cmd.add_argument("--output")


def add_audit_scaffold_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `audit-scaffold` parser."""
    audit_cmd = sub.add_parser(
        "audit-scaffold",
        help="Generate Rust remediation scaffold from guard findings",
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
        default="dev/reports/audits/RUST_AUDIT_FINDINGS.md",
        help="Scaffold output path (must be under dev/reports/audits/)",
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
    add_standard_output_arguments(audit_cmd)


def add_hygiene_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `hygiene` parser."""
    hygiene_cmd = sub.add_parser(
        "hygiene", help="Audit archive/ADR/scripts governance hygiene"
    )
    hygiene_cmd.add_argument(
        "--fix",
        action="store_true",
        help="Remove detected dev/scripts/**/__pycache__ directories after audit",
    )
    hygiene_cmd.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Treat hygiene warnings as blocking failures",
    )
    hygiene_cmd.add_argument(
        "--ignore-warning-source",
        action="append",
        choices=("mutation_badge",),
        default=[],
        help=(
            "Keep the selected warning family visible in output but exclude it "
            "from --strict-warnings failure counting"
        ),
    )
    add_standard_output_arguments(hygiene_cmd)


def add_governance_parsers(sub: argparse._SubParsersAction) -> None:
    """Register list/audit-scaffold/hygiene parser definitions."""
    add_list_parser(sub)
    add_audit_scaffold_parser(sub)
    add_hygiene_parser(sub)
