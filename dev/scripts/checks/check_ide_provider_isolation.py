#!/usr/bin/env python3
"""Report mixed host/provider coupling references in runtime and IPC modules."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from ide_provider_isolation_core import (
    ALLOWLISTED_FILE_SIGNAL_PATHS,
    ALLOWLISTED_MIXED_PATH_PREFIXES,
    ALLOWLISTED_MIXED_PATHS,
    REPO_ROOT,
    SOURCE_ROOTS,
    _is_allowlisted_file_signal_path,
    _is_allowlisted_mixed_path,
    _is_test_source_path,
    _iter_source_paths,
    _scan_text,
)


def _render_md(report: dict) -> str:
    lines = ["# check_ide_provider_isolation", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- source_roots: {', '.join(report['source_roots'])}")
    lines.append(f"- files_scanned: {report['files_scanned']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- files_with_mixed_signals: {report['files_with_mixed_signals']}")
    lines.append(
        f"- files_with_file_signal_coupling: {report['files_with_file_signal_coupling']}"
    )
    lines.append(f"- unauthorized_files: {report['unauthorized_files']}")
    lines.append(
        "- allowlisted_prefixes: "
        + ", ".join(report["allowlisted_mixed_path_prefixes"])
    )
    if report["violations"]:
        lines.append("")
        lines.append("## Unauthorized Mixed Signals")
        for item in report["violations"][:30]:
            violation_types = ", ".join(item.get("violation_types", []))
            lines.append(
                f"- `{item['file']}`: types=[{violation_types}] "
                f"mixed_signal_lines={item['mixed_signal_lines']} "
                f"file_signal_coupling={item.get('file_signal_coupling', False)} "
                f"(lines: {', '.join(str(v) for v in item['mixed_line_numbers'][:10])})"
            )
        remaining = len(report["violations"]) - 30
        if remaining > 0:
            lines.append(f"- ... and {remaining} more")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Disable blocking mode and emit report-only results.",
    )
    parser.add_argument(
        "--fail-on-violations",
        action="store_true",
        help="Deprecated alias retained for compatibility (blocking is now default).",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    source_paths = _iter_source_paths()
    per_file: list[dict] = []
    mixed_files: list[dict] = []
    file_signal_files: list[dict] = []
    violations: list[dict] = []
    files_skipped_tests = 0

    for path in source_paths:
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        if _is_test_source_path(relative_path):
            files_skipped_tests += 1
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        result = _scan_text(relative_path, text)
        per_file.append(result)
        mixed_signal_lines = int(result.get("mixed_signal_lines", 0))
        file_signal_coupling = bool(result.get("file_signal_coupling", False))
        if mixed_signal_lines > 0:
            mixed_files.append(result)
        if file_signal_coupling:
            file_signal_files.append(result)

        violation_types: list[str] = []
        if mixed_signal_lines > 0 and not _is_allowlisted_mixed_path(relative_path):
            violation_types.append("same-statement")
        if file_signal_coupling and not _is_allowlisted_file_signal_path(relative_path):
            violation_types.append("file-scope")
        if violation_types:
            violation = dict(result)
            violation["violation_types"] = violation_types
            violations.append(violation)

    blocking_mode = args.fail_on_violations or not args.report_only
    source_roots = [path.relative_to(REPO_ROOT).as_posix() for path in SOURCE_ROOTS]
    ok = not blocking_mode or not violations
    report = {
        "command": "check_ide_provider_isolation",
        "timestamp": datetime.now().isoformat(),
        "ok": ok,
        "mode": "blocking" if blocking_mode else "report-only",
        "source_root": source_roots[0] if source_roots else "",
        "source_roots": source_roots,
        "files_scanned": len(per_file),
        "files_skipped_tests": files_skipped_tests,
        "files_with_mixed_signals": len(mixed_files),
        "files_with_file_signal_coupling": len(file_signal_files),
        "unauthorized_files": len(violations),
        "allowlisted_mixed_path_prefixes": list(ALLOWLISTED_MIXED_PATH_PREFIXES),
        "allowlisted_mixed_paths": list(ALLOWLISTED_MIXED_PATHS),
        "allowlisted_file_signal_paths": list(ALLOWLISTED_FILE_SIGNAL_PATHS),
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
