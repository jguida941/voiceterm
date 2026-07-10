#!/usr/bin/env python3
"""Enforce portable platform-contract sync for lifecycle and authority surfaces."""

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

    from platform_contract_sync.report import build_report, render_md

    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()

    try:
        report = build_report()
    except (ImportError, AttributeError, RuntimeError, ValueError) as exc:
        return emit_runtime_error("check_platform_contract_sync", args.format, str(exc))

    output = json.dumps(report, indent=2) if args.format == "json" else render_md(report)
    print(output)
    return 0 if report.get("ok", False) else 1
