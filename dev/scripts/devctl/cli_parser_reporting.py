"""Parser registration helpers for status/report and operational tooling commands."""

from __future__ import annotations

import argparse

from .autonomy_status_parsers import (
    add_autonomy_report_parser,
    add_phone_status_parser,
)


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

    # autonomy-report + phone-status
    add_autonomy_report_parser(sub)
    add_phone_status_parser(sub)

    # autonomy-swarm
    autonomy_swarm_cmd = sub.add_parser(
        "autonomy-swarm",
        help="Run an adaptive autonomy swarm with metadata-driven agent sizing",
    )
    autonomy_swarm_cmd.add_argument(
        "--repo", help="owner/repo (optional; falls back to env/repo detection)"
    )
    autonomy_swarm_cmd.add_argument("--run-label", help="Optional swarm run label")
    autonomy_swarm_cmd.add_argument(
        "--output-root",
        default="dev/reports/autonomy/swarms",
        help="Root directory for swarm run bundles",
    )
    autonomy_swarm_cmd.add_argument(
        "--agents",
        type=int,
        help="Explicit agent count override (disables adaptive auto-sizing)",
    )
    autonomy_swarm_cmd.add_argument(
        "--adaptive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable metadata-driven agent sizing (default: enabled)",
    )
    autonomy_swarm_cmd.add_argument("--min-agents", type=int, default=1)
    autonomy_swarm_cmd.add_argument("--max-agents", type=int, default=20)
    autonomy_swarm_cmd.add_argument(
        "--question",
        help="Optional problem statement text used for complexity scoring",
    )
    autonomy_swarm_cmd.add_argument(
        "--question-file",
        help="Optional file containing problem statement text",
    )
    autonomy_swarm_cmd.add_argument(
        "--prompt-tokens",
        type=int,
        help="Optional known prompt-token estimate (otherwise estimated from question text)",
    )
    autonomy_swarm_cmd.add_argument(
        "--diff-ref",
        default="origin/develop",
        help="Git base ref for change-size metadata scoring",
    )
    autonomy_swarm_cmd.add_argument(
        "--target-paths",
        nargs="*",
        default=[],
        help="Optional path filters for diff metadata scoring",
    )
    autonomy_swarm_cmd.add_argument(
        "--token-budget",
        type=int,
        default=0,
        help="Optional total token budget used to cap adaptive agent count",
    )
    autonomy_swarm_cmd.add_argument(
        "--per-agent-token-cost",
        type=int,
        default=12000,
        help="Estimated token cost per agent used for token-budget capping",
    )
    autonomy_swarm_cmd.add_argument("--branch-base", default="develop")
    autonomy_swarm_cmd.add_argument(
        "--mode",
        choices=["report-only", "plan-then-fix", "fix-only"],
        default="report-only",
    )
    autonomy_swarm_cmd.add_argument(
        "--fix-command",
        help=(
            "Nested fix command forwarded to each autonomy-loop worker when "
            "--mode is plan-then-fix/fix-only"
        ),
    )
    autonomy_swarm_cmd.add_argument("--max-rounds", type=int, default=1)
    autonomy_swarm_cmd.add_argument("--max-hours", type=float, default=1.0)
    autonomy_swarm_cmd.add_argument("--max-tasks", type=int, default=1)
    autonomy_swarm_cmd.add_argument("--checkpoint-every", type=int, default=1)
    autonomy_swarm_cmd.add_argument("--loop-max-attempts", type=int, default=1)
    autonomy_swarm_cmd.add_argument("--parallel-workers", type=int, default=4)
    autonomy_swarm_cmd.add_argument("--agent-timeout-seconds", type=int, default=1800)
    autonomy_swarm_cmd.add_argument("--plan-only", action="store_true")
    autonomy_swarm_cmd.add_argument("--dry-run", action="store_true")
    autonomy_swarm_cmd.add_argument(
        "--post-audit",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run autonomy-report digest automatically after swarm execution",
    )
    autonomy_swarm_cmd.add_argument(
        "--reviewer-lane",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Reserve one swarm slot for AGENT-REVIEW post-audit lane when executing",
    )
    autonomy_swarm_cmd.add_argument(
        "--audit-run-label",
        help="Optional post-audit digest label (default: <swarm-run-label>-digest)",
    )
    autonomy_swarm_cmd.add_argument(
        "--audit-source-root",
        default="dev/reports/autonomy",
        help="Source root used by post-audit autonomy-report",
    )
    autonomy_swarm_cmd.add_argument(
        "--audit-library-root",
        default="dev/reports/autonomy/library",
        help="Library root used by post-audit autonomy-report",
    )
    autonomy_swarm_cmd.add_argument(
        "--audit-event-log",
        default="dev/reports/audits/devctl_events.jsonl",
        help="Event log path used by post-audit autonomy-report",
    )
    autonomy_swarm_cmd.add_argument(
        "--audit-refresh-orchestrate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Refresh orchestrate status/watch snapshots during post-audit run",
    )
    autonomy_swarm_cmd.add_argument(
        "--audit-copy-sources",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Copy source artifacts into the post-audit bundle",
    )
    autonomy_swarm_cmd.add_argument(
        "--audit-charts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate charts in the post-audit bundle",
    )
    autonomy_swarm_cmd.add_argument(
        "--charts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate matplotlib charts in swarm bundle",
    )
    autonomy_swarm_cmd.add_argument("--format", choices=["json", "md"], default="md")
    autonomy_swarm_cmd.add_argument("--output")
    autonomy_swarm_cmd.add_argument("--json-output")
    autonomy_swarm_cmd.add_argument(
        "--pipe-command", help="Pipe report output to a command"
    )
    autonomy_swarm_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )

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
