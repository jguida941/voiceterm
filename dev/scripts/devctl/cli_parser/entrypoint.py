"""Concrete devctl CLI entrypoint implementation."""

from __future__ import annotations

import argparse
import os
import sys
import time

from ..agent_mind_parser import add_agent_mind_parser
from ..audit_events import emit_devctl_audit_event
from ..autonomy.benchmark_parser import add_autonomy_benchmark_parser
from ..autonomy.loop_parser import add_autonomy_loop_parser
from ..autonomy.run_parser import add_autonomy_run_parser
from ..cihub_setup_parser import add_cihub_setup_parser
from ..commands import (
    agent_mind,
    audit_scaffold,
    auto_mode_status,
    autonomy_benchmark,
    autonomy_loop,
    autonomy_report,
    autonomy_run,
    autonomy_swarm,
    check,
    check_router,
    cihub_setup,
    compat_matrix,
    controller_action,
    dashboard,
    data_science,
    discover,
    docs_check,
    failure_cleanup,
    guard_run,
    homebrew,
    integrations_import,
    integrations_sync,
    listing,
    loop_packet,
    mcp,
    monitor,
    mobile_app,
    mobile_status,
    mutants,
    mutation_loop,
    mutation_score,
    orchestrate_status,
    pipeline as pipeline_command,
    platform_contracts,
    path_audit,
    path_rewrite,
    phone_status,
    probe_report,
    process_audit,
    process_cleanup,
    process_watch,
    publication_sync,
    pypi,
    quality_policy,
    ralph_status,
    release,
    release_gates,
    release_notes,
    report,
    reports_cleanup,
    review_channel,
    rollout_tail,
    security,
    ship,
    status,
    system_map,
    system_picture,
    sync,
    triage,
    triage_loop,
    view,
)
from ..commands.governance import (
    bootstrap as governance_bootstrap,
    doc_authority as governance_doc_authority,
    draft as governance_draft,
    export as governance_export,
    hygiene as governance_hygiene,
    import_findings as governance_import_findings,
    install_git_hooks as governance_install_git_hooks,
    orphan_inventory as governance_orphan_inventory,
    orchestrate_watch as governance_orchestrate_watch,
    quality_feedback as governance_quality_feedback,
    render_surfaces,
    review as governance_review,
    review_snapshot as governance_review_snapshot,
    session as governance_session,
    session_resume as governance_session_resume,
    simple_lanes,
    startup_context as governance_startup_context,
)
from ..commands.reporting import claude_loop, dogfood, findings_priority
from ..commands.vcs import commit as vcs_commit, push
from ..config import (
    DEFAULT_CI_LIMIT,
    DEFAULT_MEM_ITERATIONS,
    DEFAULT_MUTANTS_TIMEOUT,
    DEFAULT_MUTATION_THRESHOLD,
)
from ..context_graph.command import run as context_graph_run
from ..context_graph.graph_walk_command import run as graph_walk_run
from ..context_graph.parser import add_context_graph_parser, add_graph_walk_parser
from ..controller_action_parser import add_controller_action_parser
from .claude_loop import add_claude_loop_parser
from ..data_science.metrics import maybe_auto_refresh_data_science
from ..failure_cleanup_parser import add_failure_cleanup_parser
from ..governance.parser import (
    add_doc_authority_parser,
    add_governance_draft_parser,
    add_governance_import_findings_parser,
    add_governance_quality_feedback_parser,
    add_launcher_check_parser,
    add_launcher_policy_parser,
    add_launcher_probes_parser,
    add_render_surfaces_parser,
    add_tandem_validate_parser,
)
from ..integrations.import_parser import add_integrations_import_parser
from ..integrations.sync_parser import add_integrations_sync_parser
from ..loops.packet_parser import add_loop_packet_parser
from ..mobile.app_parser import add_mobile_app_parser
from ..mutation_loop.parser import add_mutation_loop_parser
from ..orchestrate_parser import add_orchestrate_parsers
from ..path_audit_parser import add_path_audit_parser, add_path_rewrite_parser
from ..pipeline_parser import add_pipeline_parser
from ..platform.parser import (
    add_platform_contracts_parser,
    add_system_map_parser,
    add_system_picture_parser,
)
from ..publication_sync.parser import add_publication_sync_parser
from ..reports_cleanup_parser import add_reports_cleanup_parser
from ..review_channel.parser import add_review_channel_parser
from ..rollout_tail_parser import add_rollout_tail_parser
from ..runtime.machine_output import clear_machine_output_metrics, consume_machine_output_metrics
from ..runtime.platform_finding_ingest import maybe_auto_ingest_devctl_result
from ..runtime.startup_gate import enforce_startup_gate
from ..security.parser import add_security_parser
from ..sync_parser import add_commit_parser, add_push_parser, add_sync_parser
from ..triage.loop_parser import add_triage_loop_parser
from ..triage.parser import add_findings_priority_parser, add_triage_parser
from .builders import add_standard_parsers

