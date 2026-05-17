#!/usr/bin/env python3
"""Enforce closure ownership for SYSTEM_MAP.md runtime-spine gaps."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    checks_dir = Path(__file__).resolve().parent.parent
    if str(checks_dir) not in sys.path:
        sys.path.insert(0, str(checks_dir))

    from check_bootstrap import REPO_ROOT, emit_runtime_error

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    from runtime_spine_closure.report import build_report, render_md

    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        report = build_report()
    except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
        return emit_runtime_error("check_runtime_spine_closure", args.format, str(exc))

    output = json.dumps(report, indent=2) if args.format == "json" else render_md(report)
    print(output)
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())

