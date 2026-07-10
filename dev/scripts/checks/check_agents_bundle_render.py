#!/usr/bin/env python3
"""Compatibility guard for the generated AGENTS boot-card surface."""

from __future__ import annotations

import argparse
import json
import sys

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.governance.surfaces import (  # noqa: E402
    build_surface_report,
    render_surface_report_markdown,
)


def build_report(*, write: bool = False) -> dict:
    """Validate or refresh AGENTS.md through render-surfaces."""
    report = build_surface_report(
        surface_ids=("agents_boot_card",),
        write=write,
        allow_missing_local_only=False,
        allowed_renderers=frozenset({"instruction_boot_card"}),
    )
    report["command"] = "check_agents_bundle_render"
    report["compatibility_note"] = (
        "AGENTS.md is now an InstructionBootCard projection; this guard "
        "delegates to render-surfaces for backward-compatible check bundles."
    )
    return report


def render_markdown(report: dict) -> str:
    return render_surface_report_markdown(report).replace(
        "# devctl render-surfaces",
        "# check_agents_bundle_render",
        1,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Rewrite AGENTS.md.")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = build_report(write=bool(args.write))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())