# Commands that run as status/reporting surfaces from the caller's point of
# view. They skip audit event writes and telemetry refresh so devctl works on
# read-only mounts, containers, and MCP adapters without triggering incidental
# filesystem writes. A few commands still have explicit managed artifact sinks.
READ_ONLY_COMMANDS: frozenset[str] = frozenset({
    "auto-mode",
    "startup-context",
    "session",
    "session-resume",
    "context-graph",
    "review-channel",
    "quality-policy",
    "orphan-inventory",
    "platform-contracts",
    "system-map",
    "mcp",
    "dashboard",
    "claude-loop",
    "discover",
    "findings-priority",
    "graph-walk",
    "view",
    "list",
    "rollout-tail",
})

# Environment variable checked by command handlers and artifact writers to
# suppress incidental filesystem writes (receipts, snapshots) that would
# otherwise make "read-only" commands fail on read-only mounts.  Set
# automatically for READ_ONLY_COMMANDS; can also be set externally by MCP
# adapters or container orchestration.
ARTIFACT_WRITES_ENV = "DEVCTL_NO_ARTIFACT_WRITES"


def artifact_writes_suppressed() -> bool:
    """True when incidental artifact writes should be skipped."""
    return os.environ.get(ARTIFACT_WRITES_ENV, "") == "1"


