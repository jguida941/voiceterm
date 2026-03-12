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
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

PROBE_SCRIPTS = [
    "probe_concurrency.py",
    "probe_design_smells.py",
    "probe_boolean_params.py",
    "probe_stringly_typed.py",
    "probe_unwrap_chains.py",
    "probe_clone_density.py",
    "probe_type_conversions.py",
    "probe_magic_numbers.py",
    "probe_dict_as_struct.py",
    "probe_unnecessary_intermediates.py",
    "probe_vague_errors.py",
    "probe_defensive_overchecking.py",
    "probe_single_use_helpers.py",
    "probe_exception_quality.py",
]


def _run_probe(script: str, since_ref: str | None, head_ref: str) -> dict | None:
    """Run one probe and return its JSON output."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "dev" / "scripts" / "checks" / script),
        "--format",
        "json",
    ]
    if since_ref:
        cmd.extend(["--since-ref", since_ref, "--head-ref", head_ref])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Warning: {script} failed: {exc}", file=sys.stderr)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all review probes and produce a combined report")
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument("--head-ref", default="HEAD", help="Head ref (default: HEAD)")
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

    # Run all probes.
    reports: list[dict] = []
    for script in PROBE_SCRIPTS:
        report = _run_probe(script, args.since_ref, args.head_ref)
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
