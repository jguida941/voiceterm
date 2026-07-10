#!/usr/bin/env python3
"""Detect orphaned, duplicate, and stranded contract dataclasses."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    checks_dir = Path(__file__).resolve().parent.parent
    if str(checks_dir) not in sys.path:
        sys.path.insert(0, str(checks_dir))

    from check_bootstrap import REPO_ROOT, emit_runtime_error

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    from contract_connectivity.report import build_report, render_md

    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument(
        "--absolute",
        action="store_true",
        help="Scan the current worktree without baseline suppression.",
    )
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument(
        "--head-ref", default="HEAD", help="Head ref used with --since-ref"
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()

    try:
        report = build_report(
            repo_root=REPO_ROOT,
            absolute=bool(args.absolute),
            since_ref=args.since_ref,
            head_ref=args.head_ref,
        )
    except (ImportError, RuntimeError, TypeError, ValueError) as exc:
        return emit_runtime_error(
            "check_contract_connectivity",
            args.format,
            str(exc),
        )

    output = (
        json.dumps(report.to_dict(), indent=2)
        if args.format == "json"
        else render_md(report)
    )
    print(output)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
