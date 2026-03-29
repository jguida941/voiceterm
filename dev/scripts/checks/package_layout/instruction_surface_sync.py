#!/usr/bin/env python3
"""Validate generated instruction and starter surfaces against repo policy."""

from __future__ import annotations

import argparse
import json

if __package__:
    from .bootstrap import REPO_ROOT, import_repo_module
else:  # pragma: no cover - standalone script fallback
    from bootstrap import REPO_ROOT, import_repo_module

_surfaces_module = import_repo_module(
    "dev.scripts.devctl.governance.surfaces",
    repo_root=REPO_ROOT,
)
build_surface_report = _surfaces_module.build_surface_report
render_surface_report_markdown = _surfaces_module.render_surface_report_markdown


def build_report(
    *,
    policy_path: str | None = None,
) -> dict:
    """Return the generated-surface sync report."""
    report = build_surface_report(
        policy_path=policy_path,
        allow_missing_local_only=True,
        allowed_renderers=frozenset({"template_file"}),
    )
    report["command"] = "check_instruction_surface_sync"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quality-policy",
        help="Optional repo policy JSON file to resolve.",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()
    report = build_report(policy_path=args.quality_policy)
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(
            render_surface_report_markdown(report).replace(
                "# devctl render-surfaces",
                "# check_instruction_surface_sync",
                1,
            )
        )
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":  # pragma: no cover - wrapper entrypoint
    raise SystemExit(main())
