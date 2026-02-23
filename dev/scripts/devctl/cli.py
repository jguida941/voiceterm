"""devctl CLI argument parsing and dispatch."""

from __future__ import annotations

import argparse
import sys

from .cihub_setup_parser import add_cihub_setup_parser
from .cli_parser_builders import add_standard_parsers
from .commands import (
    audit_scaffold,
    cihub_setup,
    check,
    docs_check,
    failure_cleanup,
    homebrew,
    hygiene,
    listing,
    mutation_score,
    mutants,
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
)
from .config import (
    DEFAULT_CI_LIMIT,
    DEFAULT_MEM_ITERATIONS,
    DEFAULT_MUTANTS_TIMEOUT,
    DEFAULT_MUTATION_THRESHOLD,
)
from .failure_cleanup_parser import add_failure_cleanup_parser
from .orchestrate_parser import add_orchestrate_parsers
from .path_audit_parser import add_path_audit_parser, add_path_rewrite_parser
from .security_parser import add_security_parser
from .sync_parser import add_sync_parser
from .triage_parser import add_triage_parser


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
    add_failure_cleanup_parser(sub, default_ci_limit=DEFAULT_CI_LIMIT)
    add_sync_parser(sub)
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
    "list": listing.run,
    "path-audit": path_audit.run,
    "path-rewrite": path_rewrite.run,
    "cihub-setup": cihub_setup.run,
    "hygiene": hygiene.run,
    "sync": sync.run,
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
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
