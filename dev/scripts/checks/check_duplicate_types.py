#!/usr/bin/env python3
"""Detect duplicate Rust struct/enum type names across files."""

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
_collect_rust_files = import_attr("rust_guard_common", "collect_rust_files")
_normalize_changed_paths = import_attr(
    "rust_guard_common", "normalize_changed_rust_paths"
)
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

guard = GuardContext(REPO_ROOT)
SOURCE_ROOT = REPO_ROOT / "rust" / "src"
TYPE_DEF_RE = re.compile(
    r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:crate\s+)?(?:unsafe\s+)?(?:struct|enum)\s+([A-Za-z_][A-Za-z0-9_]*)\b",
    re.MULTILINE,
)

# Existing intentional duplicates are tracked here so the check stays non-regressive.
ALLOWLIST_DUPLICATES: dict[str, set[str]] = {
    "Args": {
        "rust/src/bin/latency_measurement.rs",
        "rust/src/bin/stt_file_benchmark.rs",
        "rust/src/bin/voice_benchmark.rs",
    },
    "ProgressBarFamily": {
        "rust/src/bin/voiceterm/theme/colors.rs",
        "rust/src/bin/voiceterm/theme/style_schema.rs",
    },
}

def _path_for_report(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()

def _extract_type_names(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = strip_cfg_test_blocks(text)
    return TYPE_DEF_RE.findall(text)

def _build_type_index(files: list[Path]) -> tuple[dict[str, set[str]], int]:
    index: dict[str, set[str]] = {}
    type_definitions = 0
    for path in files:
        rel = _path_for_report(path)
        names = _extract_type_names(path)
        type_definitions += len(names)
        for name in names:
            index.setdefault(name, set()).add(rel)
    return index, type_definitions

def _render_md(report: dict) -> str:
    lines = ["# check_duplicate_types", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- source_root: {report['source_root']}")
    lines.append(f"- include_tests: {report['include_tests']}")
    lines.append(f"- files_scanned: {report['files_scanned']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- type_definitions_found: {report['type_definitions_found']}")
    lines.append(f"- duplicate_names_detected: {report['duplicate_names_detected']}")
    lines.append(f"- allowlist_entries: {report['allowlist_entries']}")
    lines.append(f"- allowlist_entries_used: {report['allowlist_entries_used']}")
    lines.append(f"- stale_allowlist_entries: {len(report['stale_allowlist_entries'])}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    if report["stale_allowlist_entries"]:
        lines.append("")
        lines.append("## Warnings")
        for item in report["stale_allowlist_entries"]:
            lines.append(
                f"- stale allowlist entry `{item}` no longer matches an active duplicate"
            )

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for violation in report["violations"]:
            lines.append(
                f"- `{violation['type_name']}` appears in {violation['count']} files: "
                + ", ".join(f"`{path}`" for path in violation["paths"])
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
        help="Include test files in duplicate detection",
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
        return emit_runtime_error("check_duplicate_types", args.format, str(exc))

    files, skipped_tests = _collect_rust_files(
        SOURCE_ROOT,
        include_tests=args.include_tests,
    )
    type_index, type_definitions_found = _build_type_index(files)
    mode = "commit-range" if args.since_ref else "working-tree"
    changed_path_filter = (
        _normalize_changed_paths(changed_paths, include_tests=args.include_tests)
        if args.since_ref
        else None
    )

    duplicate_names = {
        type_name: sorted(paths)
        for type_name, paths in type_index.items()
        if len(paths) > 1
    }

    violations: list[dict] = []
    allowlist_used = 0
    active_duplicate_names = set(duplicate_names.keys())
    stale_allowlist_entries = sorted(
        entry for entry in ALLOWLIST_DUPLICATES if entry not in active_duplicate_names
    )

    for type_name, paths in sorted(duplicate_names.items()):
        path_set = set(paths)
        allowlisted = ALLOWLIST_DUPLICATES.get(type_name)
        if allowlisted is not None and path_set == allowlisted:
            allowlist_used += 1
            continue
        if changed_path_filter is not None and not (path_set & changed_path_filter):
            continue
        violations.append(
            {
                "type_name": type_name,
                "count": len(paths),
                "paths": paths,
            }
        )

    report = {
        "command": "check_duplicate_types",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "ok": len(violations) == 0,
        "source_root": _path_for_report(SOURCE_ROOT),
        "include_tests": args.include_tests,
        "files_scanned": len(files),
        "files_skipped_tests": skipped_tests,
        "type_definitions_found": type_definitions_found,
        "duplicate_names_detected": len(duplicate_names),
        "allowlist_entries": len(ALLOWLIST_DUPLICATES),
        "allowlist_entries_used": allowlist_used,
        "stale_allowlist_entries": stale_allowlist_entries,
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1

if __name__ == "__main__":
    sys.exit(main())
