"""Parser registration for governance and simple policy-backed commands."""

from __future__ import annotations

import argparse

from ..common import add_standard_output_arguments
from .simple_lanes_parser import (
    add_launcher_check_parser,
    add_launcher_policy_parser,
    add_launcher_probes_parser,
    add_tandem_validate_parser,
)


def add_governance_import_findings_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `governance-import-findings` parser."""
    import_cmd = sub.add_parser(
        "governance-import-findings",
        help=(
            "Import raw external findings into a machine-readable ledger and "
            "summarize adjudication coverage against governance-review"
        ),
    )
    import_cmd.add_argument(
        "--input",
        help="Optional JSON/JSONL file containing raw external findings to import",
    )
    import_cmd.add_argument(
        "--input-format",
        choices=["auto", "json", "jsonl"],
        default="auto",
        help="Input format for --input (default: auto)",
    )
    import_cmd.add_argument(
        "--log-path",
        help=(
            "JSONL path for imported external findings "
            "(default: dev/reports/governance/external_pilot_findings.jsonl)"
        ),
    )
    import_cmd.add_argument(
        "--summary-root",
        help=(
            "Directory used for latest imported-finding summary artifacts "
            "(default: dev/reports/governance/external_findings_latest)"
        ),
    )
    import_cmd.add_argument(
        "--governance-review-log",
        help=(
            "Governance review JSONL used to measure adjudication coverage "
            "(default: dev/reports/governance/finding_reviews.jsonl)"
        ),
    )
    import_cmd.add_argument(
        "--max-rows",
        type=int,
        default=10_000,
        help="Maximum imported finding rows sampled when rendering the summary",
    )
    import_cmd.add_argument(
        "--max-governance-review-rows",
        type=int,
        default=5_000,
        help="Maximum governance review rows sampled when rendering the summary",
    )
    import_cmd.add_argument("--repo-name", help="Default repo name for imported rows")
    import_cmd.add_argument("--repo-path", help="Default repo path for imported rows")
    import_cmd.add_argument("--run-id", help="Default import run id / corpus batch label")
    import_cmd.add_argument("--check-id", help="Default check/rule id for imported rows")
    import_cmd.add_argument(
        "--signal-type",
        choices=["guard", "probe", "audit"],
        help="Default signal type for imported rows",
    )
    import_cmd.add_argument("--severity", choices=["low", "medium", "high", "critical"])
    import_cmd.add_argument("--risk-type", help="Default risk type/category label")
    import_cmd.add_argument("--source-model", help="Default source model/agent label")
    import_cmd.add_argument(
        "--source-command",
        help="Default command/surface label that produced the imported rows",
    )
    import_cmd.add_argument(
        "--scan-mode",
        choices=["working-tree", "commit-range", "adoption-scan", "absolute", "external"],
        help="Default scan mode for imported rows",
    )
    import_cmd.add_argument("--notes", help="Default note attached to imported rows")
    add_standard_output_arguments(
        import_cmd,
        format_choices=("json", "md"),
        default_format="md",
    )


def add_governance_quality_feedback_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `governance-quality-feedback` parser."""
    cmd = sub.add_parser(
        "governance-quality-feedback",
        help=(
            "Build a composite quality feedback report with Halstead metrics, "
            "false-positive analysis, per-check scores, and AI recommendations"
        ),
    )
    cmd.add_argument(
        "--repo-path",
        help="Optional repo root override (default: current working directory)",
    )
    cmd.add_argument(
        "--repo-name",
        help="Optional repo name override (default: directory basename)",
    )
    cmd.add_argument(
        "--governance-review-log",
        help=(
            "Path override for finding_reviews.jsonl "
            "(default: dev/reports/governance/finding_reviews.jsonl)"
        ),
    )
    cmd.add_argument(
        "--external-finding-log",
        help="Path override for external findings log",
    )
    cmd.add_argument(
        "--max-review-rows",
        type=int,
        default=5_000,
        help="Maximum governance review rows sampled (default: 5000)",
    )
    cmd.add_argument(
        "--max-external-rows",
        type=int,
        default=10_000,
        help="Maximum external finding rows sampled (default: 10000)",
    )
    cmd.add_argument(
        "--halstead-max-files",
        type=int,
        default=5_000,
        help="Maximum source files analyzed by Halstead scanner (default: 5000)",
    )
    cmd.add_argument(
        "--previous-snapshot",
        help="Path to previous JSON snapshot for delta comparison",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("json", "md"),
        default_format="md",
    )


def add_governance_draft_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `governance-draft` parser."""
    draft_cmd = sub.add_parser(
        "governance-draft",
        help="Scan the current repo and emit a ProjectGovernance payload from local facts",
    )
    draft_cmd.add_argument(
        "--repo-root",
        help="Override repo root path",
    )
    draft_cmd.add_argument(
        "--quality-policy",
        help="Override path to devctl repo policy JSON",
    )
    add_standard_output_arguments(
        draft_cmd,
        format_choices=("json", "md"),
        default_format="md",
    )


def add_doc_authority_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `doc-authority` parser."""
    cmd = sub.add_parser(
        "doc-authority",
        help=(
            "Scan governed markdown docs and emit a doc-authority registry "
            "report with budgets, overlaps, and consolidation signals"
        ),
    )
    cmd.add_argument(
        "--repo-path",
        help="Optional repo root override (default: current working directory)",
    )
    cmd.add_argument(
        "--quality-policy",
        help="Override path to devctl repo policy JSON",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("json", "md"),
        default_format="md",
    )


def add_render_surfaces_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `render-surfaces` parser."""
    render_cmd = sub.add_parser(
        "render-surfaces",
        help="Render repo-pack instruction and starter surfaces from policy",
    )
    render_cmd.add_argument(
        "--surface",
        action="append",
        default=[],
        help="Specific surface id to render/check (repeatable; default: all).",
    )
    render_cmd.add_argument(
        "--write",
        action="store_true",
        help="Write drifted generated surfaces to their output paths.",
    )
    render_cmd.add_argument(
        "--quality-policy",
        help=(
            "Optional repo policy JSON file to resolve "
            "(defaults to dev/config/devctl_repo_policy.json or "
            "DEVCTL_QUALITY_POLICY)."
        ),
    )
    add_standard_output_arguments(
        render_cmd,
        format_choices=("json", "md"),
        default_format="md",
    )
