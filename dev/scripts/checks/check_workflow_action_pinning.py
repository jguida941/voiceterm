#!/usr/bin/env python3
"""Guard GitHub workflows so third-party actions are pinned to full SHAs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
WORKFLOW_GLOBS = (".github/workflows/*.yml", ".github/workflows/*.yaml")
SUPPRESSION_PREFIX = "workflow-action-pinning: allow="
USES_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<value>\S+)")
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")


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

        match = USES_PATTERN.match(line)
        if not match:
            continue

        uses_value = match.group("value").strip().strip("\"'")
        if uses_value.startswith("./") or uses_value.startswith("docker://"):
            continue

        if "@" not in uses_value:
            if "missing-ref" not in suppressions:
                violations.append(
                    {
                        "file": report_path,
                        "line": lineno,
                        "rule": "missing-ref",
                        "line_text": stripped,
                        "hint": "Use `<owner>/<repo>@<40-char-sha>` for workflow actions.",
                    }
                )
            continue

        _action, ref = uses_value.rsplit("@", 1)
        if "${{" in ref:
            if "dynamic-ref" not in suppressions:
                violations.append(
                    {
                        "file": report_path,
                        "line": lineno,
                        "rule": "dynamic-ref",
                        "line_text": stripped,
                        "hint": "Avoid dynamic action refs; pin to a 40-character commit SHA.",
                    }
                )
            continue

        if not SHA_PATTERN.fullmatch(ref) and "non-sha-ref" not in suppressions:
            violations.append(
                {
                    "file": report_path,
                    "line": lineno,
                    "rule": "non-sha-ref",
                    "line_text": stripped,
                    "hint": "Pin action refs to full 40-character commit SHAs.",
                }
            )

    return violations


def build_report(explicit_paths: list[str] | None = None) -> dict:
    paths = _discover_paths(explicit_paths)
    violations: list[dict[str, object]] = []
    for path in paths:
        violations.extend(_scan_file(path))
    return {
        "command": "check_workflow_action_pinning",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": not violations,
        "workflow_count": len(paths),
        "violations": violations,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# check_workflow_action_pinning",
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
