#!/usr/bin/env python3
"""Guard against non-regressive Rust lint-debt growth in changed files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, import_attr, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, emit_runtime_error, import_attr, utc_timestamp

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")
_is_test_path = import_attr("rust_guard_common", "is_test_path")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

guard = GuardContext(REPO_ROOT)

ALLOW_ATTR_RE = re.compile(r"#\s*!?\s*\[\s*allow\s*\(")
ALLOW_ATTR_BODY_RE = re.compile(
    r"#\s*!?\s*\[\s*allow\s*\((?P<body>[^\]]*)\)\s*\]", re.DOTALL
)
DEAD_CODE_ALLOW_RE = re.compile(r"\bdead_code\b")
ALLOW_REASON_RE = re.compile(r"\breason\s*=")
UNWRAP_EXPECT_RE = re.compile(r"\b(?:unwrap|expect)\s*\(")
UNWRAP_EXPECT_UNCHECKED_RE = re.compile(r"\b(?:unwrap_unchecked|expect_unchecked)\s*\(")
PANIC_MACRO_RE = re.compile(r"\bpanic!\s*\(")

def _strip_cfg_test_blocks(text: str) -> str:
    """Backward-compatible wrapper used by unit tests."""
    return strip_cfg_test_blocks(text)

def _collect_dead_code_allow_instances(text: str | None) -> list[dict]:
    if text is None:
        return []
    instances: list[dict] = []
    for match in ALLOW_ATTR_BODY_RE.finditer(text):
        body = match.group("body")
        if not DEAD_CODE_ALLOW_RE.search(body):
            continue
        line = text.count("\n", 0, match.start()) + 1
        instances.append(
            {
                "line": line,
                "attribute": match.group(0).strip(),
                "has_reason": bool(ALLOW_REASON_RE.search(body)),
            }
        )
    return instances

def _count_metrics(text: str | None) -> dict[str, int]:
    if text is None:
        return {
            "allow_attrs": 0,
            "dead_code_allow_attrs": 0,
            "unwrap_expect_calls": 0,
            "unchecked_unwrap_expect_calls": 0,
            "panic_macro_calls": 0,
        }
    text = _strip_cfg_test_blocks(text)
    dead_code_allow_instances = _collect_dead_code_allow_instances(text)
    return {
        "allow_attrs": len(ALLOW_ATTR_RE.findall(text)),
        "dead_code_allow_attrs": len(dead_code_allow_instances),
        "unwrap_expect_calls": len(UNWRAP_EXPECT_RE.findall(text)),
        "unchecked_unwrap_expect_calls": len(UNWRAP_EXPECT_UNCHECKED_RE.findall(text)),
        "panic_macro_calls": len(PANIC_MACRO_RE.findall(text)),
    }

def _list_all_rust_paths(*, include_tests: bool) -> list[Path]:
    paths: set[Path] = set()
    tracked = guard.run_git(["git", "ls-files"]).stdout.splitlines()
    untracked = guard.run_git(
        ["git", "ls-files", "--others", "--exclude-standard"]
    ).stdout.splitlines()
    for raw in [*tracked, *untracked]:
        if not raw.strip():
            continue
        path = Path(raw.strip())
        if path.suffix != ".rs":
            continue
        if not include_tests and _is_test_path(path):
            continue
        paths.add(path)
    return sorted(paths)

def _render_md(report: dict) -> str:
    lines = ["# check_rust_lint_debt", ""]
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

    totals = report["totals"]
    lines.append(
        "- aggregate_growth: "
        f"allow_attrs {totals['allow_attrs_growth']:+d}, "
        f"dead_code_allow_attrs {totals['dead_code_allow_attrs_growth']:+d}, "
        f"unwrap_expect_calls {totals['unwrap_expect_calls_growth']:+d}, "
        "unchecked_unwrap_expect_calls "
        f"{totals['unchecked_unwrap_expect_calls_growth']:+d}, "
        f"panic_macro_calls {totals['panic_macro_calls_growth']:+d}"
    )
    lines.append(f"- dead_code_instances: {report['dead_code_instance_count']}")
    lines.append(
        f"- dead_code_without_reason: {report['dead_code_without_reason_count']}"
    )
    if report.get("dead_code_report_truncated"):
        lines.append("- dead_code_report_truncated: True")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for item in report["violations"]:
            lines.append(
                f"- `{item['path']}`: allow_attrs {item['base']['allow_attrs']} -> "
                f"{item['current']['allow_attrs']} ({item['growth']['allow_attrs']:+d}), "
                "dead_code_allow_attrs "
                f"{item['base']['dead_code_allow_attrs']} -> "
                f"{item['current']['dead_code_allow_attrs']} "
                f"({item['growth']['dead_code_allow_attrs']:+d}), "
                f"unwrap_expect_calls {item['base']['unwrap_expect_calls']} -> "
                f"{item['current']['unwrap_expect_calls']} "
                f"({item['growth']['unwrap_expect_calls']:+d}), "
                "unchecked_unwrap_expect_calls "
                f"{item['base']['unchecked_unwrap_expect_calls']} -> "
                f"{item['current']['unchecked_unwrap_expect_calls']} "
                f"({item['growth']['unchecked_unwrap_expect_calls']:+d}), "
                f"panic_macro_calls {item['base']['panic_macro_calls']} -> "
                f"{item['current']['panic_macro_calls']} "
                f"({item['growth']['panic_macro_calls']:+d})"
            )
    dead_code_instances = report.get("dead_code_instances", [])
    if dead_code_instances:
        lines.append("")
        lines.append("## Dead Code Allow Instances")
        for item in dead_code_instances:
            reason_label = "yes" if item["has_reason"] else "no"
            lines.append(
                f"- `{item['path']}:{item['line']}` reason={reason_label} "
                f"`{item['attribute']}`"
            )
    return "\n".join(lines)

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--absolute",
        action="store_true",
        help="Scan all tracked/untracked Rust source files instead of changed paths.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include Rust test files in scan results.",
    )
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument(
        "--head-ref", default="HEAD", help="Head ref used with --since-ref"
    )
    parser.add_argument(
        "--report-dead-code",
        action="store_true",
        help="Emit per-instance dead_code allow attributes for scanned files.",
    )
    parser.add_argument(
        "--dead-code-report-limit",
        type=int,
        default=200,
        help="Maximum dead_code instances to include when --report-dead-code is enabled.",
    )
    parser.add_argument(
        "--fail-on-undocumented-dead-code",
        action="store_true",
        help="Fail when any dead_code allow instance is missing a reason.",
    )
    parser.add_argument(
        "--fail-on-any-dead-code",
        action="store_true",
        help="Fail when any dead_code allow instance is present in scanned files.",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser

def main() -> int:
    args = _build_parser().parse_args()
    if args.absolute and args.since_ref:
        return emit_runtime_error(
            "check_rust_lint_debt",
            args.format,
            "--absolute cannot be combined with --since-ref/--head-ref",
        )

    try:
        if args.absolute:
            changed_paths = _list_all_rust_paths(include_tests=args.include_tests)
            base_map: dict[Path, Path] = {}
        else:
            if args.since_ref:
                guard.validate_ref(args.since_ref)
                guard.validate_ref(args.head_ref)
            changed_paths, base_map = list_changed_paths_with_base_map(
                guard.run_git,
                args.since_ref,
                args.head_ref,
            )
    except RuntimeError as exc:
        return emit_runtime_error("check_rust_lint_debt", args.format, str(exc))

    mode = (
        "absolute"
        if args.absolute
        else ("commit-range" if args.since_ref else "working-tree")
    )
    files_considered = 0
    files_skipped_non_rust = 0
    files_skipped_tests = 0
    totals_allow_growth = 0
    totals_dead_code_allow_growth = 0
    totals_unwrap_growth = 0
    totals_unchecked_unwrap_growth = 0
    totals_panic_growth = 0
    total_dead_code_instance_count = 0
    violations: list[dict] = []
    dead_code_instances: list[dict] = []
    dead_code_without_reason_count = 0
    dead_code_report_limit = max(0, args.dead_code_report_limit)

    for path in changed_paths:
        if path.suffix != ".rs":
            files_skipped_non_rust += 1
            continue
        if not args.include_tests and _is_test_path(path):
            files_skipped_tests += 1
            continue

        files_considered += 1

        base_path = base_map.get(path, path)
        if args.absolute:
            base_text = guard.read_text_from_worktree(path)
            current_text = base_text
        elif args.since_ref:
            base_text = guard.read_text_from_ref(base_path, args.since_ref)
            current_text = guard.read_text_from_ref(path, args.head_ref)
        else:
            base_text = guard.read_text_from_ref(base_path, "HEAD")
            current_text = guard.read_text_from_worktree(path)

        base = _count_metrics(base_text)
        current = _count_metrics(current_text)
        growth = {
            "allow_attrs": current["allow_attrs"] - base["allow_attrs"],
            "dead_code_allow_attrs": current["dead_code_allow_attrs"]
            - base["dead_code_allow_attrs"],
            "unwrap_expect_calls": current["unwrap_expect_calls"]
            - base["unwrap_expect_calls"],
            "unchecked_unwrap_expect_calls": current["unchecked_unwrap_expect_calls"]
            - base["unchecked_unwrap_expect_calls"],
            "panic_macro_calls": current["panic_macro_calls"]
            - base["panic_macro_calls"],
        }

        totals_allow_growth += growth["allow_attrs"]
        totals_dead_code_allow_growth += growth["dead_code_allow_attrs"]
        totals_unwrap_growth += growth["unwrap_expect_calls"]
        totals_unchecked_unwrap_growth += growth["unchecked_unwrap_expect_calls"]
        totals_panic_growth += growth["panic_macro_calls"]
        total_dead_code_instance_count += current["dead_code_allow_attrs"]

        if (
            args.report_dead_code
            or args.fail_on_undocumented_dead_code
            or args.fail_on_any_dead_code
        ):
            file_dead_code_instances = _collect_dead_code_allow_instances(
                _strip_cfg_test_blocks(current_text)
                if current_text is not None
                else None
            )
            dead_code_without_reason_count += sum(
                1 for item in file_dead_code_instances if not item["has_reason"]
            )
            for item in file_dead_code_instances:
                if (
                    dead_code_report_limit > 0
                    and len(dead_code_instances) >= dead_code_report_limit
                ):
                    break
                dead_code_instances.append(
                    {
                        "path": path.as_posix(),
                        "line": item["line"],
                        "has_reason": item["has_reason"],
                        "attribute": item["attribute"],
                    }
                )

        if (
            growth["allow_attrs"] > 0
            or growth["dead_code_allow_attrs"] > 0
            or growth["unwrap_expect_calls"] > 0
            or growth["unchecked_unwrap_expect_calls"] > 0
            or growth["panic_macro_calls"] > 0
        ):
            violations.append(
                {
                    "path": path.as_posix(),
                    "base": base,
                    "current": current,
                    "growth": growth,
                }
            )

    dead_code_instance_count = total_dead_code_instance_count
    fail_due_to_dead_code_policy = False
    if args.fail_on_undocumented_dead_code and dead_code_without_reason_count > 0:
        fail_due_to_dead_code_policy = True
    if args.fail_on_any_dead_code and dead_code_instance_count > 0:
        fail_due_to_dead_code_policy = True

    report = {
        "command": "check_rust_lint_debt",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": args.since_ref if mode == "commit-range" else None,
        "head_ref": args.head_ref if mode == "commit-range" else None,
        "ok": len(violations) == 0 and not fail_due_to_dead_code_policy,
        "files_changed": len(changed_paths),
        "files_considered": files_considered,
        "files_skipped_non_rust": files_skipped_non_rust,
        "files_skipped_tests": files_skipped_tests,
        "totals": {
            "allow_attrs_growth": totals_allow_growth,
            "dead_code_allow_attrs_growth": totals_dead_code_allow_growth,
            "unwrap_expect_calls_growth": totals_unwrap_growth,
            "unchecked_unwrap_expect_calls_growth": totals_unchecked_unwrap_growth,
            "panic_macro_calls_growth": totals_panic_growth,
        },
        "dead_code_instance_count": dead_code_instance_count,
        "dead_code_without_reason_count": dead_code_without_reason_count,
        "dead_code_instances": dead_code_instances if args.report_dead_code else [],
        "dead_code_report_truncated": (
            args.report_dead_code
            and dead_code_report_limit > 0
            and dead_code_instance_count > len(dead_code_instances)
        ),
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1

if __name__ == "__main__":
    sys.exit(main())
