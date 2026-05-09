#!/usr/bin/env python3
"""Package-owned entrypoint for the multi-agent sync guard."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if __package__:
    from .report import build_report, render_md
else:  # pragma: no cover - standalone package fallback
    from report import build_report, render_md

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.runtime.validation_scope import (
    add_validation_scope_argument,
    apply_validation_scope_to_report,
    validation_scope_from_args,
)

MASTER_PLAN_PATH = REPO_ROOT / "dev/active/MASTER_PLAN.md"
RUNBOOK_PATH = REPO_ROOT / "dev/active/review_channel.md"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    add_validation_scope_argument(parser)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = build_report(
        repo_root=REPO_ROOT,
        master_plan_path=MASTER_PLAN_PATH,
        runbook_path=RUNBOOK_PATH,
    )
    report = apply_validation_scope_to_report(
        report,
        validation_scope_from_args(args),
        reason=(
            "multi-agent sync reads live coordination projections; governed "
            "publication validation records it as advisory evidence."
        ),
    )
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_md(report))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())
