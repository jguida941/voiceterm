#!/usr/bin/env python3
"""Verify governed lifecycle transition metadata is graph-walkable."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dev.scripts.devctl.runtime.governed_transitions import (
    GovernedTransitionModule,
    TransitionContract,
    governed_transition_modules_path,
    load_governed_transitions,
    load_transition_module_rows,
)

from .graph import verify_transition_paths
from .models import GovernedTransitionReport
from .render import render_md


def build_report(
    *,
    repo_root: Path,
    manifest_path: Path | None = None,
    transitions: Sequence[TransitionContract] | None = None,
    manifest_modules: Sequence[str] | None = None,
) -> GovernedTransitionReport:
    """Load and verify governed transitions."""
    resolved_manifest_path = manifest_path or governed_transition_modules_path(repo_root)
    rows: tuple[GovernedTransitionModule, ...] = ()
    if transitions is None:
        rows = load_transition_module_rows(resolved_manifest_path)
        transitions = load_governed_transitions(
            repo_root=repo_root,
            path=resolved_manifest_path,
        )
    module_names = tuple(manifest_modules or tuple(row.module for row in rows))
    path_checks = verify_transition_paths(tuple(transitions))
    return GovernedTransitionReport(
        ok=all(check.ok for check in path_checks),
        transition_count=len(transitions),
        checked_path_count=len(path_checks),
        manifest_modules=module_names,
        path_checks=path_checks,
    )


def main(argv: list[str] | None = None) -> int:
    checks_dir = Path(__file__).resolve().parent.parent
    if str(checks_dir) not in sys.path:
        sys.path.insert(0, str(checks_dir))

    from check_bootstrap import REPO_ROOT, emit_runtime_error

    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Optional governed transition module manifest path.",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(
            repo_root=REPO_ROOT,
            manifest_path=args.manifest,
        )
    except (ImportError, RuntimeError, TypeError, ValueError) as exc:
        return int(
            emit_runtime_error("check_governed_transitions", args.format, str(exc))
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
