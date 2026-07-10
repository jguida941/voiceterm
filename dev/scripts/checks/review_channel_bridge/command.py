#!/usr/bin/env python3
"""Validate the temporary markdown review-channel bridge contract."""

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

    from dev.scripts.devctl.runtime.validation_scope import (
        add_validation_scope_argument,
        apply_validation_scope_to_report,
        validation_scope_from_args,
    )
    from review_channel_bridge.report import build_report, render_md

    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    add_validation_scope_argument(parser)
    args = parser.parse_args()

    try:
        report = build_report()
    except (ImportError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return emit_runtime_error("check_review_channel_bridge", args.format, str(exc))
    report = apply_validation_scope_to_report(
        report,
        validation_scope_from_args(args),
        reason=(
            "review-channel bridge validation reads live compatibility and "
            "session projection state; governed publication validation records "
            "it as advisory evidence."
        ),
    )

    output = json.dumps(report, indent=2) if args.format == "json" else render_md(report)
    print(output)
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
