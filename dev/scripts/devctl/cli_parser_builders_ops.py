"""Parser builders for release, docs, reporting, and governance commands."""

from __future__ import annotations

import argparse


def add_release_parsers(sub: argparse._SubParsersAction) -> None:
    """Register release and distribution command parsers."""
    release_cmd = sub.add_parser(
        "release", help="Run tag + notes release flow (legacy-compatible)"
    )
    release_cmd.add_argument("--version", required=True)
    release_cmd.add_argument(
        "--prepare-release",
        action="store_true",
        help="Auto-update release metadata files before tag/notes steps",
    )
    release_cmd.add_argument("--homebrew", action="store_true")
    release_cmd.add_argument(
        "--yes", action="store_true", help="Skip confirmation prompts"
    )
    release_cmd.add_argument("--allow-ci", action="store_true")
    release_cmd.add_argument("--dry-run", action="store_true")

    ship_cmd = sub.add_parser(
        "ship", help="Run release/distribution steps from one control-plane command"
    )
    ship_cmd.add_argument("--version", required=True)
    ship_cmd.add_argument(
        "--prepare-release",
        action="store_true",
        help="Auto-update release metadata files before verify/tag/publish steps",
    )
    ship_cmd.add_argument(
        "--verify", action="store_true", help="Run release verification checks"
    )
    ship_cmd.add_argument(
        "--verify-docs", action="store_true", help="Include docs-check in verify step"
    )
    ship_cmd.add_argument("--tag", action="store_true", help="Create/push git tag")
    ship_cmd.add_argument(
        "--notes", action="store_true", help="Generate release notes markdown"
    )
    ship_cmd.add_argument("--github", action="store_true", help="Create GitHub release")
    ship_cmd.add_argument(
        "--github-fail-on-no-commits",
        action="store_true",
        help="Pass --fail-on-no-commits to gh release create",
    )
    ship_cmd.add_argument("--pypi", action="store_true", help="Publish PyPI package")
    ship_cmd.add_argument("--homebrew", action="store_true", help="Update Homebrew tap")
    ship_cmd.add_argument(
        "--verify-pypi", action="store_true", help="Verify PyPI JSON endpoint version"
    )
    ship_cmd.add_argument("--notes-output", help="Release notes output file path")
    ship_cmd.add_argument(
        "--yes", action="store_true", help="Skip confirmation prompts"
    )
    ship_cmd.add_argument("--allow-ci", action="store_true")
    ship_cmd.add_argument("--dry-run", action="store_true")
    ship_cmd.add_argument("--format", choices=["text", "json", "md"], default="text")
    ship_cmd.add_argument("--output")
    ship_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    ship_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")

    notes_cmd = sub.add_parser(
        "release-notes", help="Generate markdown release notes from git diff history"
    )
    notes_cmd.add_argument("--version", required=True)
    notes_cmd.add_argument(
        "--output",
        help="Output markdown path (default: /tmp/voiceterm-release-vX.Y.Z.md)",
    )
    notes_cmd.add_argument(
        "--end-ref",
        help="End ref for compare range (default: vX.Y.Z if tag exists, else HEAD)",
    )
    notes_cmd.add_argument(
        "--previous-tag",
        help="Explicit previous tag (default: latest prior v* tag)",
    )
    notes_cmd.add_argument("--dry-run", action="store_true")

    homebrew_cmd = sub.add_parser("homebrew", help="Run Homebrew tap update flow")
    homebrew_cmd.add_argument("--version", required=True)
    homebrew_cmd.add_argument(
        "--yes", action="store_true", help="Skip confirmation prompts"
    )
    homebrew_cmd.add_argument("--allow-ci", action="store_true")
    homebrew_cmd.add_argument("--dry-run", action="store_true")

    pypi_cmd = sub.add_parser("pypi", help="Run PyPI build/check/upload flow")
    pypi_cmd.add_argument(
        "--upload", action="store_true", help="Upload package to PyPI"
    )
    pypi_cmd.add_argument(
        "--yes", action="store_true", help="Skip confirmation prompts"
    )
    pypi_cmd.add_argument("--allow-ci", action="store_true")
    pypi_cmd.add_argument("--dry-run", action="store_true")


def add_docs_and_reporting_parsers(
    sub: argparse._SubParsersAction,
    *,
    default_ci_limit: int,
) -> None:
    """Register docs, status, and report command parsers."""
    docs_cmd = sub.add_parser("docs-check", help="Verify user-facing docs are updated")
    docs_cmd.add_argument(
        "--user-facing", action="store_true", help="Enforce user-facing doc updates"
    )
    docs_cmd.add_argument(
        "--strict", action="store_true", help="Require all user docs when --user-facing"
    )
    docs_cmd.add_argument(
        "--strict-tooling",
        action="store_true",
        help="Require all canonical maintainer docs for tooling/release changes",
    )
    docs_cmd.add_argument(
        "--since-ref",
        help="Use commit-range mode by comparing changes from this ref (e.g. origin/develop, HEAD~1)",
    )
    docs_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Range-mode head ref used with --since-ref (default: HEAD)",
    )
    docs_cmd.add_argument("--format", choices=["json", "md"], default="md")
    docs_cmd.add_argument("--output")
    docs_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    docs_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")

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


def add_governance_parsers(sub: argparse._SubParsersAction) -> None:
    """Register list, audit-scaffold, and hygiene parser definitions."""
    list_cmd = sub.add_parser("list", help="List devctl commands and profiles")
    list_cmd.add_argument("--format", choices=["json", "md"], default="md")
    list_cmd.add_argument("--output")

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
