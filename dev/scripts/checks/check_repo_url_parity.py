#!/usr/bin/env python3
"""Guard that all repo URL references point to the canonical repository."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_URL = "github.com/jguida941/voiceterm"
URL_PATTERN = re.compile(r"github\.com/jguida941/[a-zA-Z0-9_-]+")

SCAN_FILES = (
    "rust/Cargo.toml",
    "README.md",
    "pypi/pyproject.toml",
    ".coderabbit.yaml",
)


def _path_for_report(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _scan_file(path: Path) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [
            {
                "file": _path_for_report(path),
                "line": 0,
                "url": "",
                "hint": str(exc),
            }
        ]

    report_path = _path_for_report(path)
    for lineno, line in enumerate(lines, start=1):
        for match in URL_PATTERN.finditer(line):
            found = match.group(0)
            if found != CANONICAL_URL:
                violations.append(
                    {
                        "file": report_path,
                        "line": lineno,
                        "url": found,
                        "hint": f"Expected {CANONICAL_URL}, found {found}",
                    }
                )
    return violations


def build_report() -> dict:
    violations: list[dict[str, object]] = []
    scanned = 0
    for relative in SCAN_FILES:
        path = REPO_ROOT / relative
        if not path.exists():
            continue
        scanned += 1
        violations.extend(_scan_file(path))
    return {
        "command": "check_repo_url_parity",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": not violations,
        "files_scanned": scanned,
        "violations": violations,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# check_repo_url_parity",
        "",
        f"- ok: {report['ok']}",
        f"- files_scanned: {report['files_scanned']}",
        f"- violations: {len(report['violations'])}",
    ]
    violations = report.get("violations", [])
    if violations:
        lines.extend(["", "## Violations"])
        for v in violations:
            lines.append(f"- {v['file']}:{v['line']} `{v['url']}` -> {v['hint']}")
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
