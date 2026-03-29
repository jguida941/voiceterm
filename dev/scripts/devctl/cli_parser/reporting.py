"""Parser registration helpers for status/report and operational tooling commands."""

from __future__ import annotations

import argparse

from ..autonomy.status_parsers import (
    add_autonomy_report_parser,
    add_mobile_status_parser,
    add_phone_status_parser,
)
from ..common import add_standard_output_arguments
from ..repo_packs import active_path_config as _active_path_config
from ..data_science.parser import add_data_science_parser
from ..governance_bootstrap_parser import add_governance_bootstrap_parser
from ..governance_export_parser import add_governance_export_parser
from ..governance_review_parser import add_governance_review_parser
from ..probe_report_parser import add_probe_report_parser
from ..quality_policy_parser import add_quality_policy_parser
from ..ralph_status_parser import add_ralph_status_parser
from .builders_ops import (
    add_audit_scaffold_parser,
    add_docs_check_parser,
    add_hygiene_parser,
    add_list_parser,
    add_report_parser,
    add_status_parser,
)
from .hygiene import add_process_hygiene_parsers


def add_reporting_parsers(
    sub: argparse._SubParsersAction,
    *,
    default_ci_limit: int,
) -> None:
    """Register reporting, tooling-status, and operational parsers."""
    add_docs_check_parser(sub)
    add_status_parser(sub, default_ci_limit=default_ci_limit)
    add_report_parser(sub, default_ci_limit=default_ci_limit)
    add_list_parser(sub)
    add_process_hygiene_parsers(sub)
    add_compat_matrix_parser(sub)
    add_mcp_parser(sub)
    add_data_science_parser(sub)
    add_quality_policy_parser(sub)
    add_governance_export_parser(sub)
    add_governance_bootstrap_parser(sub)
    add_governance_review_parser(sub)
    add_probe_report_parser(sub)
    add_autonomy_report_parser(sub)
    add_phone_status_parser(sub)
    add_mobile_status_parser(sub)
    add_ralph_status_parser(sub)
    add_autonomy_swarm_parser(sub)
    add_audit_scaffold_parser(sub)
    add_hygiene_parser(sub)


def add_compat_matrix_parser(sub: argparse._SubParsersAction) -> None:
    compat_matrix_cmd = sub.add_parser(
        "compat-matrix",
        help="Validate IDE/provider compatibility matrix metadata and smoke coverage",
    )
    compat_matrix_cmd.add_argument(
        "--no-smoke",
        action="store_true",
        help="Run schema/coverage validation only (skip runtime enum smoke checks)",
    )
    add_standard_output_arguments(compat_matrix_cmd)


def add_mcp_parser(sub: argparse._SubParsersAction) -> None:
    mcp_cmd = sub.add_parser(
        "mcp",
        help="Read-only MCP adapter contract + stdio server for devctl surfaces",
    )
    mcp_cmd.add_argument(
        "--serve-stdio",
        action="store_true",
        help="Serve MCP JSON-RPC over stdio (Content-Length framing)",
    )
    mcp_cmd.add_argument(
        "--tool",
        help="Invoke one allowlisted read-only tool and print result output",
    )
    mcp_cmd.add_argument(
        "--tool-args-json",
        help="JSON object string passed to --tool as arguments",
    )
    add_standard_output_arguments(mcp_cmd)


def add_autonomy_swarm_parser(sub: argparse._SubParsersAction) -> None:
    autonomy_swarm_cmd = sub.add_parser(
        "autonomy-swarm",
        help="Run an adaptive autonomy swarm with metadata-driven agent sizing",
    )
    autonomy_swarm_cmd.add_argument("--repo", help="owner/repo (optional; falls back to env/repo detection)")
    autonomy_swarm_cmd.add_argument("--run-label", help="Optional swarm run label")
    autonomy_swarm_cmd.add_argument(
        "--output-root",
        default=_active_path_config().autonomy_swarm_root_rel,
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
        help=("Nested fix command forwarded to each autonomy-loop worker when " "--mode is plan-then-fix/fix-only"),
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
        default=_active_path_config().autonomy_source_root_rel,
        help="Source root used by post-audit autonomy-report",
    )
    autonomy_swarm_cmd.add_argument(
        "--audit-library-root",
        default=_active_path_config().autonomy_library_root_rel,
        help="Library root used by post-audit autonomy-report",
    )
    autonomy_swarm_cmd.add_argument(
        "--audit-event-log",
        default=_active_path_config().audit_event_log_rel,
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
    add_standard_output_arguments(autonomy_swarm_cmd)
    autonomy_swarm_cmd.add_argument("--json-output")
