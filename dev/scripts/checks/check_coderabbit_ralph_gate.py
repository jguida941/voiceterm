#!/usr/bin/env python3
"""Verify that CodeRabbit Ralph loop passed for a specific commit SHA."""

from __future__ import annotations

import argparse
import json
import sys

try:
    from dev.scripts.checks import check_coderabbit_gate as gate_core
    from dev.scripts.checks import coderabbit_gate_core as gate_rendering
except ModuleNotFoundError:
    import check_coderabbit_gate as gate_core
    import coderabbit_gate_core as gate_rendering

DEFAULT_WORKFLOW = "CodeRabbit Ralph Loop"


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
    parser.add_argument("--limit", type=int, default=gate_core.DEFAULT_LIMIT)
    parser.add_argument("--require-conclusion", default="success")
    parser.add_argument(
        "--wait-seconds", type=int, default=gate_core.DEFAULT_WAIT_SECONDS
    )
    parser.add_argument(
        "--poll-seconds", type=int, default=gate_core.DEFAULT_POLL_SECONDS
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def _normalize_report(report: dict) -> dict:
    payload = dict(report)
    payload["command"] = "check_coderabbit_ralph_gate"
    reason = str(payload.get("reason") or "")
    if reason == "coderabbit_gate_passed":
        payload["reason"] = "coderabbit_ralph_gate_passed"
    return payload


def _render_md(report: dict) -> str:
    return gate_rendering.render_report_md(
        report,
        title="check_coderabbit_ralph_gate",
    )


def main() -> int:
    args = _build_parser().parse_args()
    report = _normalize_report(gate_core._build_report(args))

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
