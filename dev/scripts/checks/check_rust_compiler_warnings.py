#!/usr/bin/env python3
"""Fail when changed Rust source files emit compiler warnings."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from check_bootstrap import emit_runtime_error, import_attr, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import (
        emit_runtime_error,
        import_attr,
        utc_timestamp,
    )

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")
_is_test_path = import_attr("rust_guard_common", "is_test_path")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)
DEFAULT_WORKING_DIRECTORY = Path("rust")
DEFAULT_CARGO_COMMAND = [
    "cargo",
    "test",
    "--workspace",
    "--all-features",
    "--all-targets",
    "--no-run",
    "--message-format=json",
]


def _list_all_rust_paths(*, include_tests: bool) -> set[str]:
    tracked = guard.run_git(["git", "ls-files"]).stdout.splitlines()
    untracked = guard.run_git(
        ["git", "ls-files", "--others", "--exclude-standard"]
    ).stdout.splitlines()
    normalized: set[str] = set()
    for raw in [*tracked, *untracked]:
        path = Path(raw.strip())
        if path.suffix != ".rs" or not path.as_posix().startswith("rust/"):
            continue
        if not include_tests and _is_test_path(path):
            continue
        normalized.add(path.as_posix())
    return normalized


def _normalize_target_paths(
    changed_paths: list[Path],
    *,
    include_tests: bool,
) -> set[str]:
    normalized: set[str] = set()
    for path in changed_paths:
        if path.suffix != ".rs" or not path.as_posix().startswith("rust/"):
            continue
        if not include_tests and _is_test_path(path):
            continue
        normalized.add(path.as_posix())
    return normalized


def _normalize_warning_path(file_name: str, working_directory: Path) -> str | None:
    raw = file_name.strip()
    if not raw:
        return None
    path = Path(raw)
    if path.suffix != ".rs":
        return None
    if path.is_absolute():
        try:
            return path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return None
    if raw.startswith("rust/"):
        return raw
    working_prefix = working_directory.as_posix().strip("/")
    if working_prefix:
        return f"{working_prefix}/{raw}"
    return raw


def _warning_path_and_line(message: dict, working_directory: Path) -> tuple[str | None, int | None]:
    spans = message.get("spans")
    if not isinstance(spans, list):
        return None, None

    fallback_path: str | None = None
    fallback_line: int | None = None
    for span in spans:
        if not isinstance(span, dict):
            continue
        file_name = span.get("file_name")
        if not isinstance(file_name, str):
            continue
        normalized = _normalize_warning_path(file_name, working_directory)
        if normalized is None:
            continue
        line_start = span.get("line_start")
        line_number = line_start if isinstance(line_start, int) else None
        if fallback_path is None:
            fallback_path = normalized
            fallback_line = line_number
        if span.get("is_primary"):
            return normalized, line_number
    return fallback_path, fallback_line


def collect_warning_records(
    lines: list[str],
    *,
    working_directory: Path,
    target_paths: set[str],
) -> list[dict[str, object]]:
    warnings: list[dict[str, object]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if payload.get("reason") != "compiler-message":
            continue
        message = payload.get("message")
        if not isinstance(message, dict):
            continue
        if str(message.get("level", "")).lower() != "warning":
            continue
        warning_path, line_number = _warning_path_and_line(message, working_directory)
        if warning_path is None or warning_path not in target_paths:
            continue
        code_payload = message.get("code")
        code = None
        if isinstance(code_payload, dict):
            code_value = code_payload.get("code")
            if isinstance(code_value, str) and code_value:
                code = code_value
        text = message.get("message")
        warnings.append(
            {
                "path": warning_path,
                "line": line_number,
                "code": code or "warning",
                "message": text if isinstance(text, str) else "compiler warning",
            }
        )
    warnings.sort(
        key=lambda item: (
            str(item["path"]),
            int(item["line"] or 0),
            str(item["code"]),
            str(item["message"]),
        )
    )
    return warnings


def run_cargo_warning_scan(working_directory: Path) -> tuple[list[str], int, list[str]]:
    process = subprocess.Popen(
        DEFAULT_CARGO_COMMAND,
        cwd=str(REPO_ROOT / working_directory),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    captured_lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        captured_lines.append(line)
    return captured_lines, process.wait(), list(DEFAULT_CARGO_COMMAND)


def _render_md(report: dict) -> str:
    lines = ["# check_rust_compiler_warnings", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- warnings: {len(report['warnings'])}")
    lines.append(f"- cargo_exit_code: {report['cargo_exit_code']}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")
    lines.append(f"- working_directory: {report['working_directory']}")
    lines.append(f"- input_jsonl: {report['input_jsonl'] or 'none'}")
    if report.get("error"):
        lines.append(f"- error: {report['error']}")
    if report["warnings"]:
        lines.append("")
        lines.append("## Warnings")
        for item in report["warnings"]:
            location = item["path"]
            if item.get("line"):
                location = f"{location}:{item['line']}"
            lines.append(f"- `{location}` `{item['code']}` {item['message']}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--absolute",
        action="store_true",
        help="Scan all tracked/untracked Rust files instead of only changed files.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test-only Rust files in the warning target set.",
    )
    parser.add_argument("--since-ref", help="Compare changed files against this git ref.")
    parser.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref used with --since-ref comparisons.",
    )
    parser.add_argument(
        "--working-directory",
        default=DEFAULT_WORKING_DIRECTORY.as_posix(),
        help="Repo-relative cargo working directory.",
    )
    parser.add_argument(
        "--input-jsonl",
        default="",
        help="Optional pre-recorded cargo JSON lines file for testing or offline review.",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.absolute and args.since_ref:
        return emit_runtime_error(
            "check_rust_compiler_warnings",
            args.format,
            "--absolute cannot be combined with --since-ref/--head-ref",
        )

    try:
        if args.absolute:
            target_paths = _list_all_rust_paths(include_tests=args.include_tests)
            files_changed = len(target_paths)
        else:
            if args.since_ref:
                guard.validate_ref(args.since_ref)
                guard.validate_ref(args.head_ref)
            changed_paths, _base_map = list_changed_paths_with_base_map(
                guard.run_git,
                args.since_ref,
                args.head_ref,
            )
            files_changed = len(changed_paths)
            target_paths = _normalize_target_paths(
                changed_paths,
                include_tests=args.include_tests,
            )
    except RuntimeError as exc:
        return emit_runtime_error(
            "check_rust_compiler_warnings",
            args.format,
            str(exc),
        )

    mode = (
        "absolute"
        if args.absolute
        else ("commit-range" if args.since_ref else "working-tree")
    )
    working_directory = Path(args.working_directory)
    report = {
        "command": "check_rust_compiler_warnings",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "ok": True,
        "files_changed": files_changed,
        "files_considered": len(target_paths),
        "cargo_exit_code": 0,
        "working_directory": working_directory.as_posix(),
        "input_jsonl": args.input_jsonl,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "warnings": [],
    }

    if not target_paths:
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print(_render_md(report))
        return 0

    try:
        if args.input_jsonl:
            lines = Path(args.input_jsonl).read_text(encoding="utf-8").splitlines(True)
            cargo_exit_code = 0
        else:
            lines, cargo_exit_code, _command = run_cargo_warning_scan(working_directory)
        warnings = collect_warning_records(
            lines,
            working_directory=working_directory,
            target_paths=target_paths,
        )
    except OSError as exc:
        return emit_runtime_error(
            "check_rust_compiler_warnings",
            args.format,
            str(exc),
        )

    report["cargo_exit_code"] = cargo_exit_code
    report["warnings"] = warnings
    report["ok"] = cargo_exit_code == 0 and not warnings
    if cargo_exit_code != 0:
        report["error"] = "cargo warning scan failed"

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
