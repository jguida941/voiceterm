#!/usr/bin/env python3
"""Guard against known Rust audit regression patterns across runtime sources."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from check_bootstrap import import_attr, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import import_attr, utc_timestamp

GuardContext = import_attr("rust_guard_common", "GuardContext")
list_changed_paths = import_attr("rust_guard_common", "list_changed_paths")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)
SOURCE_ROOT = REPO_ROOT / "rust" / "src"
SOURCE_ROOT_RELATIVE = SOURCE_ROOT.relative_to(REPO_ROOT)

PATTERNS = {
    "utf8_prefix_slice": re.compile(
        r"&\s*[A-Za-z_][A-Za-z0-9_]*\s*\[\s*\.\.\s*[A-Za-z_][A-Za-z0-9_]*\.len\(\)\.min\("
    ),
    "char_limit_truncate": re.compile(r"\.truncate\s*\(\s*INPUT_MAX_CHARS\s*\)"),
    "single_pass_secret_find": re.compile(
        r"if\s+let\s+Some\([^)]*\)\s*=\s*redacted\.find\("
    ),
    "deterministic_id_hash_suffix": re.compile(
        r"wrapping_mul\((?:2654435761|2246822519)\)"
    ),
    "lossy_vad_cast_i16": re.compile(r"\(\s*clamped\s*\*\s*32_768\.0\s*\)\s*as\s*i16"),
}


def _iter_rust_paths() -> list[Path]:
    if not SOURCE_ROOT.exists():
        return []
    paths: set[Path] = set()
    for path in SOURCE_ROOT.rglob("*.rs"):
        if "target" in path.parts:
            continue
        paths.add(path)
    return sorted(paths)


def _list_changed_paths(since_ref: str | None, head_ref: str) -> list[Path]:
    """Compatibility wrapper over shared changed-path helper."""
    return list_changed_paths(guard.run_git, since_ref, head_ref)


def _is_runtime_source_path(path: Path) -> bool:
    """Return True if *path* (repo-relative) is under SOURCE_ROOT."""
    try:
        path.relative_to(SOURCE_ROOT_RELATIVE)
        return True
    except ValueError:
        return False


def _count_metrics(text: str | None) -> dict[str, int]:
    if text is None:
        return {name: 0 for name in PATTERNS}
    return {name: len(pattern.findall(text)) for name, pattern in PATTERNS.items()}


def _has_positive_metrics(metrics: dict[str, int]) -> bool:
    return any(value > 0 for value in metrics.values())


def _render_md(report: dict) -> str:
    lines = ["# check_rust_audit_patterns", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- mode: {report['mode']}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
        lines.append(f"- head_ref: {report['head_ref']}")
    lines.append(f"- source_root: {report['source_root']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- violations: {len(report['violations'])}")
    lines.append(
        "- aggregate: "
        + ", ".join(f"{name}={count}" for name, count in report["totals"].items())
    )
    if report.get("stale_pattern_warning"):
        lines.append(f"- stale_pattern_warning: {report['stale_pattern_warning']}")
    if report.get("error"):
        lines.append(f"- error: {report['error']}")
    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: prefer UTF-8-safe prefix helpers, char-safe truncation, "
            "multi-occurrence redaction loops, non-deterministic ID suffixes, and "
            "explicit saturating float-to-i16 conversions."
        )
        for item in report["violations"]:
            flagged = ", ".join(
                f"{name}={count}"
                for name, count in item["metrics"].items()
                if count > 0
            )
            lines.append(f"- `{item['path']}`: {flagged}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument(
        "--head-ref", default="HEAD", help="Head ref (only used with --since-ref)"
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    violations: list[dict] = []
    totals = {name: 0 for name in PATTERNS}
    error: str | None = None
    stale_pattern_warning: str | None = None
    files_considered = 0
    mode = "commit-range" if args.since_ref else "working-tree"

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)

        if args.since_ref:
            changed_paths = _list_changed_paths(args.since_ref, args.head_ref)
        else:
            changed_paths = _list_changed_paths(None, "HEAD")

        for path in changed_paths:
            if not str(path).endswith(".rs"):
                continue
            if "target" in path.parts:
                continue
            if not _is_runtime_source_path(path):
                continue

            files_considered += 1

            if args.since_ref:
                current_text = guard.read_text_from_ref(path, args.head_ref)
            else:
                current_text = guard.read_text_from_worktree(path)

            metrics = _count_metrics(current_text)
            for name, value in metrics.items():
                totals[name] += value
            if _has_positive_metrics(metrics):
                violations.append(
                    {
                        "path": str(path),
                        "metrics": metrics,
                    }
                )

    except Exception as exc:
        error = str(exc)

    if not error and files_considered > 0 and all(v == 0 for v in totals.values()):
        file_noun = "file" if files_considered == 1 else "files"
        stale_pattern_warning = (
            f"all {len(PATTERNS)} audit patterns matched zero times across "
            f"{files_considered} {file_noun}; patterns may be stale or source "
            "may have been fully remediated"
        )

    source_root_label = (
        SOURCE_ROOT.relative_to(REPO_ROOT).as_posix()
        if SOURCE_ROOT.exists()
        else "missing"
    )

    report = {
        "command": "check_rust_audit_patterns",
        "timestamp": utc_timestamp(),
        "mode": mode if not error else "error",
        "since_ref": args.since_ref,
        "head_ref": args.head_ref if args.since_ref else None,
        "ok": len(violations) == 0 and error is None,
        "error": error,
        "stale_pattern_warning": stale_pattern_warning,
        "source_root": source_root_label,
        "files_considered": files_considered,
        "totals": totals,
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    if error is not None:
        return 2
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
