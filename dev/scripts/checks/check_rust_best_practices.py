#!/usr/bin/env python3
"""Guard against non-regressive Rust best-practice drift in changed files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from check_bootstrap import emit_runtime_error, import_attr, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import emit_runtime_error, import_attr, utc_timestamp

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")
_is_test_path = import_attr("rust_guard_common", "is_test_path")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

ALLOW_ATTR_RE = re.compile(r"#\s*\[\s*allow\s*\((?P<body>[^\]]*)\)\s*\]", re.DOTALL)
ALLOW_REASON_RE = re.compile(r"\breason\s*=")
UNSAFE_BLOCK_RE = re.compile(r"\bunsafe\s*\{")
UNSAFE_FN_RE = re.compile(r"\bunsafe\s+fn\b")
PUB_UNSAFE_FN_RE = re.compile(r"\bpub(?:\s*\([^\)]*\))?\s+unsafe\s+fn\b")
UNSAFE_IMPL_RE = re.compile(r"\bunsafe\s+impl\b")
MEM_FORGET_RE = re.compile(r"\b(?:std::mem::forget|mem::forget)\s*\(")
RESULT_STRING_RE = re.compile(r"Result\s*<[^>]*,\s*String\s*>")
EXPECT_JOIN_RECV_RE = re.compile(
    r"\.\s*(?:join|recv|recv_timeout)\s*\(\s*\)\s*\.\s*expect\s*\("
)
ENV_MUTATION_RE = re.compile(r"\b(?:std::)?env::(?:set_var|remove_var)\s*\(")


def _count_allow_without_reason(text: str | None) -> int:
    if text is None:
        return 0
    count = 0
    for match in ALLOW_ATTR_RE.finditer(text):
        body = match.group("body")
        if not ALLOW_REASON_RE.search(body):
            count += 1
    return count


def _has_nearby_safety_comment(lines: list[str], index: int, lookback: int = 5) -> bool:
    min_index = max(0, index - lookback)
    for probe in range(index - 1, min_index - 1, -1):
        raw = lines[probe].strip()
        if not raw:
            continue
        if "SAFETY:" in raw or "# Safety" in raw:
            return True
        if raw.startswith(("//", "/*", "*", "///", "//!", "#[")):
            continue
        break
    return False


def _count_undocumented_unsafe_blocks(text: str | None) -> int:
    if text is None:
        return 0
    lines = text.splitlines()
    count = 0
    for index, line in enumerate(lines):
        if not UNSAFE_BLOCK_RE.search(line):
            continue
        if UNSAFE_FN_RE.search(line):
            # `unsafe fn ... {` is tracked by the missing safety-docs metric below.
            continue
        if not _has_nearby_safety_comment(lines, index):
            count += 1
    return count


def _public_unsafe_fn_missing_safety_docs(lines: list[str], index: int) -> bool:
    saw_doc = False
    saw_safety_heading = False
    probe = index - 1
    while probe >= 0:
        raw = lines[probe].strip()
        if not raw:
            if saw_doc:
                break
            probe -= 1
            continue
        if raw.startswith("#["):
            probe -= 1
            continue
        if raw.startswith("///"):
            saw_doc = True
            if "# Safety" in raw:
                saw_safety_heading = True
            probe -= 1
            continue
        break
    return not (saw_doc and saw_safety_heading)


def _count_pub_unsafe_fn_missing_safety_docs(text: str | None) -> int:
    if text is None:
        return 0
    lines = text.splitlines()
    count = 0
    for index, line in enumerate(lines):
        if not PUB_UNSAFE_FN_RE.search(line):
            continue
        if _public_unsafe_fn_missing_safety_docs(lines, index):
            count += 1
    return count


def _count_unsafe_impl_missing_safety_comment(text: str | None) -> int:
    if text is None:
        return 0
    lines = text.splitlines()
    count = 0
    for index, line in enumerate(lines):
        if not UNSAFE_IMPL_RE.search(line):
            continue
        if not _has_nearby_safety_comment(lines, index):
            count += 1
    return count


def _count_mem_forget_calls(text: str | None) -> int:
    if text is None:
        return 0
    return len(MEM_FORGET_RE.findall(text))


def _count_result_string(text: str | None) -> int:
    if text is None:
        return 0
    return len(RESULT_STRING_RE.findall(text))


def _count_expect_on_join_recv(text: str | None) -> int:
    if text is None:
        return 0
    return len(EXPECT_JOIN_RECV_RE.findall(text))


def _count_env_mutation_calls(text: str | None) -> int:
    if text is None:
        return 0
    return len(ENV_MUTATION_RE.findall(text))


def _count_metrics(text: str | None) -> dict[str, int]:
    if text is not None:
        text = strip_cfg_test_blocks(text)
    return {
        "allow_without_reason": _count_allow_without_reason(text),
        "undocumented_unsafe_blocks": _count_undocumented_unsafe_blocks(text),
        "pub_unsafe_fn_missing_safety_docs": _count_pub_unsafe_fn_missing_safety_docs(
            text
        ),
        "unsafe_impl_missing_safety_comment": _count_unsafe_impl_missing_safety_comment(
            text
        ),
        "mem_forget_calls": _count_mem_forget_calls(text),
        "result_string_types": _count_result_string(text),
        "expect_on_join_recv": _count_expect_on_join_recv(text),
        "env_mutation_calls": _count_env_mutation_calls(text),
    }


def _render_md(report: dict) -> str:
    lines = ["# check_rust_best_practices", ""]
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
        f"allow_without_reason {totals['allow_without_reason_growth']:+d}, "
        f"undocumented_unsafe_blocks {totals['undocumented_unsafe_blocks_growth']:+d}, "
        "pub_unsafe_fn_missing_safety_docs "
        f"{totals['pub_unsafe_fn_missing_safety_docs_growth']:+d}, "
        "unsafe_impl_missing_safety_comment "
        f"{totals['unsafe_impl_missing_safety_comment_growth']:+d}, "
        f"mem_forget_calls {totals['mem_forget_calls_growth']:+d}, "
        f"result_string_types {totals['result_string_types_growth']:+d}, "
        f"expect_on_join_recv {totals['expect_on_join_recv_growth']:+d}, "
        f"env_mutation_calls {totals['env_mutation_calls_growth']:+d}"
    )

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for item in report["violations"]:
            growth = item["growth"]
            lines.append(
                f"- `{item['path']}`: allow_without_reason "
                f"{item['base']['allow_without_reason']} -> "
                f"{item['current']['allow_without_reason']} "
                f"({growth['allow_without_reason']:+d}), "
                "undocumented_unsafe_blocks "
                f"{item['base']['undocumented_unsafe_blocks']} -> "
                f"{item['current']['undocumented_unsafe_blocks']} "
                f"({growth['undocumented_unsafe_blocks']:+d}), "
                "pub_unsafe_fn_missing_safety_docs "
                f"{item['base']['pub_unsafe_fn_missing_safety_docs']} -> "
                f"{item['current']['pub_unsafe_fn_missing_safety_docs']} "
                f"({growth['pub_unsafe_fn_missing_safety_docs']:+d}), "
                "unsafe_impl_missing_safety_comment "
                f"{item['base']['unsafe_impl_missing_safety_comment']} -> "
                f"{item['current']['unsafe_impl_missing_safety_comment']} "
                f"({growth['unsafe_impl_missing_safety_comment']:+d}), "
                f"mem_forget_calls {item['base']['mem_forget_calls']} -> "
                f"{item['current']['mem_forget_calls']} "
                f"({growth['mem_forget_calls']:+d}), "
                f"result_string_types {item['base']['result_string_types']} -> "
                f"{item['current']['result_string_types']} "
                f"({growth['result_string_types']:+d}), "
                f"expect_on_join_recv {item['base']['expect_on_join_recv']} -> "
                f"{item['current']['expect_on_join_recv']} "
                f"({growth['expect_on_join_recv']:+d}), "
                f"env_mutation_calls {item['base']['env_mutation_calls']} -> "
                f"{item['current']['env_mutation_calls']} "
                f"({growth['env_mutation_calls']:+d})"
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
        return emit_runtime_error("check_rust_best_practices", args.format, str(exc))

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_rust = 0
    files_skipped_tests = 0
    totals_allow_growth = 0
    totals_unsafe_growth = 0
    totals_pub_unsafe_docs_growth = 0
    totals_unsafe_impl_docs_growth = 0
    totals_mem_forget_growth = 0
    totals_result_string_growth = 0
    totals_expect_join_recv_growth = 0
    totals_env_mutation_growth = 0
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
            "allow_without_reason": current["allow_without_reason"]
            - base["allow_without_reason"],
            "undocumented_unsafe_blocks": current["undocumented_unsafe_blocks"]
            - base["undocumented_unsafe_blocks"],
            "pub_unsafe_fn_missing_safety_docs": current[
                "pub_unsafe_fn_missing_safety_docs"
            ]
            - base["pub_unsafe_fn_missing_safety_docs"],
            "unsafe_impl_missing_safety_comment": current[
                "unsafe_impl_missing_safety_comment"
            ]
            - base["unsafe_impl_missing_safety_comment"],
            "mem_forget_calls": current["mem_forget_calls"] - base["mem_forget_calls"],
            "result_string_types": current["result_string_types"]
            - base["result_string_types"],
            "expect_on_join_recv": current["expect_on_join_recv"]
            - base["expect_on_join_recv"],
            "env_mutation_calls": current["env_mutation_calls"]
            - base["env_mutation_calls"],
        }

        totals_allow_growth += growth["allow_without_reason"]
        totals_unsafe_growth += growth["undocumented_unsafe_blocks"]
        totals_pub_unsafe_docs_growth += growth["pub_unsafe_fn_missing_safety_docs"]
        totals_unsafe_impl_docs_growth += growth["unsafe_impl_missing_safety_comment"]
        totals_mem_forget_growth += growth["mem_forget_calls"]
        totals_result_string_growth += growth["result_string_types"]
        totals_expect_join_recv_growth += growth["expect_on_join_recv"]
        totals_env_mutation_growth += growth["env_mutation_calls"]

        if (
            growth["allow_without_reason"] > 0
            or growth["undocumented_unsafe_blocks"] > 0
            or growth["pub_unsafe_fn_missing_safety_docs"] > 0
            or growth["unsafe_impl_missing_safety_comment"] > 0
            or growth["mem_forget_calls"] > 0
            or growth["result_string_types"] > 0
            or growth["expect_on_join_recv"] > 0
            or growth["env_mutation_calls"] > 0
        ):
            violations.append(
                {
                    "path": path.as_posix(),
                    "base": base,
                    "current": current,
                    "growth": growth,
                }
            )

    report = {
        "command": "check_rust_best_practices",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "ok": len(violations) == 0,
        "files_changed": len(changed_paths),
        "files_considered": files_considered,
        "files_skipped_non_rust": files_skipped_non_rust,
        "files_skipped_tests": files_skipped_tests,
        "totals": {
            "allow_without_reason_growth": totals_allow_growth,
            "undocumented_unsafe_blocks_growth": totals_unsafe_growth,
            "pub_unsafe_fn_missing_safety_docs_growth": totals_pub_unsafe_docs_growth,
            "unsafe_impl_missing_safety_comment_growth": totals_unsafe_impl_docs_growth,
            "mem_forget_calls_growth": totals_mem_forget_growth,
            "result_string_types_growth": totals_result_string_growth,
            "expect_on_join_recv_growth": totals_expect_join_recv_growth,
            "env_mutation_calls_growth": totals_env_mutation_growth,
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
