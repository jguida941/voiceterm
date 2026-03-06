#!/usr/bin/env python3
"""Flag check scripts that lack corresponding test files."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CHECKS_DIR = REPO_ROOT / "dev" / "scripts" / "checks"
TESTS_DIR = REPO_ROOT / "dev" / "scripts" / "devctl" / "tests"
SUPPORT_SUFFIXES = ("_support.py", "_core.py", "_render.py")


def _is_support_module(filename: str) -> bool:
    return any(filename.endswith(suffix) for suffix in SUPPORT_SUFFIXES)


def _find_test_file(check_name: str) -> bool:
    for candidate in TESTS_DIR.glob(f"test_{check_name}*.py"):
        return True
    bare_name = check_name.removeprefix("check_")
    for candidate in TESTS_DIR.glob(f"test_{bare_name}*.py"):
        return True
    return False


def build_report() -> dict:
    check_scripts = sorted(CHECKS_DIR.glob("check_*.py"))
    violations: list[dict[str, str]] = []
    tested_count = 0

    for script_path in check_scripts:
        filename = script_path.name
        if _is_support_module(filename):
            continue
        stem = filename.removesuffix(".py")
        if _find_test_file(stem):
            tested_count += 1
        else:
            violations.append({
                "file": f"dev/scripts/checks/{filename}",
                "hint": f"No test file found matching test_{stem}*.py or test_{stem.removeprefix('check_')}*.py",
            })

    total = tested_count + len(violations)
    return {
        "command": "check_test_coverage_parity",
        "timestamp": datetime.now().isoformat(),
        "ok": not violations,
        "total_checks": total,
        "tested_checks": tested_count,
        "violations": violations,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# check_test_coverage_parity",
        "",
        f"- ok: {report['ok']}",
        f"- total_checks: {report['total_checks']}",
        f"- tested_checks: {report['tested_checks']}",
        f"- untested: {len(report['violations'])}",
    ]
    violations = report.get("violations", [])
    if violations:
        lines.extend(["", "## Untested check scripts"])
        for v in violations:
            lines.append(f"- {v['file']} -> {v['hint']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()
    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
