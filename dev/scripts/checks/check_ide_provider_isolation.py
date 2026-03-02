#!/usr/bin/env python3
"""Report mixed host/provider coupling references in runtime modules."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = REPO_ROOT / "rust" / "src" / "bin" / "voiceterm"

HOST_PATTERNS = (
    re.compile(r"\bTerminalHost\b"),
    re.compile(r"\bTerminalFamily\b"),
    re.compile(r"\bJetBrains\b"),
    re.compile(r"\bCursor\b"),
)
PROVIDER_PATTERNS = (
    re.compile(r"\bBackendFamily\b"),
    re.compile(r"\bProvider::"),
    re.compile(r"\bclaude\b", re.IGNORECASE),
    re.compile(r"\bcodex\b", re.IGNORECASE),
    re.compile(r"\bgemini\b", re.IGNORECASE),
)

ALLOWLISTED_MIXED_PATH_PREFIXES = (
    "rust/src/bin/voiceterm/writer/",
    "rust/src/bin/voiceterm/event_loop/",
    "rust/src/bin/voiceterm/runtime_compat.rs",
)
ALLOWLISTED_MIXED_PATHS = (
    "rust/src/bin/voiceterm/event_loop.rs",
    "rust/src/bin/voiceterm/terminal.rs",
)


def _iter_source_paths() -> list[Path]:
    if not SOURCE_ROOT.exists():
        return []
    paths: list[Path] = []
    for path in SOURCE_ROOT.rglob("*.rs"):
        if "target" in path.parts:
            continue
        paths.append(path)
    return sorted(paths)


def _is_allowlisted_mixed_path(relative_path: str) -> bool:
    return relative_path in ALLOWLISTED_MIXED_PATHS or any(
        relative_path == prefix or relative_path.startswith(prefix)
        for prefix in ALLOWLISTED_MIXED_PATH_PREFIXES
    )


def _strip_inline_comment(raw_line: str) -> str:
    return raw_line.split("//", 1)[0].strip()


def _scan_text(relative_path: str, text: str) -> dict:
    host_hits = 0
    provider_hits = 0
    mixed_line_numbers: list[int] = []
    statement_start: int | None = None
    statement_has_host_signal = False
    statement_has_provider_signal = False

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_inline_comment(raw_line)
        if not line:
            continue
        if line.startswith("use "):
            # Import lists often mention both host/provider symbols on one line.
            # Track coupling in executable statements instead.
            continue

        has_host_signal = any(pattern.search(line) for pattern in HOST_PATTERNS)
        has_provider_signal = any(pattern.search(line) for pattern in PROVIDER_PATTERNS)
        if has_host_signal:
            host_hits += 1
        if has_provider_signal:
            provider_hits += 1

        if statement_start is None:
            statement_start = lineno
            statement_has_host_signal = False
            statement_has_provider_signal = False
        statement_has_host_signal = statement_has_host_signal or has_host_signal
        statement_has_provider_signal = statement_has_provider_signal or has_provider_signal

        statement_ends = line.endswith(";") or line.endswith("{") or line.endswith("}")
        if not statement_ends:
            continue
        if statement_has_host_signal and statement_has_provider_signal:
            mixed_line_numbers.append(statement_start)
        statement_start = None
        statement_has_host_signal = False
        statement_has_provider_signal = False

    if (
        statement_start is not None
        and statement_has_host_signal
        and statement_has_provider_signal
    ):
        mixed_line_numbers.append(statement_start)

    return {
        "file": relative_path,
        "host_signal_lines": host_hits,
        "provider_signal_lines": provider_hits,
        "mixed_signal_lines": len(mixed_line_numbers),
        "mixed_line_numbers": mixed_line_numbers,
    }


def _render_md(report: dict) -> str:
    lines = ["# check_ide_provider_isolation", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- source_root: {report['source_root']}")
    lines.append(f"- files_scanned: {report['files_scanned']}")
    lines.append(f"- files_with_mixed_signals: {report['files_with_mixed_signals']}")
    lines.append(f"- unauthorized_files: {report['unauthorized_files']}")
    lines.append(
        "- allowlisted_prefixes: "
        + ", ".join(report["allowlisted_mixed_path_prefixes"])
    )
    if report["violations"]:
        lines.append("")
        lines.append("## Unauthorized Mixed Signals")
        for item in report["violations"][:30]:
            lines.append(
                f"- `{item['file']}`: mixed_signal_lines={item['mixed_signal_lines']} "
                f"(lines: {', '.join(str(v) for v in item['mixed_line_numbers'][:10])})"
            )
        remaining = len(report["violations"]) - 30
        if remaining > 0:
            lines.append(f"- ... and {remaining} more")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fail-on-violations", action="store_true")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    source_paths = _iter_source_paths()
    per_file: list[dict] = []
    mixed_files: list[dict] = []
    violations: list[dict] = []

    for path in source_paths:
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        result = _scan_text(relative_path, text)
        per_file.append(result)
        if result["mixed_signal_lines"] <= 0:
            continue
        mixed_files.append(result)
        if not _is_allowlisted_mixed_path(relative_path):
            violations.append(result)

    blocking_mode = args.fail_on_violations
    ok = not blocking_mode or not violations
    report = {
        "command": "check_ide_provider_isolation",
        "timestamp": datetime.now().isoformat(),
        "ok": ok,
        "mode": "blocking" if blocking_mode else "report-only",
        "source_root": SOURCE_ROOT.relative_to(REPO_ROOT).as_posix(),
        "files_scanned": len(per_file),
        "files_with_mixed_signals": len(mixed_files),
        "unauthorized_files": len(violations),
        "allowlisted_mixed_path_prefixes": list(ALLOWLISTED_MIXED_PATH_PREFIXES),
        "allowlisted_mixed_paths": list(ALLOWLISTED_MIXED_PATHS),
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
