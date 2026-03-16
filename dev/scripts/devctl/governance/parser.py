"""Parser registration for governance and simple policy-backed commands."""

from __future__ import annotations

import argparse

from ..common import add_standard_output_arguments


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


def add_launcher_check_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `launcher-check` parser."""
    launcher_check_cmd = sub.add_parser(
        "launcher-check",
        help="Run focused AI guards for launcher/package Python entrypoints",
    )
    launcher_check_cmd.add_argument(
        "--since-ref",
        help="Optional git base ref used to limit the guard scan",
    )
    launcher_check_cmd.add_argument(
        "--adoption-scan",
        action="store_true",
        help="Run against the current worktree instead of diff-scoped growth checks",
    )
    launcher_check_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref used with --since-ref (default: HEAD)",
    )
    launcher_check_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Render the delegated `check` plan without executing it",
    )
    launcher_check_cmd.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue through guard failures in the delegated `check` run",
    )
    launcher_check_cmd.add_argument(
        "--no-parallel",
        action="store_true",
        help="Run delegated AI guards sequentially instead of batched phases",
    )
    add_standard_output_arguments(
        launcher_check_cmd,
        format_choices=("text", "json", "md"),
        default_format="text",
    )


def add_launcher_probes_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `launcher-probes` parser."""
    launcher_probes_cmd = sub.add_parser(
        "launcher-probes",
        help="Run focused review probes for launcher/package Python entrypoints",
    )
    launcher_probes_cmd.add_argument(
        "--since-ref",
        help="Optional git base ref used to limit probe scanning",
    )
    launcher_probes_cmd.add_argument(
        "--adoption-scan",
        action="store_true",
        help="Run a full current-worktree onboarding scan",
    )
    launcher_probes_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref used with --since-ref (default: HEAD)",
    )
    launcher_probes_cmd.add_argument(
        "--output-root",
        default="dev/reports/probes",
        help="Root directory for aggregated probe artifacts",
    )
    launcher_probes_cmd.add_argument(
        "--emit-artifacts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write probe artifacts under --output-root",
    )
    add_standard_output_arguments(
        launcher_probes_cmd,
        format_choices=("json", "md", "terminal"),
        default_format="md",
    )
    launcher_probes_cmd.add_argument(
        "--json-output",
        help="Optional path for the JSON report when --format is not json",
    )


def add_launcher_policy_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `launcher-policy` parser."""
    launcher_policy_cmd = sub.add_parser(
        "launcher-policy",
        help="Show the focused launcher/package quality policy",
    )
    add_standard_output_arguments(
        launcher_policy_cmd,
        format_choices=("json", "md"),
        default_format="md",
    )


def add_tandem_validate_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `tandem-validate` parser."""
    tandem_validate_cmd = sub.add_parser(
        "tandem-validate",
        help=(
            "Run the canonical live tandem validation lane "
            "(policy resolution, router-derived bundle/risk add-ons, final bridge/tandem guards)"
        ),
    )
    tandem_validate_cmd.add_argument(
        "--since-ref",
        help="Optional git base ref used to route against a commit range instead of the current dirty tree",
    )
    tandem_validate_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref used with --since-ref (default: HEAD)",
    )
    tandem_validate_cmd.add_argument(
        "--quality-policy",
        help=(
            "Optional repo policy JSON file used for router resolution and "
            "policy-aware delegated devctl commands"
        ),
    )
    tandem_validate_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Render and audit the routed command plan without executing it",
    )
    tandem_validate_cmd.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue through delegated command failures instead of stopping at the first one",
    )
    add_standard_output_arguments(
        tandem_validate_cmd,
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
