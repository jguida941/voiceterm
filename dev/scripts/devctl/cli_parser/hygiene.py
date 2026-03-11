"""Parser registration helpers for process-hygiene commands.

Extracted from cli_parser_reporting.py to keep that module under the
code-shape soft limit. Covers the process-audit/process-cleanup/process-watch
subcommands that inspect/clean/watch repo-related host process trees.
"""

from __future__ import annotations

import argparse

from ..common import add_standard_output_arguments


def add_process_hygiene_parsers(sub: argparse._SubParsersAction) -> None:
    """Register process-audit/process-cleanup/process-watch/guard-run parsers."""
    # process-audit
    process_audit_cmd = sub.add_parser(
        "process-audit",
        help="Audit host repo-related runtime/tooling process trees",
    )
    process_audit_cmd.add_argument(
        "--strict",
        action="store_true",
        help="Fail when blocking repo-related host processes are still running",
    )
    add_standard_output_arguments(process_audit_cmd)

    # process-cleanup
    process_cleanup_cmd = sub.add_parser(
        "process-cleanup",
        help="Clean orphaned/stale host repo-related process trees and optionally verify",
    )
    process_cleanup_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Report cleanup targets without killing any processes",
    )
    process_cleanup_cmd.add_argument(
        "--verify",
        action="store_true",
        help="Re-run strict host audit after cleanup and fail if anything remains",
    )
    add_standard_output_arguments(process_cleanup_cmd)

    # process-watch
    process_watch_cmd = sub.add_parser(
        "process-watch",
        help="Periodically audit host repo-related process trees and optionally clean leaks",
    )
    process_watch_cmd.add_argument(
        "--cleanup",
        action="store_true",
        help="Run orphan/stale cleanup before each audit iteration",
    )
    process_watch_cmd.add_argument(
        "--strict",
        action="store_true",
        help="Use strict audit semantics for each iteration",
    )
    process_watch_cmd.add_argument(
        "--iterations",
        type=int,
        default=4,
        help="Maximum audit iterations to run",
    )
    process_watch_cmd.add_argument(
        "--interval-seconds",
        type=float,
        default=15.0,
        help="Delay between iterations",
    )
    process_watch_cmd.add_argument(
        "--stop-on-clean",
        action="store_true",
        help="Stop early once the watched host process state is clean",
    )
    add_standard_output_arguments(process_watch_cmd)

    # guard-run
    guard_run_cmd = sub.add_parser(
        "guard-run",
        help="Run one local command and always follow with repo process hygiene",
    )
    guard_run_cmd.add_argument(
        "--cwd",
        help="Working directory for the guarded command (default: repo root)",
    )
    guard_run_cmd.add_argument(
        "--post-action",
        choices=["auto", "quick", "cleanup", "none"],
        default="auto",
        help="Post-run hygiene follow-up mode",
    )
    guard_run_cmd.add_argument(
        "--label",
        help="Optional report label for the guarded command step",
    )
    guard_run_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the guarded command and follow-up without executing them",
    )
    guard_run_cmd.add_argument(
        "--provider",
        choices=["unknown", "codex", "claude", "shared"],
        help="Optional watchdog provider tag for the emitted episode artifact",
    )
    guard_run_cmd.add_argument(
        "--session-id",
        help="Optional watchdog session id for the emitted episode artifact",
    )
    guard_run_cmd.add_argument(
        "--peer-session-id",
        help="Optional peer session id for shared-loop watchdog artifacts",
    )
    guard_run_cmd.add_argument(
        "--trigger-reason",
        help="Optional typed trigger reason for the emitted watchdog episode",
    )
    guard_run_cmd.add_argument(
        "--retry-count",
        type=int,
        default=0,
        help="Optional retry count metadata for the emitted watchdog episode",
    )
    guard_run_cmd.add_argument(
        "--escaped-findings-count",
        type=int,
        default=0,
        help="Optional escaped-review findings count for the emitted watchdog episode",
    )
    guard_run_cmd.add_argument(
        "--guard-result",
        choices=["pass", "fail", "skipped", "noisy"],
        help="Optional explicit watchdog guard result override",
    )
    guard_run_cmd.add_argument(
        "--reviewer-verdict",
        choices=["accepted", "accepted_with_followups", "rejected", "deferred"],
        help="Optional explicit reviewer verdict override for the emitted watchdog episode",
    )
    add_standard_output_arguments(guard_run_cmd)
    guard_run_cmd.add_argument(
        "guarded_command",
        nargs=argparse.REMAINDER,
        help="Command to execute; pass it after `--` to avoid parser ambiguity",
    )
