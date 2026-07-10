"""CLI construction helpers for the mutation Ralph workflow bridge."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

SYSTEM_TMPDIR = Path(tempfile.gettempdir())


def _tmp_path(filename: str) -> str:
    return str(SYSTEM_TMPDIR / filename)


def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    subcommands = parser.add_subparsers(dest="command", required=True)

    resolve = subcommands.add_parser(
        "resolve-config",
        help="Resolve and validate workflow config, then append outputs.",
    )
    resolve.add_argument("--github-output", required=True)
    resolve.add_argument(
        "--event-name",
        default="",
        help="Optional explicit event name override (defaults to EVENT_NAME env var).",
    )

    extract = subcommands.add_parser(
        "extract-failure-reason",
        help="Print the stripped `reason` field from a loop JSON payload.",
    )
    extract.add_argument("--input", required=True)

    run_loop = subcommands.add_parser(
        "run-loop",
        help="Execute the mutation loop command with workflow soft-fail policy.",
    )
    run_loop.add_argument("--target-repo", required=True)
    run_loop.add_argument("--target-branch", required=True)
    run_loop.add_argument("--max-attempts", required=True)
    run_loop.add_argument("--poll-seconds", required=True)
    run_loop.add_argument("--timeout-seconds", required=True)
    run_loop.add_argument("--mode", required=True)
    run_loop.add_argument("--threshold", required=True)
    run_loop.add_argument("--notify-mode", required=True)
    run_loop.add_argument("--comment-target", required=True)
    run_loop.add_argument("--comment-pr-number", default="")
    run_loop.add_argument("--fix-command", default="")
    run_loop.add_argument("--json-output", default=_tmp_path("mutation-ralph-loop.json"))
    run_loop.add_argument("--output", default=_tmp_path("mutation-ralph-loop.md"))

    return parser
