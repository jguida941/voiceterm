"""Loop helpers for the mutation Ralph workflow bridge."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

SYSTEM_TMPDIR = Path(tempfile.gettempdir())


def extract_failure_reason(json_path: Path) -> str:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("reason") or "").strip()


def build_loop_command(args) -> list[str]:
    command = [
        "python3",
        "dev/scripts/devctl.py",
        "mutation-loop",
        "--repo",
        args.target_repo,
        "--branch",
        args.target_branch,
        "--workflow",
        "Mutation Testing",
        "--max-attempts",
        args.max_attempts,
        "--poll-seconds",
        args.poll_seconds,
        "--timeout-seconds",
        args.timeout_seconds,
        "--mode",
        args.mode,
        "--threshold",
        args.threshold,
        "--notify",
        args.notify_mode,
        "--comment-target",
        args.comment_target,
        "--emit-bundle",
        "--bundle-dir",
        str(SYSTEM_TMPDIR),
        "--bundle-prefix",
        "mutation-ralph-loop",
        "--json-output",
        args.json_output,
        "--format",
        "md",
        "--output",
        args.output,
    ]
    if args.comment_pr_number:
        command.extend(["--comment-pr-number", args.comment_pr_number])
    if args.mode != "report-only" and args.fix_command:
        command.extend(["--fix-command", args.fix_command])
    return command


def extract_failure_reason_command(args) -> int:
    try:
        reason = extract_failure_reason(Path(args.input))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Failed to read failure reason: {exc}")
        return 1
    print(reason)
    return 0


def run_loop_command(args) -> int:
    command = build_loop_command(args)
    try:
        result = subprocess.run(command, check=False)
    except OSError as exc:
        print(f"Failed to execute mutation loop command: {exc}")
        return 1
    if result.returncode == 0:
        return 0

    report_path = Path(args.json_output)
    if args.mode == "report-only" and report_path.is_file():
        try:
            reason = extract_failure_reason(report_path)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"Failed to read failure reason: {exc}")
            return result.returncode
        if reason == "artifact download failed":
            print("::warning::Mutation Ralph loop report-only mode skipped hard-fail (artifact download failed).")
            return 0
    return result.returncode
