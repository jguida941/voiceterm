"""devctl CLI argument parsing and dispatch."""

from __future__ import annotations

import argparse
import sys
import time

from .cihub_setup_parser import add_cihub_setup_parser
from .cli_parser_builders import add_standard_parsers
from .commands import (
    autonomy_loop,
    audit_scaffold,
    check,
    cihub_setup,
    docs_check,
    failure_cleanup,
    homebrew,
    hygiene,
    integrations_import,
    integrations_sync,
    listing,
    loop_packet,
    mutants,
    mutation_loop,
    mutation_score,
    orchestrate_status,
    orchestrate_watch,
    path_audit,
    path_rewrite,
    pypi,
    release,
    release_notes,
    report,
    security,
    ship,
    status,
    sync,
    triage,
    triage_loop,
)
from .config import (
    DEFAULT_CI_LIMIT,
    DEFAULT_MEM_ITERATIONS,
    DEFAULT_MUTANTS_TIMEOUT,
    DEFAULT_MUTATION_THRESHOLD,
)
from .audit_events import emit_devctl_audit_event
from .failure_cleanup_parser import add_failure_cleanup_parser
from .orchestrate_parser import add_orchestrate_parsers
from .path_audit_parser import add_path_audit_parser, add_path_rewrite_parser
from .security_parser import add_security_parser
from .sync_parser import add_sync_parser
from .loop_packet_parser import add_loop_packet_parser
from .autonomy_loop_parser import add_autonomy_loop_parser
from .mutation_loop_parser import add_mutation_loop_parser
from .triage_loop_parser import add_triage_loop_parser
from .triage_parser import add_triage_parser
from .integrations_import_parser import add_integrations_import_parser
from .integrations_sync_parser import add_integrations_sync_parser


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
    add_orchestrate_parsers(sub)
    add_path_audit_parser(sub)
    add_path_rewrite_parser(sub)
    add_cihub_setup_parser(sub)
    add_security_parser(sub)
    add_triage_parser(sub, default_ci_limit=DEFAULT_CI_LIMIT)
    add_triage_loop_parser(sub)
    add_loop_packet_parser(sub)
    add_autonomy_loop_parser(sub)
    add_mutation_loop_parser(sub)
    add_failure_cleanup_parser(sub, default_ci_limit=DEFAULT_CI_LIMIT)
    add_sync_parser(sub)
    add_integrations_sync_parser(sub)
    add_integrations_import_parser(sub)
    return parser


COMMAND_HANDLERS = {
    "check": check.run,
    "mutants": mutants.run,
    "mutation-score": mutation_score.run,
    "docs-check": docs_check.run,
    "release": release.run,
    "ship": ship.run,
    "release-notes": release_notes.run,
    "homebrew": homebrew.run,
    "pypi": pypi.run,
    "status": status.run,
    "orchestrate-status": orchestrate_status.run,
    "orchestrate-watch": orchestrate_watch.run,
    "report": report.run,
    "triage": triage.run,
    "triage-loop": triage_loop.run,
    "loop-packet": loop_packet.run,
    "autonomy-loop": autonomy_loop.run,
    "mutation-loop": mutation_loop.run,
    "list": listing.run,
    "path-audit": path_audit.run,
    "path-rewrite": path_rewrite.run,
    "cihub-setup": cihub_setup.run,
    "hygiene": hygiene.run,
    "sync": sync.run,
    "integrations-sync": integrations_sync.run,
    "integrations-import": integrations_import.run,
    "security": security.run,
    "failure-cleanup": failure_cleanup.run,
    "audit-scaffold": audit_scaffold.run,
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
    started = time.monotonic()
    return_code = 1
    try:
        return_code = handler(args)
        return return_code
    finally:
        duration_seconds = time.monotonic() - started
        emit_devctl_audit_event(
            command=args.command,
            args=args,
            returncode=return_code,
            duration_seconds=duration_seconds,
            argv=sys.argv[1:],
        )


if __name__ == "__main__":
    sys.exit(main())
