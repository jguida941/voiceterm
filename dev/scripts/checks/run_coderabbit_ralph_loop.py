#!/usr/bin/env python3
"""Run a bounded CodeRabbit remediation loop against medium+ backlog items."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

from coderabbit_ralph_loop_core import (
    DEFAULT_WORKFLOW,
    execute_loop,
    resolve_repo,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="owner/repo (default: $GITHUB_REPOSITORY)")
    parser.add_argument("--branch", required=True)
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--run-list-limit", type=int, default=30)
    parser.add_argument("--poll-seconds", type=int, default=20)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument(
        "--fix-command",
        help=(
            "Optional command executed per attempt when backlog is non-empty. "
            "Command is expected to apply fixes and push a new commit to the branch."
        ),
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument("--output", help="Primary output path")
    parser.add_argument("--json-output", help="Optional secondary JSON report path")
    return parser


def _render_markdown(report: dict) -> str:
    lines = ["# coderabbit_ralph_loop", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- repo: {report.get('repo')}")
    lines.append(f"- branch: {report.get('branch')}")
    lines.append(f"- workflow: {report.get('workflow')}")
    lines.append(f"- max_attempts: {report.get('max_attempts')}")
    lines.append(f"- completed_attempts: {report.get('completed_attempts')}")
    lines.append(f"- unresolved_count: {report.get('unresolved_count')}")
    lines.append(f"- reason: {report.get('reason')}")
    lines.append("")
    lines.append("## Attempts")
    lines.append("")
    attempts = report.get("attempts", [])
    if not attempts:
        lines.append("- none")
        return "\n".join(lines)
    for attempt in attempts:
        lines.append(
            "- "
            + f"#{attempt.get('attempt')} "
            + f"run_id={attempt.get('run_id')} "
            + f"sha={attempt.get('run_sha')} "
            + f"conclusion={attempt.get('run_conclusion')} "
            + f"backlog={attempt.get('backlog_count')} "
            + f"status={attempt.get('status')}"
        )
        if attempt.get("run_url"):
            lines.append(f"  url: {attempt.get('run_url')}")
        if attempt.get("message"):
            lines.append(f"  note: {attempt.get('message')}")
    return "\n".join(lines)


def _write_output(content: str, output: str | None) -> None:
    if not output:
        print(content)
        return
    path = Path(output).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"saved: {path}")


def main() -> int:
    args = _build_parser().parse_args()
    repo = resolve_repo(args.repo)
    if not repo:
        print("Error: unable to resolve repository (pass --repo or set GITHUB_REPOSITORY).")
        return 2
    if args.max_attempts < 1:
        print("Error: --max-attempts must be >= 1")
        return 2
    if not shutil.which("gh"):
        print("Error: gh CLI is required for ralph loop.")
        return 2

    report = execute_loop(
        repo=repo,
        branch=args.branch,
        workflow=args.workflow,
        max_attempts=args.max_attempts,
        run_list_limit=args.run_list_limit,
        poll_seconds=args.poll_seconds,
        timeout_seconds=args.timeout_seconds,
        fix_command=args.fix_command,
    )

    payload = json.dumps(report, indent=2)
    if args.format == "json":
        _write_output(payload, args.output)
    else:
        _write_output(_render_markdown(report), args.output)
    if args.json_output:
        _write_output(payload, args.json_output)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
