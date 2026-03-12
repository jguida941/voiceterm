"""Public entrypoint for rendered review-probe reports.

Usage:
    python3 dev/scripts/checks/probe_report_render.py --input probes.json
    python3 dev/scripts/checks/probe_report_render.py < probes.json

Programmatic imports should continue using this module:
    from probe_report_render import render_rich_report
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    from dev.scripts.checks.probe_report_support import aggregate_probe_results
    from dev.scripts.checks.probe_report_renderer_core import (
        render_rich_report,
        render_terminal_report,
    )
except ModuleNotFoundError:  # pragma: no cover
    from probe_report_support import aggregate_probe_results
    from probe_report_renderer_core import render_rich_report, render_terminal_report


def _load_reports(input_path: str | None) -> list[dict[str, Any]]:
    """Load one or more probe reports from stdin or a JSON file."""
    payload = Path(input_path).read_text() if input_path else sys.stdin.read()
    data = json.loads(payload)
    return data if isinstance(data, list) else [data]


def main() -> int:
    """CLI entry point — reads probe JSON from stdin or file."""
    import argparse as _argparse

    parser = _argparse.ArgumentParser(description="Render rich human-readable probe reports")
    parser.add_argument(
        "--input",
        help="JSON file with probe results (reads stdin if omitted)",
    )
    parser.add_argument(
        "--format",
        choices=("md", "terminal"),
        default="md",
        help="Output format (default: md)",
    )
    args = parser.parse_args()

    reports = _load_reports(args.input)
    if args.format == "terminal":
        print(render_terminal_report(reports))
    else:
        print(render_rich_report(reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
