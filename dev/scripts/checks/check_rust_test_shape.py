#!/usr/bin/env python3
"""Guard against non-regressive Rust test-file shape drift."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    from git_change_paths import list_changed_paths_with_base_map
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.git_change_paths import list_changed_paths_with_base_map
try:
    from rust_guard_common import (
        is_test_path as _is_test_path,
        read_text_from_ref as _read_text_from_ref_with_git,
        read_text_from_worktree as _read_text_from_worktree_with_root,
        run_git as _run_git_with_root,
        validate_ref as _validate_ref_with_git,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.rust_guard_common import (
        is_test_path as _is_test_path,
        read_text_from_ref as _read_text_from_ref_with_git,
        read_text_from_worktree as _read_text_from_worktree_with_root,
        run_git as _run_git_with_root,
        validate_ref as _validate_ref_with_git,
    )

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class TestShapePolicy:
    soft_limit: int
    hard_limit: int
    oversize_growth_limit: int
    hard_lock_growth_limit: int


DEFAULT_POLICY = TestShapePolicy(
    soft_limit=1200,
    hard_limit=1800,
    oversize_growth_limit=80,
    hard_lock_growth_limit=0,
)

PATH_POLICY_OVERRIDES: dict[str, TestShapePolicy] = {
    "rust/src/bin/voiceterm/event_loop/tests.rs": TestShapePolicy(
        soft_limit=6200,
        hard_limit=7000,
        oversize_growth_limit=80,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/writer/state/tests.rs": TestShapePolicy(
        soft_limit=2100,
        hard_limit=2600,
        oversize_growth_limit=400,
        hard_lock_growth_limit=0,
    ),
    "rust/src/ipc/tests.rs": TestShapePolicy(
        soft_limit=1800,
        hard_limit=2400,
        oversize_growth_limit=400,
        hard_lock_growth_limit=0,
    ),
}

TEST_SHAPE_AUDIT_GUIDANCE = (
    "Split large Rust test files into focused modules (for example behavior areas or fixtures) "
    "instead of extending one broad `tests.rs` surface."
)


def _run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run_git_with_root(REPO_ROOT, args, check=check)


def _validate_ref(ref: str) -> None:
    _validate_ref_with_git(_run_git, ref)


def _read_text_from_ref(path: Path, ref: str) -> str | None:
    return _read_text_from_ref_with_git(_run_git, path, ref)


def _read_text_from_worktree(path: Path) -> str | None:
    return _read_text_from_worktree_with_root(REPO_ROOT, path)


def _count_lines(text: str | None) -> int:
    if not text:
        return 0
    return len(text.splitlines())


def _policy_for_path(path: Path) -> tuple[TestShapePolicy, str]:
    override = PATH_POLICY_OVERRIDES.get(path.as_posix())
    if override is not None:
        return override, f"path_override:{path.as_posix()}"
    return DEFAULT_POLICY, "rust_test_default"


def _evaluate(base_lines: int, current_lines: int, policy: TestShapePolicy) -> str | None:
    growth = current_lines - base_lines

    if current_lines > policy.hard_limit and base_lines <= policy.hard_limit:
        return "crossed_hard_limit"
    if base_lines > policy.hard_limit and growth > policy.hard_lock_growth_limit:
        return "exceeded_hard_lock_growth_limit"

    if current_lines > policy.soft_limit and base_lines <= policy.soft_limit:
        return "crossed_soft_limit"
    if base_lines > policy.soft_limit and growth > policy.oversize_growth_limit:
        return "exceeded_oversize_growth_limit"

    return None


def _render_md(report: dict) -> str:
    lines = ["# check_rust_test_shape", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- files_skipped_non_rust: {report['files_skipped_non_rust']}")
    lines.append(f"- files_skipped_non_tests: {report['files_skipped_non_tests']}")
    lines.append(f"- files_using_path_overrides: {report['files_using_path_overrides']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for item in report["violations"]:
            lines.append(
                f"- `{item['path']}` ({item['reason']}): {item['base_lines']} -> "
                f"{item['current_lines']} (growth {item['growth']:+d}); "
                f"{TEST_SHAPE_AUDIT_GUIDANCE} [policy: {item['policy_source']}]"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument("--head-ref", default="HEAD", help="Head ref used with --since-ref")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    try:
        if args.since_ref:
            _validate_ref(args.since_ref)
            _validate_ref(args.head_ref)
        changed_paths, base_map = list_changed_paths_with_base_map(
            _run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError as exc:
        report = {
            "command": "check_rust_test_shape",
            "timestamp": datetime.now().isoformat(),
            "ok": False,
            "error": str(exc),
        }
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print("# check_rust_test_shape\n")
            print(f"- ok: False\n- error: {report['error']}")
        return 2

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_rust = 0
    files_skipped_non_tests = 0
    files_using_path_overrides = 0
    violations: list[dict] = []

    for path in changed_paths:
        if path.suffix != ".rs":
            files_skipped_non_rust += 1
            continue
        if not _is_test_path(path):
            files_skipped_non_tests += 1
            continue

        files_considered += 1

        policy, policy_source = _policy_for_path(path)
        if policy_source.startswith("path_override:"):
            files_using_path_overrides += 1

        base_path = base_map.get(path, path)
        if args.since_ref:
            base_text = _read_text_from_ref(base_path, args.since_ref)
            current_text = _read_text_from_ref(path, args.head_ref)
        else:
            base_text = _read_text_from_ref(base_path, "HEAD")
            current_text = _read_text_from_worktree(path)

        base_lines = _count_lines(base_text)
        current_lines = _count_lines(current_text)
        reason = _evaluate(base_lines, current_lines, policy)
        if reason is None:
            continue

        violations.append(
            {
                "path": path.as_posix(),
                "base_lines": base_lines,
                "current_lines": current_lines,
                "growth": current_lines - base_lines,
                "reason": reason,
                "policy": {
                    "soft_limit": policy.soft_limit,
                    "hard_limit": policy.hard_limit,
                    "oversize_growth_limit": policy.oversize_growth_limit,
                    "hard_lock_growth_limit": policy.hard_lock_growth_limit,
                },
                "policy_source": policy_source,
            }
        )

    report = {
        "command": "check_rust_test_shape",
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "ok": len(violations) == 0,
        "files_changed": len(changed_paths),
        "files_considered": files_considered,
        "files_skipped_non_rust": files_skipped_non_rust,
        "files_skipped_non_tests": files_skipped_non_tests,
        "files_using_path_overrides": files_using_path_overrides,
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
