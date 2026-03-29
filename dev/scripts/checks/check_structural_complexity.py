#!/usr/bin/env python3
"""Guard against excessive structural complexity in Rust functions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, import_attr, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, emit_runtime_error, import_attr, utc_timestamp

scan_rust_functions = import_attr("code_shape_function_policy", "scan_rust_functions")
list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")
_collect_rust_files = import_attr("rust_guard_common", "collect_rust_files")
_normalize_changed_paths = import_attr(
    "rust_guard_common", "normalize_changed_rust_paths"
)
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

guard = GuardContext(REPO_ROOT)
SOURCE_ROOT = REPO_ROOT / "rust" / "src"

IF_RE = re.compile(r"\bif\b")
MATCH_RE = re.compile(r"\bmatch\b")
FOR_RE = re.compile(r"\bfor\b")
WHILE_RE = re.compile(r"\bwhile\b")
LOOP_RE = re.compile(r"\bloop\b")

@dataclass(frozen=True)
class ComplexityPolicy:
    max_score: int
    max_branch_points: int
    max_nesting_depth: int

@dataclass(frozen=True)
class ComplexityException:
    max_score: int
    max_branch_points: int
    max_nesting_depth: int
    owner: str
    expires_on: str
    follow_up_mp: str
    reason: str

DEFAULT_POLICY = ComplexityPolicy(
    max_score=90,
    max_branch_points=85,
    max_nesting_depth=10,
)

# Keep empty by default. Add entries only for approved temporary waivers.
FUNCTION_COMPLEXITY_EXCEPTIONS: dict[str, ComplexityException] = {}

def _path_for_report(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()

def _parse_exception_expiry(raw_value: str) -> date | None:
    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        return None

def _count_branch_points(text: str) -> int:
    return (
        len(IF_RE.findall(text))
        + len(MATCH_RE.findall(text))
        + len(FOR_RE.findall(text))
        + len(WHILE_RE.findall(text))
        + len(LOOP_RE.findall(text))
        + text.count("&&")
        + text.count("||")
        + text.count("?")
    )

def _max_nesting_depth(text: str) -> int:
    depth = 0
    max_depth = 0
    for char in text:
        if char == "{":
            depth += 1
            if depth > max_depth:
                max_depth = depth
        elif char == "}":
            depth = max(0, depth - 1)
    return max_depth

def _render_md(report: dict) -> str:
    lines = ["# check_structural_complexity", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- source_root: {report['source_root']}")
    lines.append(f"- include_tests: {report['include_tests']}")
    lines.append(f"- files_scanned: {report['files_scanned']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- functions_scanned: {report['functions_scanned']}")
    lines.append(f"- exceptions_defined: {report['exceptions_defined']}")
    lines.append(f"- exceptions_used: {report['exceptions_used']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for violation in report["violations"]:
            lines.append(
                f"- `{violation['path']}::{violation['function_name']}`: "
                f"score={violation['score']} "
                f"(branches={violation['branch_points']}, depth={violation['max_nesting_depth']}) "
                f"exceeds limits score<={violation['limit']['max_score']}, "
                f"branches<={violation['limit']['max_branch_points']}, "
                f"depth<={violation['limit']['max_nesting_depth']} ({violation['reason']})"
            )

    return "\n".join(lines)

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument(
        "--head-ref", default="HEAD", help="Head ref used with --since-ref"
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in complexity scan",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser

def main() -> int:
    args = _build_parser().parse_args()
    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, _base_map = list_changed_paths_with_base_map(
            guard.run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError as exc:
        return emit_runtime_error("check_structural_complexity", args.format, str(exc))

    files, skipped_tests = _collect_rust_files(
        SOURCE_ROOT,
        include_tests=args.include_tests,
    )
    changed_path_filter = (
        _normalize_changed_paths(changed_paths, include_tests=args.include_tests)
        if args.since_ref
        else None
    )

    mode = "commit-range" if args.since_ref else "working-tree"
    today = date.today()
    functions_scanned = 0
    exceptions_used = 0
    violations: list[dict] = []

    for path in files:
        path_str = _path_for_report(path)
        if changed_path_filter is not None and path_str not in changed_path_filter:
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        text = strip_cfg_test_blocks(text)
        lines = text.splitlines()
        functions = scan_rust_functions(text)
        functions_scanned += len(functions)

        for function in functions:
            start = int(function["start_line"]) - 1
            end = int(function["end_line"])
            body = "\n".join(lines[start:end])
            branch_points = _count_branch_points(body)
            max_nesting_depth = _max_nesting_depth(body)
            score = branch_points + max(0, max_nesting_depth - 1)

            function_name = str(function["name"])
            key = f"{path_str}::{function_name}"
            exception = FUNCTION_COMPLEXITY_EXCEPTIONS.get(key)
            limit = DEFAULT_POLICY
            reason = "exceeds_default_policy"

            if exception is not None:
                expiry = _parse_exception_expiry(exception.expires_on)
                if expiry is None:
                    violations.append(
                        {
                            "path": path_str,
                            "function_name": function_name,
                            "score": score,
                            "branch_points": branch_points,
                            "max_nesting_depth": max_nesting_depth,
                            "reason": "exception_invalid_expiry",
                            "limit": {
                                "max_score": exception.max_score,
                                "max_branch_points": exception.max_branch_points,
                                "max_nesting_depth": exception.max_nesting_depth,
                            },
                        }
                    )
                    continue
                if today <= expiry:
                    limit = ComplexityPolicy(
                        max_score=exception.max_score,
                        max_branch_points=exception.max_branch_points,
                        max_nesting_depth=exception.max_nesting_depth,
                    )
                    reason = "exceeds_exception_policy"
                    exceptions_used += 1
                else:
                    violations.append(
                        {
                            "path": path_str,
                            "function_name": function_name,
                            "score": score,
                            "branch_points": branch_points,
                            "max_nesting_depth": max_nesting_depth,
                            "reason": "exception_expired",
                            "limit": {
                                "max_score": exception.max_score,
                                "max_branch_points": exception.max_branch_points,
                                "max_nesting_depth": exception.max_nesting_depth,
                            },
                        }
                    )
                    continue

            if (
                score <= limit.max_score
                and branch_points <= limit.max_branch_points
                and max_nesting_depth <= limit.max_nesting_depth
            ):
                continue

            violations.append(
                {
                    "path": path_str,
                    "function_name": function_name,
                    "score": score,
                    "branch_points": branch_points,
                    "max_nesting_depth": max_nesting_depth,
                    "line_count": int(function["line_count"]),
                    "reason": reason,
                    "limit": {
                        "max_score": limit.max_score,
                        "max_branch_points": limit.max_branch_points,
                        "max_nesting_depth": limit.max_nesting_depth,
                    },
                }
            )

    report = {
        "command": "check_structural_complexity",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "ok": len(violations) == 0,
        "source_root": _path_for_report(SOURCE_ROOT),
        "include_tests": args.include_tests,
        "files_scanned": len(files),
        "files_skipped_tests": skipped_tests,
        "functions_scanned": functions_scanned,
        "exceptions_defined": len(FUNCTION_COMPLEXITY_EXCEPTIONS),
        "exceptions_used": exceptions_used,
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1

if __name__ == "__main__":
    sys.exit(main())
