"""devctl session: standardized entry point for AI agent sessions.

Replaces ad-hoc prompts with governed, portable session bootstraps.
Each role (reviewer, implementer, dashboard) gets a consistent
startup sequence through the typed review-channel system.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ...config import get_repo_root
from ...common import add_standard_output_arguments


def add_parser(subparsers) -> None:
    """Register the session CLI parser."""
    cmd = subparsers.add_parser(
        "session",
        help="Start a governed AI agent session with role-specific bootstrap.",
    )
    cmd.add_argument(
        "--role",
        choices=("reviewer", "implementer", "dashboard"),
        required=True,
        help="Agent role for this session.",
    )
    cmd.add_argument(
        "--loop",
        action="store_true",
        default=False,
        help="Reviewer-only: continuous polling loop that relaunches on exit.",
    )
    cmd.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Seconds between polling cycles in --loop mode (default: 30).",
    )
    cmd.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Skip TTY requirement. Use when running without a terminal.",
    )
    add_standard_output_arguments(cmd)


def run(args) -> int:
    """Dispatch to the role-specific session handler."""
    role = args.role
    repo_root = get_repo_root()
    if role == "reviewer":
        return _run_reviewer(args, repo_root)
    if role == "implementer":
        return _run_implementer(args, repo_root)
    if role == "dashboard":
        return _run_dashboard(args, repo_root)
    return 1


def _run_reviewer(args, repo_root: Path) -> int:
    """Start a reviewer session, optionally in continuous loop mode."""
    if args.loop:
        from .session_reviewer_loop import run_reviewer_loop
        return run_reviewer_loop(
            repo_root=repo_root,
            interval=args.interval,
            headless=args.headless,
        )
    # One-shot: print bootstrap and exit
    return _emit_bootstrap(args, repo_root, role="reviewer")


def _run_implementer(args, repo_root: Path) -> int:
    """Start an implementer session with typed bootstrap."""
    return _emit_bootstrap(args, repo_root, role="implementer")


def _run_dashboard(args, repo_root: Path) -> int:
    """Start a dashboard session (read-only monitoring)."""
    return _emit_bootstrap(args, repo_root, role="dashboard")


def _emit_bootstrap(args, repo_root: Path, *, role: str) -> int:
    """Run session-resume for the role and emit the bootstrap packet."""
    result = subprocess.run(
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "session-resume",
            "--role", role,
            "--format", "bootstrap",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    report = {
        "command": "session",
        "role": role,
        "loop": getattr(args, "loop", False),
        "bootstrap_exit_code": result.returncode,
        "bootstrap": result.stdout.strip()[:2000] if result.stdout else "",
    }
    if result.returncode != 0:
        report["errors"] = [result.stderr.strip()[:500]] if result.stderr else []
    fmt = getattr(args, "format", "json")
    if fmt == "json":
        print(json.dumps(report, indent=2))
    else:
        print(report.get("bootstrap", ""))
    return result.returncode
