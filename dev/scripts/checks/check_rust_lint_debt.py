#!/usr/bin/env python3
"""Guard against non-regressive Rust lint-debt growth in changed files."""

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
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.git_change_paths import list_changed_paths_with_base_map

REPO_ROOT = Path(__file__).resolve().parents[3]

ALLOW_ATTR_RE = re.compile(r"#\s*\[\s*allow\s*\(")
UNWRAP_EXPECT_RE = re.compile(r"\b(?:unwrap|expect)\s*\(")


def _run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip() or "git command failed")
    return result


def _validate_ref(ref: str) -> None:
    _run_git(["git", "rev-parse", "--verify", ref], check=True)


def _is_test_path(path: Path) -> bool:
    normalized = f"/{path.as_posix()}/"
    name = path.name
    return "/tests/" in normalized or name == "tests.rs" or name.endswith("_test.rs")


def _read_text_from_ref(path: Path, ref: str) -> str | None:
    spec = f"{ref}:{path.as_posix()}"
    result = _run_git(["git", "show", spec], check=False)
    if result.returncode == 0:
        return result.stdout

    stderr = result.stderr.strip().lower()
    missing_markers = ("does not exist in", "exists on disk, but not in", "fatal: path")
    if any(marker in stderr for marker in missing_markers):
        return None
    raise RuntimeError(result.stderr.strip() or f"failed to read {spec}")


def _read_text_from_worktree(path: Path) -> str | None:
    absolute = REPO_ROOT / path
    if not absolute.exists():
        return None
    return absolute.read_text(encoding="utf-8", errors="replace")


def _count_metrics(text: str | None) -> dict[str, int]:
    if text is None:
        return {"allow_attrs": 0, "unwrap_expect_calls": 0}
    return {
        "allow_attrs": len(ALLOW_ATTR_RE.findall(text)),
        "unwrap_expect_calls": len(UNWRAP_EXPECT_RE.findall(text)),
    }


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
        f"unwrap_expect_calls {totals['unwrap_expect_calls_growth']:+d}"
    )

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for item in report["violations"]:
            lines.append(
                f"- `{item['path']}`: allow_attrs {item['base']['allow_attrs']} -> "
                f"{item['current']['allow_attrs']} ({item['growth']['allow_attrs']:+d}), "
                f"unwrap_expect_calls {item['base']['unwrap_expect_calls']} -> "
                f"{item['current']['unwrap_expect_calls']} "
                f"({item['growth']['unwrap_expect_calls']:+d})"
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
            "command": "check_rust_lint_debt",
            "timestamp": datetime.now().isoformat(),
            "ok": False,
            "error": str(exc),
        }
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print("# check_rust_lint_debt\n")
            print(f"- ok: False\n- error: {report['error']}")
        return 2

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_rust = 0
    files_skipped_tests = 0
    totals_allow_growth = 0
    totals_unwrap_growth = 0
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
            base_text = _read_text_from_ref(base_path, args.since_ref)
            current_text = _read_text_from_ref(path, args.head_ref)
        else:
            base_text = _read_text_from_ref(base_path, "HEAD")
            current_text = _read_text_from_worktree(path)

        base = _count_metrics(base_text)
        current = _count_metrics(current_text)
        growth = {
            "allow_attrs": current["allow_attrs"] - base["allow_attrs"],
            "unwrap_expect_calls": current["unwrap_expect_calls"] - base["unwrap_expect_calls"],
        }

        totals_allow_growth += growth["allow_attrs"]
        totals_unwrap_growth += growth["unwrap_expect_calls"]

        if growth["allow_attrs"] > 0 or growth["unwrap_expect_calls"] > 0:
            violations.append(
                {
                    "path": path.as_posix(),
                    "base": base,
                    "current": current,
                    "growth": growth,
                }
            )

    report = {
        "command": "check_rust_lint_debt",
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
            "allow_attrs_growth": totals_allow_growth,
            "unwrap_expect_calls_growth": totals_unwrap_growth,
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
