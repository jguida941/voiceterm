#!/usr/bin/env python3
"""Enforce high-signal Clippy lint baseline from JSON warning output."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
DEFAULT_BASELINE = REPO_ROOT / "dev/config/clippy/high_signal_lints.json"


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"json file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid json in {path}: {exc}") from exc


def _load_baseline(path: Path) -> dict[str, int]:
    payload = _read_json(path)
    lints = payload.get("lints")
    if not isinstance(lints, dict):
        raise RuntimeError(f"{path} must define object field `lints`")
    result: dict[str, int] = {}
    for lint, value in lints.items():
        if not isinstance(lint, str):
            raise RuntimeError(f"{path} contains non-string lint id: {lint!r}")
        if not isinstance(value, int) or value < 0:
            raise RuntimeError(f"{path} lint `{lint}` must map to non-negative integer")
        result[lint] = value
    if not result:
        raise RuntimeError(f"{path} must contain at least one lint baseline")
    return result


def _load_observed_lints(path: Path) -> dict[str, int]:
    payload = _read_json(path)
    lints = payload.get("lints")
    if not isinstance(lints, dict):
        raise RuntimeError(f"{path} must define object field `lints`")
    result: dict[str, int] = {}
    for lint, value in lints.items():
        if not isinstance(lint, str):
            raise RuntimeError(f"{path} contains non-string lint id: {lint!r}")
        if not isinstance(value, int) or value < 0:
            raise RuntimeError(f"{path} lint `{lint}` must map to non-negative integer")
        result[lint] = value
    return result


def _render_md(report: dict) -> str:
    lines = ["# check_clippy_high_signal", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- baseline_file: {report['baseline_file']}")
    lines.append(f"- input_file: {report['input_file']}")
    lines.append(f"- tracked_lints: {report['tracked_lints']}")
    lines.append(f"- observed_lints: {report['observed_lints']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("error"):
        lines.append(f"- error: {report['error']}")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for item in report["violations"]:
            lines.append(
                f"- `{item['lint']}`: observed {item['observed']} > max_allowed {item['max_allowed']}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-lints-json",
        required=True,
        help="Path to lint-count JSON emitted by collect_clippy_warnings.py",
    )
    parser.add_argument(
        "--baseline-file",
        default=str(DEFAULT_BASELINE),
        help="Path to high-signal lint baseline JSON",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    input_path = Path(args.input_lints_json)
    baseline_path = Path(args.baseline_file)

    try:
        baseline = _load_baseline(baseline_path)
        observed = _load_observed_lints(input_path)
    except RuntimeError as exc:
        report = {
            "command": "check_clippy_high_signal",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "ok": False,
            "baseline_file": str(baseline_path),
            "input_file": str(input_path),
            "tracked_lints": 0,
            "observed_lints": 0,
            "violations": [],
            "error": str(exc),
        }
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print(_render_md(report))
        return 2

    violations = []
    for lint, max_allowed in sorted(baseline.items()):
        observed_count = int(observed.get(lint, 0))
        if observed_count > max_allowed:
            violations.append(
                {
                    "lint": lint,
                    "max_allowed": max_allowed,
                    "observed": observed_count,
                }
            )

    report = {
        "command": "check_clippy_high_signal",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": len(violations) == 0,
        "baseline_file": str(baseline_path),
        "input_file": str(input_path),
        "tracked_lints": len(baseline),
        "observed_lints": len(observed),
        "violations": violations,
    }
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
