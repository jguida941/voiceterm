#!/usr/bin/env python3
"""Guard against non-regressive Rust best-practice drift in changed files."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

ALLOW_ATTR_RE = re.compile(r"#\s*\[\s*allow\s*\((?P<body>[^\]]*)\)\s*\]", re.DOTALL)
ALLOW_REASON_RE = re.compile(r"\breason\s*=")
UNSAFE_BLOCK_RE = re.compile(r"\bunsafe\s*\{")
UNSAFE_FN_RE = re.compile(r"\bunsafe\s+fn\b")
PUB_UNSAFE_FN_RE = re.compile(r"\bpub(?:\s*\([^\)]*\))?\s+unsafe\s+fn\b")


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


def _list_changed_paths(since_ref: str | None, head_ref: str) -> list[Path]:
    if since_ref:
        diff_cmd = ["git", "diff", "--name-only", "--diff-filter=ACMR", since_ref, head_ref]
    else:
        diff_cmd = ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"]

    changed = {Path(line.strip()) for line in _run_git(diff_cmd).stdout.splitlines() if line.strip()}

    if since_ref is None:
        untracked = _run_git(["git", "ls-files", "--others", "--exclude-standard"])
        for line in untracked.stdout.splitlines():
            if line.strip():
                changed.add(Path(line.strip()))

    return sorted(changed)


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


def _count_metrics(text: str | None) -> dict[str, int]:
    return {
        "allow_without_reason": _count_allow_without_reason(text),
        "undocumented_unsafe_blocks": _count_undocumented_unsafe_blocks(text),
        "pub_unsafe_fn_missing_safety_docs": _count_pub_unsafe_fn_missing_safety_docs(text),
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
        f"{totals['pub_unsafe_fn_missing_safety_docs_growth']:+d}"
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
                f"({growth['pub_unsafe_fn_missing_safety_docs']:+d})"
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
        changed_paths = _list_changed_paths(args.since_ref, args.head_ref)
    except RuntimeError as exc:
        report = {
            "command": "check_rust_best_practices",
            "timestamp": datetime.now().isoformat(),
            "ok": False,
            "error": str(exc),
        }
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print("# check_rust_best_practices\n")
            print(f"- ok: False\n- error: {report['error']}")
        return 2

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_rust = 0
    files_skipped_tests = 0
    totals_allow_growth = 0
    totals_unsafe_growth = 0
    totals_pub_unsafe_docs_growth = 0
    violations: list[dict] = []

    for path in changed_paths:
        if path.suffix != ".rs":
            files_skipped_non_rust += 1
            continue
        if _is_test_path(path):
            files_skipped_tests += 1
            continue

        files_considered += 1

        if args.since_ref:
            base_text = _read_text_from_ref(path, args.since_ref)
            current_text = _read_text_from_ref(path, args.head_ref)
        else:
            base_text = _read_text_from_ref(path, "HEAD")
            current_text = _read_text_from_worktree(path)

        base = _count_metrics(base_text)
        current = _count_metrics(current_text)
        growth = {
            "allow_without_reason": current["allow_without_reason"] - base["allow_without_reason"],
            "undocumented_unsafe_blocks": current["undocumented_unsafe_blocks"]
            - base["undocumented_unsafe_blocks"],
            "pub_unsafe_fn_missing_safety_docs": current["pub_unsafe_fn_missing_safety_docs"]
            - base["pub_unsafe_fn_missing_safety_docs"],
        }

        totals_allow_growth += growth["allow_without_reason"]
        totals_unsafe_growth += growth["undocumented_unsafe_blocks"]
        totals_pub_unsafe_docs_growth += growth["pub_unsafe_fn_missing_safety_docs"]

        if (
            growth["allow_without_reason"] > 0
            or growth["undocumented_unsafe_blocks"] > 0
            or growth["pub_unsafe_fn_missing_safety_docs"] > 0
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
            "allow_without_reason_growth": totals_allow_growth,
            "undocumented_unsafe_blocks_growth": totals_unsafe_growth,
            "pub_unsafe_fn_missing_safety_docs_growth": totals_pub_unsafe_docs_growth,
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