def _read_only_command_suppresses_artifact_writes(args) -> bool:
    """Return whether the dispatcher should set artifact-write suppression."""
    if args.command not in READ_ONLY_COMMANDS:
        return False
    if args.command == "context-graph" and getattr(args, "mode", "") == "bootstrap":
        return False
    return True


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argparse parser for devctl."""
    parser = argparse.ArgumentParser(description="VoiceTerm Dev CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    add_standard_parsers(
        sub,
        default_ci_limit=DEFAULT_CI_LIMIT,
        default_mem_iterations=DEFAULT_MEM_ITERATIONS,
        default_mutants_timeout=DEFAULT_MUTANTS_TIMEOUT,
        default_mutation_threshold=DEFAULT_MUTATION_THRESHOLD,
    )
    add_governance_import_findings_parser(sub)
    add_governance_draft_parser(sub)
    add_doc_authority_parser(sub)
    add_governance_quality_feedback_parser(sub)
    add_orchestrate_parsers(sub)
    add_publication_sync_parser(sub)
    add_platform_contracts_parser(sub)
    add_system_map_parser(sub)
    add_system_picture_parser(sub)
    add_render_surfaces_parser(sub)
    add_launcher_check_parser(sub)
    add_launcher_probes_parser(sub)
    add_launcher_policy_parser(sub)
    add_tandem_validate_parser(sub)
    add_review_channel_parser(sub)
    add_pipeline_parser(sub)
    add_rollout_tail_parser(sub)
    add_agent_mind_parser(sub)
    add_path_audit_parser(sub)
    add_path_rewrite_parser(sub)
    add_cihub_setup_parser(sub)
    add_security_parser(sub)
    add_controller_action_parser(sub)
    add_mobile_app_parser(sub)
    add_findings_priority_parser(sub)
    add_triage_parser(sub, default_ci_limit=DEFAULT_CI_LIMIT)
    add_triage_loop_parser(sub)
    add_loop_packet_parser(sub)
    add_autonomy_loop_parser(sub)
    add_autonomy_benchmark_parser(sub)
    add_autonomy_run_parser(sub)
    add_mutation_loop_parser(sub)
    add_failure_cleanup_parser(sub, default_ci_limit=DEFAULT_CI_LIMIT)
    add_reports_cleanup_parser(sub)
    add_commit_parser(sub)
    add_push_parser(sub)
    add_sync_parser(sub)
    add_integrations_sync_parser(sub)
    add_integrations_import_parser(sub)
    add_context_graph_parser(sub)
    add_graph_walk_parser(sub)
    governance_startup_context.add_parser(sub)
    governance_session.add_parser(sub)
    governance_session_resume.add_parser(sub)
    governance_review_snapshot.add_parser(sub)
    governance_orphan_inventory.add_parser(sub)
    governance_install_git_hooks.add_parser(sub)
    _add_dashboard_parser(sub)
    add_claude_loop_parser(sub)
    dogfood.add_parser(sub)
    monitor.add_parser(sub)
    auto_mode_status.add_parser(sub)
    discover.add_parser(sub)
    view.add_parser(sub)
    return parser


def _add_dashboard_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``dashboard`` subcommand."""
    from ..common import add_standard_output_arguments

    dash = sub.add_parser(
        "dashboard",
        help="Governance dashboard snapshot from existing artifacts",
    )
    add_standard_output_arguments(
        dash,
        format_choices=("terminal", "md", "json", "simple"),
        default_format="terminal",
    )
    dash.add_argument(
        "--view",
        choices=["overview", "dev", "analytics", "quality", "audit", "publication", "health"],
        default="overview",
        help="Dashboard view: overview (all), dev, analytics, quality, audit, publication, health",
    )
    dash.add_argument(
        "--role",
        choices=("dashboard", "observer"),
        default="dashboard",
        help="Caller role for advisory next-command filtering.",
    )
    dash.add_argument(
        "--follow",
        action="store_true",
        default=False,
        help="Poll and re-render dashboard snapshots until interrupted.",
    )
    dash.add_argument(
        "--interval",
        default="5",
        help="Polling interval for --follow, for example 1, 500ms, or 5s.",
    )
    dash.add_argument(
        "--max-follow-snapshots",
        type=int,
        default=None,
        help="Stop --follow after this many snapshots; useful for probes.",
    )
    dash.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Strip ANSI color codes from terminal output (also honors NO_COLOR env var)",
    )


