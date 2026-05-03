"""Bounded Python test command implementation."""

from __future__ import annotations

import json
import os

from ...common import run_cmd, write_output
from ...config import REPO_ROOT
from ...runtime.python_test_contract import build_python_test_command
from ...time_utils import utc_timestamp


def run(args) -> int:
    resolved = build_python_test_command(
        suite_id=args.suite,
        explicit_targets=tuple(args.path or ()),
        timeout_seconds=args.timeout_seconds,
        per_test_timeout_seconds=args.per_test_timeout_seconds,
        fail_fast=not args.no_fail_fast,
    )
    env = dict(os.environ)
    env["VOICETERM_DEVCTL_LIVE_OUTPUT_TIMEOUT_SECONDS"] = str(
        max(1, resolved.timeout_seconds + 30)
    )
    result = run_cmd(
        "test-python",
        list(resolved.command),
        cwd=REPO_ROOT,
        env=env,
        dry_run=args.dry_run,
    )
    report = _build_report(resolved, result, dry_run=args.dry_run)
    output = json.dumps(report, indent=2) if args.format == "json" else _render_md(report)
    write_output(output, None)
    return 0 if report["ok"] else 1


def _build_report(resolved, result: dict, *, dry_run: bool) -> dict[str, object]:
    report: dict[str, object] = {}
    report["command"] = "test-python"
    report["timestamp"] = utc_timestamp()
    report["ok"] = result["returncode"] == 0
    report["suite"] = resolved.suite_id
    report["targets"] = list(resolved.targets)
    report["fail_fast"] = resolved.fail_fast
    report["timeout_seconds"] = resolved.timeout_seconds
    report["per_test_timeout_seconds"] = resolved.per_test_timeout_seconds
    report["pytest_command"] = list(resolved.command)
    report["dry_run"] = dry_run
    report["step"] = result
    return report


def _render_md(report: dict[str, object]) -> str:
    step = report["step"] if isinstance(report["step"], dict) else {}
    lines = [
        "# devctl test-python",
        "",
        f"- ok: {report['ok']}",
        f"- suite: {report['suite']}",
        f"- targets: {', '.join(report['targets'])}",
        f"- fail_fast: {report['fail_fast']}",
        f"- timeout_seconds: {report['timeout_seconds']}",
        f"- per_test_timeout_seconds: {report['per_test_timeout_seconds']}",
        f"- returncode: {step.get('returncode')}",
        f"- duration_s: {step.get('duration_s')}",
        "",
        "## Command",
        f"- `{' '.join(report['pytest_command'])}`",
    ]
    if step.get("failure_output"):
        lines.extend(["", "## Failure Output", str(step["failure_output"])])
    return "\n".join(lines)
