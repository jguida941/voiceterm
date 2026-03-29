#!/usr/bin/env python3
"""Guard bundle registry DRY compliance: flag copy-paste command sharing."""

from __future__ import annotations

import argparse
import json

from .analysis import DEFAULT_MAX_WIDELY_SHARED_COMMANDS, build_report
from .rendering import render_markdown


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument(
        "--max-shared",
        "--max-widely-shared-commands",
        dest="max_widely_shared_commands",
        type=int,
        default=DEFAULT_MAX_WIDELY_SHARED_COMMANDS,
        help=(
            "Max widely shared commands allowed across more than two bundles "
            "before composition becomes mandatory (default: 5)."
        ),
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = build_report(
        max_widely_shared_commands=args.max_widely_shared_commands
    )
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