COMMAND_HANDLERS = {
    "auto-mode": auto_mode_status.run,
    "check": check.run,
    "check-router": check_router.run,
    "claude-loop": claude_loop.run,
    "dashboard": dashboard.run,
    "dogfood": dogfood.run,
    "monitor": monitor.run,
    "mutants": mutants.run,
    "mutation-score": mutation_score.run,
    "docs-check": docs_check.run,
    "release": release.run,
    "release-gates": release_gates.run,
    "ship": ship.run,
    "release-notes": release_notes.run,
    "review-channel": review_channel.run,
    "pipeline": pipeline_command.run,
    "rollout-tail": rollout_tail.run,
    "agent-mind": agent_mind.run,
    "homebrew": homebrew.run,
    "pypi": pypi.run,
    "status": status.run,
    "orchestrate-status": orchestrate_status.run,
    "orchestrate-watch": governance_orchestrate_watch.run,
    "platform-contracts": platform_contracts.run,
    "system-map": system_map.run,
    "orphan-inventory": governance_orphan_inventory.run,
    "system-picture": system_picture.run,
    "report": report.run,
    "findings-priority": findings_priority.run,
    "triage": triage.run,
    "data-science": data_science.run,
    "probe-report": probe_report.run,
    "quality-policy": quality_policy.run,
    "launcher-check": simple_lanes.run_launcher_check,
    "launcher-probes": simple_lanes.run_launcher_probes,
    "launcher-policy": simple_lanes.run_launcher_policy,
    "tandem-validate": simple_lanes.run_tandem_validate,
    "render-surfaces": render_surfaces.run,
    "governance-export": governance_export.run,
    "governance-bootstrap": governance_bootstrap.run,
    "doc-authority": governance_doc_authority.run,
    "governance-draft": governance_draft.run,
    "governance-import-findings": governance_import_findings.run,
    "governance-quality-feedback": governance_quality_feedback.run,
    "governance-review": governance_review.run,
    "triage-loop": triage_loop.run,
    "loop-packet": loop_packet.run,
    "autonomy-loop": autonomy_loop.run,
    "autonomy-benchmark": autonomy_benchmark.run,
    "swarm_run": autonomy_run.run,
    "autonomy-report": autonomy_report.run,
    "phone-status": phone_status.run,
    "commit": vcs_commit.run,
    "push": push.run,
    "mobile-app": mobile_app.run,
    "mobile-status": mobile_status.run,
    "process-audit": process_audit.run,
    "process-cleanup": process_cleanup.run,
    "process-watch": process_watch.run,
    "guard-run": guard_run.run,
    "autonomy-swarm": autonomy_swarm.run,
    "mutation-loop": mutation_loop.run,
    "list": listing.run,
    "compat-matrix": compat_matrix.run,
    "mcp": mcp.run,
    "path-audit": path_audit.run,
    "path-rewrite": path_rewrite.run,
    "publication-sync": publication_sync.run,
    "ralph-status": ralph_status.run,
    "cihub-setup": cihub_setup.run,
    "controller-action": controller_action.run,
    "hygiene": governance_hygiene.run,
    "sync": sync.run,
    "integrations-sync": integrations_sync.run,
    "integrations-import": integrations_import.run,
    "security": security.run,
    "failure-cleanup": failure_cleanup.run,
    "reports-cleanup": reports_cleanup.run,
    "audit-scaffold": audit_scaffold.run,
    "context-graph": context_graph_run,
    "graph-walk": graph_walk_run,
    "startup-context": governance_startup_context.run,
    "session": governance_session.run,
    "session-resume": governance_session_resume.run,
    "review-snapshot": governance_review_snapshot.run,
    "install-git-hooks": governance_install_git_hooks.run,
    "discover": discover.run,
    "view": view.run,
}


def main() -> int:
    """Entry point for devctl CLI."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "check":
        if args.ci:
            args.profile = "ci"
        if args.prepush:
            args.profile = "prepush"

    handler = COMMAND_HANDLERS.get(args.command)
    if handler is None:
        print(f"error: unknown command '{args.command}'", file=sys.stderr)
        return 1
    clear_machine_output_metrics()
    started = time.monotonic()
    return_code = 1
    is_read_only = args.command in READ_ONLY_COMMANDS
    suppress_artifact_writes = _read_only_command_suppresses_artifact_writes(args)
    previous_artifact_write_env = os.environ.get(ARTIFACT_WRITES_ENV)
    if suppress_artifact_writes:
        os.environ[ARTIFACT_WRITES_ENV] = "1"
    try:
        gate_failure = enforce_startup_gate(args)
        if gate_failure is not None:
            print(gate_failure, file=sys.stderr)
            return_code = 1
            return return_code
        return_code = handler(args)
        return return_code
    finally:
        if suppress_artifact_writes:
            if previous_artifact_write_env is None:
                os.environ.pop(ARTIFACT_WRITES_ENV, None)
            else:
                os.environ[ARTIFACT_WRITES_ENV] = previous_artifact_write_env
        duration_seconds = time.monotonic() - started
        if not is_read_only:
            emit_devctl_audit_event(
                command=args.command,
                args=args,
                returncode=return_code,
                duration_seconds=duration_seconds,
                argv=sys.argv[1:],
                machine_output=consume_machine_output_metrics(),
            )
            maybe_auto_ingest_devctl_result(
                command=args.command,
                returncode=return_code,
                argv=sys.argv[1:],
                read_only=is_read_only,
            )
        if not is_read_only and args.command != "data-science":
            maybe_auto_refresh_data_science(command=args.command)


__all__ = [
    "ARTIFACT_WRITES_ENV",
    "COMMAND_HANDLERS",
    "READ_ONLY_COMMANDS",
    "artifact_writes_suppressed",
    "build_parser",
    "main",
]
