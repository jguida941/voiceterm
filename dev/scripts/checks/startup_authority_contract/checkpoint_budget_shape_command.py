#!/usr/bin/env python3
"""Render the typed startup checkpoint-budget shape."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .command import _load_governance
from .runtime_checks import classify_checkpoint_budget_shape

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

_COMMAND = "check_checkpoint_budget_shape"


def _build_report(
    repo_root: Path | None = None,
    *,
    governance=None,
) -> dict[str, object]:
    root = repo_root or REPO_ROOT
    gov = _load_governance(root, governance=governance)
    shape = classify_checkpoint_budget_shape(gov, repo_root=root).to_dict()
    return {
        "command": _COMMAND,
        "ok": not bool(shape.get("bootstrap_blocked")),
        "checkpoint_budget_shape": shape,
        "state": shape.get("state", "unknown"),
        "bootstrap_blocked": bool(shape.get("bootstrap_blocked")),
        "next_required_action": shape.get("next_required_action", "none"),
        "errors": list(shape.get("errors") or ()),
    }


def _render_md(report: dict[str, object]) -> str:
    shape = report.get("checkpoint_budget_shape")
    shape = shape if isinstance(shape, dict) else {}
    lines = [f"# {_COMMAND}", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- state: {report['state']}")
    lines.append(f"- bootstrap_blocked: {report['bootstrap_blocked']}")
    lines.append(f"- next_required_action: {report['next_required_action']}")
    lines.append(f"- pipeline_id: {shape.get('pipeline_id', '') or '(none)'}")
    lines.append(f"- pipeline_state: {shape.get('pipeline_state', '') or '(none)'}")
    lines.append(f"- tree_hash_match: {shape.get('tree_hash_match', False)}")
    lines.append(f"- receipt_backed: {shape.get('receipt_backed', False)}")
    errors = report.get("errors") or []
    if errors:
        lines.append("")
        lines.append("## Errors")
        for error in errors:
            lines.append(f"- {error}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = _build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
