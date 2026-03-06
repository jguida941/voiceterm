#!/usr/bin/env python3
"""Run cargo clippy and emit warning summary for CI badge updates."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def count_warning_messages(lines: Iterable[str]) -> int:
    """Count compiler-message entries reported at warning level."""
    warning_count = 0
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
        message = payload.get("message") or {}
        if str(message.get("level", "")).lower() == "warning":
            warning_count += 1
    return warning_count


def collect_warning_lint_counts(lines: Iterable[str]) -> dict[str, int]:
    """Collect warning counts keyed by lint code (`clippy::<lint>` etc.)."""
    lint_counts: dict[str, int] = {}
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
        message = payload.get("message") or {}
        if str(message.get("level", "")).lower() != "warning":
            continue
        code_payload = message.get("code") or {}
        lint = code_payload.get("code")
        if not isinstance(lint, str) or not lint:
            continue
        lint_counts[lint] = lint_counts.get(lint, 0) + 1
    return lint_counts


def build_summary(exit_code: int, warning_count: int) -> dict[str, int | str]:
    """Build normalized status payload for downstream badge rendering."""
    status = "success"
    if exit_code != 0 or warning_count != 0:
        status = "failure"
    return {
        "warnings": warning_count,
        "exit_code": exit_code,
        "status": status,
    }


def build_clippy_command(*, deny_warnings: bool) -> list[str]:
    """Build the cargo clippy command used for JSON lint collection."""
    command = [
        "cargo",
        "clippy",
        "--workspace",
        "--all-features",
        "--message-format=json",
    ]
    if deny_warnings:
        command.extend(["--", "-D", "warnings"])
    return command


def run_clippy(
    working_directory: Path,
    *,
    deny_warnings: bool,
    quiet_json_stream: bool,
) -> tuple[list[str], int]:
    """Run cargo clippy in JSON mode and optionally stream output to stdout."""
    command = build_clippy_command(deny_warnings=deny_warnings)
    process = subprocess.Popen(
        command,
        cwd=str(working_directory),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    captured_lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        if not quiet_json_stream:
            sys.stdout.write(line)
        captured_lines.append(line)
    exit_code = process.wait()
    return captured_lines, exit_code


def write_summary_json(path: Path, summary: dict[str, int | str]) -> None:
    """Write machine-readable summary payload."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def write_lints_json(path: Path, lint_counts: dict[str, int]) -> None:
    """Write machine-readable lint histogram payload."""
    payload = {
        "schema_version": 1,
        "lints": dict(sorted(lint_counts.items())),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_github_output(path: Path, summary: dict[str, int | str]) -> None:
    """Write step outputs for GitHub Actions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"warnings={summary['warnings']}\n")
        handle.write(f"status={summary['status']}\n")
        handle.write(f"exit_code={summary['exit_code']}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect clippy warning count and status for CI badge updates."
    )
    parser.add_argument(
        "--working-directory",
        default="rust",
        help="Directory where cargo clippy should run",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional path for summary JSON output",
    )
    parser.add_argument(
        "--github-output",
        default="",
        help="Optional path to append GitHub Actions step outputs",
    )
    parser.add_argument(
        "--output-lints-json",
        default="",
        help="Optional path for lint-code histogram JSON output",
    )
    parser.add_argument(
        "--deny-warnings",
        action="store_true",
        help="Run clippy with `-D warnings` for strict failure behavior",
    )
    parser.add_argument(
        "--quiet-json-stream",
        action="store_true",
        help="Do not stream JSON compiler output to stdout",
    )
    parser.add_argument(
        "--propagate-exit-code",
        action="store_true",
        help="Exit with cargo clippy status code instead of always returning 0",
    )
    args = parser.parse_args()

    working_directory = Path(args.working_directory)
    try:
        lines, exit_code = run_clippy(
            working_directory,
            deny_warnings=args.deny_warnings,
            quiet_json_stream=args.quiet_json_stream,
        )
    except OSError as exc:
        print(f"Failed to execute cargo clippy: {exc}", file=sys.stderr)
        lines = []
        exit_code = 127

    warning_count = count_warning_messages(lines)
    lint_counts = collect_warning_lint_counts(lines)
    summary = build_summary(exit_code, warning_count)

    if args.output_json:
        write_summary_json(Path(args.output_json), summary)
    if args.output_lints_json:
        write_lints_json(Path(args.output_lints_json), lint_counts)
    if args.github_output:
        write_github_output(Path(args.github_output), summary)

    print(
        "Clippy summary: status={status} warnings={warnings} exit_code={exit_code}".format(
            status=summary["status"],
            warnings=summary["warnings"],
            exit_code=summary["exit_code"],
        )
    )
    if args.propagate_exit_code:
        return int(exit_code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
