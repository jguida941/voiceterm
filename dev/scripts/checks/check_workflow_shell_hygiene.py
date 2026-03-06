#!/usr/bin/env python3
"""Guard against shell anti-patterns in GitHub workflow run blocks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_GLOBS = (".github/workflows/*.yml", ".github/workflows/*.yaml")
SUPPRESSION_PREFIX = "workflow-shell-hygiene: allow="

RUN_BLOCK_RE = re.compile(r"^(\s*)run:\s*[|>]")

LINE_RULES = (
    {
        "id": "find-pipe-head",
        "pattern": re.compile(r"\bfind\b.+\|\s*head\s+-n\s+1\b"),
        "hint": "Use a deterministic bridge helper instead of `find ... | head -n 1`.",
    },
    {
        "id": "inline-python-heredoc",
        "pattern": re.compile(r"\bpython(?:3)?\s+<<\s*['\"]?[A-Za-z0-9_]+"),
        "hint": "Move inline Python snippets into `dev/scripts/*.py` helper modules.",
    },
    {
        "id": "inline-python-c",
        "pattern": re.compile(r"\bpython(?:3)?\s+-c\s+"),
        "hint": "Move inline Python snippets into `dev/scripts/*.py` helper modules.",
    },
)

# kept for backwards compat — older code may reference RULES
RULES = LINE_RULES


def _path_for_report(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _discover_paths(explicit_paths: list[str] | None) -> list[Path]:
    if explicit_paths:
        return sorted((REPO_ROOT / relative).resolve() for relative in explicit_paths)
    paths: set[Path] = set()
    for pattern in WORKFLOW_GLOBS:
        paths.update(REPO_ROOT.glob(pattern))
    return sorted(paths)


def _scan_run_blocks(lines: list[str], report_path: str) -> list[dict[str, object]]:
    """Flag multi-line run: blocks that don't start with set -euo pipefail."""
    violations: list[dict[str, object]] = []
    i = 0
    while i < len(lines):
        match = RUN_BLOCK_RE.match(lines[i])
        if not match:
            i += 1
            continue
        run_lineno = i + 1
        run_indent = len(match.group(1))
        # check for inline suppression on the run: line itself
        if SUPPRESSION_PREFIX in lines[i]:
            suffix = lines[i][lines[i].index(SUPPRESSION_PREFIX) + len(SUPPRESSION_PREFIX):]
            suppressed = {s.strip() for s in suffix.split(",") if s.strip()}
            if "all" in suppressed or "missing-pipefail" in suppressed:
                i += 1
                continue
        # find the first non-empty command line in the block body
        i += 1
        first_cmd = None
        first_cmd_lineno = None
        while i < len(lines):
            body_line = lines[i]
            if body_line.strip() == "":
                i += 1
                continue
            body_indent = len(body_line) - len(body_line.lstrip())
            if body_indent <= run_indent:
                break
            stripped = body_line.strip()
            if stripped.startswith("#"):
                i += 1
                continue
            first_cmd = stripped
            first_cmd_lineno = i + 1
            break
        if first_cmd is None:
            continue
        if first_cmd.startswith("set -euo pipefail") or first_cmd.startswith("set +e"):
            continue
        violations.append(
            {
                "file": report_path,
                "line": run_lineno,
                "rule": "missing-pipefail",
                "line_text": lines[run_lineno - 1].strip(),
                "hint": "Multi-line run: blocks should start with `set -euo pipefail`.",
            }
        )
    return violations


def _scan_file(path: Path) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [
            {
                "file": _path_for_report(path),
                "line": 0,
                "rule": "read-error",
                "line_text": "",
                "hint": str(exc),
            }
        ]
    report_path = _path_for_report(path)

    # line-level pattern rules
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        suppressions: set[str] = set()
        token_index = stripped.find(SUPPRESSION_PREFIX)
        if token_index >= 0:
            suffix = stripped[token_index + len(SUPPRESSION_PREFIX) :].strip()
            suppressions = {part.strip() for part in suffix.split(",") if part.strip()}
            if "all" in suppressions:
                continue
        for rule in LINE_RULES:
            if rule["id"] in suppressions:
                continue
            if rule["pattern"].search(line):
                violations.append(
                    {
                        "file": report_path,
                        "line": lineno,
                        "rule": rule["id"],
                        "line_text": stripped,
                        "hint": rule["hint"],
                    }
                )

    # block-level: multi-line run: blocks missing set -euo pipefail
    violations.extend(_scan_run_blocks(lines, report_path))

    return violations


def build_report(explicit_paths: list[str] | None = None) -> dict:
    paths = _discover_paths(explicit_paths)
    violations: list[dict[str, object]] = []
    for path in paths:
        violations.extend(_scan_file(path))
    return {
        "command": "check_workflow_shell_hygiene",
        "timestamp": datetime.now().isoformat(),
        "ok": not violations,
        "workflow_count": len(paths),
        "violations": violations,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# check_workflow_shell_hygiene",
        "",
        f"- ok: {report['ok']}",
        f"- workflow_count: {report['workflow_count']}",
        f"- violations: {len(report['violations'])}",
    ]
    violations = report.get("violations", [])
    if violations:
        lines.extend(["", "## Violations"])
        for violation in violations:
            lines.append(
                "- {file}:{line} [{rule}] `{line_text}` -> {hint}".format(
                    file=violation["file"],
                    line=violation["line"],
                    rule=violation["rule"],
                    line_text=violation["line_text"],
                    hint=violation["hint"],
                )
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument(
        "--paths",
        nargs="*",
        help="Optional repository-relative workflow paths to scan.",
    )
    args = parser.parse_args()
    report = build_report(args.paths)
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
