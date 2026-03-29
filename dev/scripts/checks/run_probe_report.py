#!/usr/bin/env python3
"""Run all review probes and produce a combined quality report.

Usage:
    python3 dev/scripts/checks/run_probe_report.py                  # markdown
    python3 dev/scripts/checks/run_probe_report.py --format terminal # compact
    python3 dev/scripts/checks/run_probe_report.py --format json     # raw data
    python3 dev/scripts/checks/run_probe_report.py --since-ref HEAD~5 # commit range
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, import_repo_module
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, import_repo_module

_quality_policy = import_repo_module("dev.scripts.devctl.quality_policy", repo_root=REPO_ROOT)
_quality_policy_loader = import_repo_module(
    "dev.scripts.devctl.quality_policy_loader",
    repo_root=REPO_ROOT,
)
_script_catalog = import_repo_module("dev.scripts.devctl.script_catalog", repo_root=REPO_ROOT)

QUALITY_POLICY_ENV_VAR = _quality_policy_loader.QUALITY_POLICY_ENV_VAR
resolve_review_probe_script_ids = _quality_policy.resolve_review_probe_script_ids
probe_script_cmd = _script_catalog.probe_script_cmd

def _run_probe(
    probe_id: str,
    *,
    since_ref: str | None,
    head_ref: str,
    policy_path: str | None,
) -> dict | None:
    """Run one probe and return its JSON output."""
    cmd = [sys.executable, *probe_script_cmd(probe_id, "--format", "json")[1:]]
    if since_ref:
        cmd.extend(["--since-ref", since_ref, "--head-ref", head_ref])
    env = os.environ.copy()
    if policy_path:
        env[QUALITY_POLICY_ENV_VAR] = str(Path(policy_path).expanduser())

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
            check=False,
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Warning: {probe_id} failed: {exc}", file=sys.stderr)
    return None

def main() -> int:
    parser = argparse.ArgumentParser(description="Run all review probes and produce a combined report")
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument("--head-ref", default="HEAD", help="Head ref (default: HEAD)")
    parser.add_argument(
        "--quality-policy",
        help="Override the resolved repo quality policy for probe selection/config",
    )
    parser.add_argument(
        "--format",
        choices=("md", "terminal", "json"),
        default="md",
        help="Output format (default: md)",
    )
    parser.add_argument(
        "--output",
        help="Write report to file instead of stdout",
    )
    parser.add_argument(
        "--no-source",
        action="store_true",
        help="Omit source code snippets from report",
    )
    parser.add_argument(
        "--no-diffs",
        action="store_true",
        help="Omit git diff context from report",
    )
    args = parser.parse_args()

    probe_ids = resolve_review_probe_script_ids(policy_path=args.quality_policy)
    reports: list[dict] = []
    for probe_id in probe_ids:
        report = _run_probe(
            probe_id,
            since_ref=args.since_ref,
            head_ref=args.head_ref,
            policy_path=args.quality_policy,
        )
        if report:
            reports.append(report)

    if args.format == "json":
        output = json.dumps(reports, indent=2)
    else:
        # Import renderer (same directory).
        sys.path.insert(0, str(Path(__file__).parent))
        from probe_report_render import render_rich_report, render_terminal_report

        if args.format == "terminal":
            output = render_terminal_report(reports, repo_root=REPO_ROOT)
        else:
            output = render_rich_report(
                reports,
                repo_root=REPO_ROOT,
                show_source=not args.no_source,
                show_diffs=not args.no_diffs,
            )

    if args.output:
        Path(args.output).write_text(output + "\n")
        print(f"Report written to {args.output}")
    else:
        print(output)

    return 0

if __name__ == "__main__":
    sys.exit(main())
