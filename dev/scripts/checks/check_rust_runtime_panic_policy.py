#!/usr/bin/env python3
"""Guard against non-regressive unallowlisted runtime panic! growth."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from git_change_paths import list_changed_paths_with_base_map
except (
    ModuleNotFoundError
):  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.git_change_paths import list_changed_paths_with_base_map
try:
    from rust_guard_common import GuardContext
    from rust_guard_common import is_test_path as _is_test_path
except (
    ModuleNotFoundError
):  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.rust_guard_common import GuardContext
    from dev.scripts.checks.rust_guard_common import is_test_path as _is_test_path
try:
    from rust_check_text_utils import (
        mask_rust_comments_and_strings,
        strip_cfg_test_blocks,
    )
except (
    ModuleNotFoundError
):  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.rust_check_text_utils import (
        mask_rust_comments_and_strings,
        strip_cfg_test_blocks,
    )

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

PANIC_MACRO_RE = re.compile(r"\bpanic!\s*\(")
PANIC_ALLOW_MARKER_RE = re.compile(r"panic-policy:\s*allow\b", re.IGNORECASE)
PANIC_ALLOW_REASON_RE = re.compile(r"\breason\s*=", re.IGNORECASE)


def _is_comment_like(raw_line: str) -> bool:
    stripped = raw_line.strip()
    return stripped.startswith(("//", "/*", "*", "///", "//!"))


def _has_allowlisted_panic_comment(
    lines: list[str], index: int, lookback: int = 3
) -> bool:
    min_index = max(0, index - lookback)
    for probe in range(index, min_index - 1, -1):
        raw = lines[probe].strip()
        if PANIC_ALLOW_MARKER_RE.search(raw):
            return PANIC_ALLOW_REASON_RE.search(raw) is not None
        if probe == index:
            continue
        if raw and not _is_comment_like(raw) and not raw.startswith("#["):
            break
    return False


def _find_unallowlisted_panic_lines(text: str | None) -> list[int]:
    if text is None:
        return []
    text = strip_cfg_test_blocks(text)
    masked_text = mask_rust_comments_and_strings(text)
    lines = text.splitlines()
    masked_lines = masked_text.splitlines()
    line_numbers: list[int] = []
    for index, line in enumerate(lines):
        if index >= len(masked_lines):
            break
        panic_matches = list(PANIC_MACRO_RE.finditer(masked_lines[index]))
        if not panic_matches:
            continue
        if _is_comment_like(line):
            continue
        if _has_allowlisted_panic_comment(lines, index):
            continue
        for _ in panic_matches:
            line_numbers.append(index + 1)
    return line_numbers


def _count_metrics(text: str | None) -> dict[str, object]:
    line_numbers = _find_unallowlisted_panic_lines(text)
    return {
        "unallowlisted_panic_calls": len(line_numbers),
        "unallowlisted_panic_line_numbers": line_numbers,
    }


def _render_md(report: dict) -> str:
    lines = ["# check_rust_runtime_panic_policy", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- files_skipped_non_rust: {report['files_skipped_non_rust']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")
    lines.append(
        "- aggregate_growth: "
        f"unallowlisted_panic_calls {report['totals']['unallowlisted_panic_calls_growth']:+d}"
    )

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: add nearby comment `// panic-policy: allow reason=<why panic is required>` "
            "for any new runtime panic path, or replace with typed error handling."
        )
        for item in report["violations"]:
            line_hint = ", ".join(
                str(v) for v in item["current"]["unallowlisted_panic_line_numbers"][:8]
            )
            if line_hint:
                line_hint = f" lines {line_hint}"
            lines.append(
                f"- `{item['path']}`: unallowlisted_panic_calls "
                f"{item['base']['unallowlisted_panic_calls']} -> "
                f"{item['current']['unallowlisted_panic_calls']} "
                f"({item['growth']['unallowlisted_panic_calls']:+d}){line_hint}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument(
        "--head-ref", default="HEAD", help="Head ref used with --since-ref"
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, base_map = list_changed_paths_with_base_map(
            guard.run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError as exc:
        report = {
            "command": "check_rust_runtime_panic_policy",
            "timestamp": datetime.now().isoformat(),
            "ok": False,
            "error": str(exc),
        }
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print("# check_rust_runtime_panic_policy\n")
            print(f"- ok: False\n- error: {report['error']}")
        return 2

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_rust = 0
    files_skipped_tests = 0
    totals_unallowlisted_growth = 0
    violations: list[dict] = []

    for path in changed_paths:
        if path.suffix != ".rs":
            files_skipped_non_rust += 1
            continue
        if _is_test_path(path):
            files_skipped_tests += 1
            continue

        files_considered += 1

        base_path = base_map.get(path, path)
        if args.since_ref:
            base_text = guard.read_text_from_ref(base_path, args.since_ref)
            current_text = guard.read_text_from_ref(path, args.head_ref)
        else:
            base_text = guard.read_text_from_ref(base_path, "HEAD")
            current_text = guard.read_text_from_worktree(path)

        base = _count_metrics(base_text)
        current = _count_metrics(current_text)
        growth = {
            "unallowlisted_panic_calls": int(current["unallowlisted_panic_calls"])
            - int(base["unallowlisted_panic_calls"])
        }
        totals_unallowlisted_growth += growth["unallowlisted_panic_calls"]

        if growth["unallowlisted_panic_calls"] > 0:
            violations.append(
                {
                    "path": path.as_posix(),
                    "base": base,
                    "current": current,
                    "growth": growth,
                }
            )

    report = {
        "command": "check_rust_runtime_panic_policy",
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "ok": len(violations) == 0,
        "files_changed": len(changed_paths),
        "files_considered": files_considered,
        "files_skipped_non_rust": files_skipped_non_rust,
        "files_skipped_tests": files_skipped_tests,
        "totals": {
            "unallowlisted_panic_calls_growth": totals_unallowlisted_growth,
        },
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
