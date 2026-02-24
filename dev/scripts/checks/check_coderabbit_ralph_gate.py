#!/usr/bin/env python3
"""Verify that CodeRabbit Ralph loop passed for a specific commit SHA."""

from __future__ import annotations

import argparse
import json
import sys

try:
    from dev.scripts.checks import check_coderabbit_gate as gate_core
except ModuleNotFoundError:
    import check_coderabbit_gate as gate_core

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
    parser.add_argument("--limit", type=int, default=gate_core.DEFAULT_LIMIT)
    parser.add_argument("--require-conclusion", default="success")
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
    lines = ["# check_coderabbit_ralph_gate", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- workflow: {report.get('workflow')}")
    if report.get("repo"):
        lines.append(f"- repo: {report.get('repo')}")
    lines.append(f"- branch_requested: {report.get('branch_requested') or '(none)'}")
    lines.append(f"- branch: {report.get('branch')}")
    lines.append(f"- fallback_without_branch: {report.get('fallback_without_branch')}")
    lines.append(f"- sha: {report.get('sha')}")
    lines.append(f"- checked_runs: {report.get('checked_runs')}")
    lines.append(f"- matching_runs: {report.get('matching_runs')}")
    lines.append(f"- reason: {report.get('reason')}")
    warnings = report.get("warnings")
    if isinstance(warnings, list):
        for warning in warnings:
            lines.append(f"- warning: {warning}")
    latest = report.get("latest_match")
    if isinstance(latest, dict) and latest:
        lines.append(
            "- latest_match: "
            + ", ".join(
                [
                    f"status={latest.get('status')}",
                    f"conclusion={latest.get('conclusion')}",
                    f"url={latest.get('url')}",
                    f"created_at={latest.get('created_at')}",
                ]
            )
        )
    return "\n".join(lines)


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
