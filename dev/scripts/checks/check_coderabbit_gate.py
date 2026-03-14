#!/usr/bin/env python3
"""Verify that CodeRabbit triage gate passed for a specific commit SHA."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
DEFAULT_WORKFLOW = "CodeRabbit Triage Bridge"
DEFAULT_LIMIT = 50
DEFAULT_WAIT_SECONDS = 0
DEFAULT_POLL_SECONDS = 15

try:
    from dev.scripts.checks.coderabbit_gate_core import build_report, render_report_md
    from dev.scripts.checks.coderabbit_gate_support import (
        is_ci_environment,
        local_workflow_exists_by_name,
        looks_like_connectivity_error,
    )
except ModuleNotFoundError:  # pragma: no cover - local fallback
    from coderabbit_gate_core import build_report, render_report_md
    from coderabbit_gate_support import (
        is_ci_environment,
        local_workflow_exists_by_name,
        looks_like_connectivity_error,
    )


def _run_capture(cmd: list[str]) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return 127, "", str(exc)
    return completed.returncode, completed.stdout or "", completed.stderr or ""


def _local_workflow_exists_by_name(workflow_name: str) -> bool:
    return local_workflow_exists_by_name(REPO_ROOT, workflow_name)


def _build_report(args) -> dict[str, Any]:
    return build_report(
        args,
        run_capture=_run_capture,
        local_workflow_exists_by_name=_local_workflow_exists_by_name,
        is_ci_environment=is_ci_environment,
        looks_like_connectivity_error=looks_like_connectivity_error,
        default_wait_seconds=DEFAULT_WAIT_SECONDS,
        default_poll_seconds=DEFAULT_POLL_SECONDS,
    )


def _render_md(report: dict) -> str:
    return render_report_md(report, title="check_coderabbit_gate")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW)
    parser.add_argument("--repo", help="owner/repo override for gh run list")
    parser.add_argument("--sha", help="Commit SHA to validate (default: HEAD)")
    parser.add_argument(
        "--branch",
        help="Optional branch hint for gh run list; commit filtering is always applied.",
    )
    parser.add_argument(
        "--allow-branch-fallback",
        action="store_true",
        help="Allow commit-only fallback when the requested branch has no matching workflow runs.",
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--require-conclusion", default="success")
    parser.add_argument("--wait-seconds", type=int, default=DEFAULT_WAIT_SECONDS)
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = _build_report(args)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
