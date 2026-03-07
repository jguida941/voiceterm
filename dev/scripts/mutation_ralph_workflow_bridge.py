#!/usr/bin/env python3
"""Workflow helper for Mutation Ralph loop config resolution and report parsing."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Mapping

ALLOWED_EXECUTION_MODES = {"report-only", "plan-then-fix", "fix-only"}
ALLOWED_NOTIFY_MODES = {"summary-only", "summary-and-comment"}
ALLOWED_COMMENT_TARGETS = {"auto", "pr", "commit"}
SYSTEM_TMPDIR = Path(tempfile.gettempdir())


def _tmp_path(filename: str) -> str:
    return str(SYSTEM_TMPDIR / filename)


def _validate_positive_int(raw_value: str, *, minimum: int, label: str) -> str:
    if not re.fullmatch(r"[0-9]+", raw_value or ""):
        raise ValueError(f"Invalid {label}: {raw_value}")
    value = int(raw_value)
    if value < minimum:
        raise ValueError(f"Invalid {label}: {raw_value}")
    return raw_value


def _validate_threshold(raw_value: str) -> str:
    try:
        threshold = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid threshold: {raw_value}") from exc
    if threshold <= 0 or threshold > 1:
        raise ValueError(f"Invalid threshold: {raw_value}")
    return raw_value


def _validate_allowed(raw_value: str, *, allowed: set[str], label: str) -> str:
    if raw_value not in allowed:
        raise ValueError(f"Invalid {label}: {raw_value}")
    return raw_value


def resolve_config_from_env(event_name: str, env: Mapping[str, str]) -> dict[str, str]:
    dispatch_mode = event_name == "workflow_dispatch"
    if dispatch_mode:
        branch = env.get("DISPATCH_BRANCH", "")
        max_attempts = env.get("DISPATCH_MAX_ATTEMPTS", "") or "3"
        poll_seconds = env.get("DISPATCH_POLL_SECONDS", "") or "20"
        timeout_seconds = env.get("DISPATCH_TIMEOUT_SECONDS", "") or "1800"
        execution_mode = env.get("DISPATCH_EXECUTION_MODE", "") or "report-only"
        threshold = env.get("DISPATCH_THRESHOLD", "") or "0.80"
        notify_mode = env.get("DISPATCH_NOTIFY_MODE", "") or "summary-only"
        comment_target = env.get("DISPATCH_COMMENT_TARGET", "") or "auto"
        comment_pr_number = env.get("DISPATCH_COMMENT_PR_NUMBER", "")
        fix_command = env.get("DISPATCH_FIX_COMMAND", "")
    else:
        branch = env.get("WORKFLOW_BRANCH", "")
        max_attempts = env.get("LOOP_MAX_ATTEMPTS", "") or "3"
        poll_seconds = env.get("LOOP_POLL_SECONDS", "") or "20"
        timeout_seconds = env.get("LOOP_TIMEOUT_SECONDS", "") or "1800"
        execution_mode = env.get("LOOP_EXECUTION_MODE", "") or "report-only"
        threshold = env.get("LOOP_THRESHOLD", "") or "0.80"
        notify_mode = env.get("LOOP_NOTIFY_MODE", "") or "summary-only"
        comment_target = env.get("LOOP_COMMENT_TARGET", "") or "auto"
        comment_pr_number = env.get("LOOP_COMMENT_PR_NUMBER", "")
        fix_command = env.get("LOOP_FIX_COMMAND", "")

    if not branch:
        raise ValueError("Branch is required.")

    return {
        "branch": branch,
        "max_attempts": _validate_positive_int(
            max_attempts, minimum=1, label="max attempts"
        ),
        "poll_seconds": _validate_positive_int(
            poll_seconds, minimum=5, label="poll seconds"
        ),
        "timeout_seconds": _validate_positive_int(
            timeout_seconds, minimum=60, label="timeout seconds"
        ),
        "execution_mode": _validate_allowed(
            execution_mode,
            allowed=ALLOWED_EXECUTION_MODES,
            label="execution mode",
        ),
        "threshold": _validate_threshold(threshold),
        "notify_mode": _validate_allowed(
            notify_mode,
            allowed=ALLOWED_NOTIFY_MODES,
            label="notify mode",
        ),
        "comment_target": _validate_allowed(
            comment_target,
            allowed=ALLOWED_COMMENT_TARGETS,
            label="comment target",
        ),
        "comment_pr_number": comment_pr_number,
        "fix_command": fix_command,
    }


def write_config_outputs(config: Mapping[str, str], output_path: Path) -> None:
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(f"branch={config['branch']}\n")
        handle.write(f"max_attempts={config['max_attempts']}\n")
        handle.write(f"poll_seconds={config['poll_seconds']}\n")
        handle.write(f"timeout_seconds={config['timeout_seconds']}\n")
        handle.write(f"execution_mode={config['execution_mode']}\n")
        handle.write(f"threshold={config['threshold']}\n")
        handle.write(f"notify_mode={config['notify_mode']}\n")
        handle.write(f"comment_target={config['comment_target']}\n")
        handle.write(f"comment_pr_number={config['comment_pr_number']}\n")
        handle.write("fix_command<<EOF\n")
        handle.write(f"{config['fix_command']}\n")
        handle.write("EOF\n")


def extract_failure_reason(json_path: Path) -> str:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("reason") or "").strip()


def build_loop_command(args: argparse.Namespace) -> list[str]:
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


def _resolve_config_command(args: argparse.Namespace) -> int:
    event_name = args.event_name or os.getenv("EVENT_NAME", "")
    try:
        config = resolve_config_from_env(event_name=event_name, env=os.environ)
    except ValueError as exc:
        print(str(exc))
        return 1
    write_config_outputs(config, Path(args.github_output))
    return 0


def _extract_failure_reason_command(args: argparse.Namespace) -> int:
    try:
        reason = extract_failure_reason(Path(args.input))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Failed to read failure reason: {exc}")
        return 1
    print(reason)
    return 0


def _run_loop_command(args: argparse.Namespace) -> int:
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
            print(
                "::warning::Mutation Ralph loop report-only mode skipped hard-fail "
                "(artifact download failed)."
            )
            return 0
    return result.returncode


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    resolve = subcommands.add_parser(
        "resolve-config",
        help="Resolve and validate workflow config, then append outputs.",
    )
    resolve.add_argument("--github-output", required=True)
    resolve.add_argument(
        "--event-name",
        default="",
        help="Optional explicit event name override (defaults to EVENT_NAME env var).",
    )

    extract = subcommands.add_parser(
        "extract-failure-reason",
        help="Print the stripped `reason` field from a loop JSON payload.",
    )
    extract.add_argument("--input", required=True)

    run_loop = subcommands.add_parser(
        "run-loop",
        help="Execute the mutation loop command with workflow soft-fail policy.",
    )
    run_loop.add_argument("--target-repo", required=True)
    run_loop.add_argument("--target-branch", required=True)
    run_loop.add_argument("--max-attempts", required=True)
    run_loop.add_argument("--poll-seconds", required=True)
    run_loop.add_argument("--timeout-seconds", required=True)
    run_loop.add_argument("--mode", required=True)
    run_loop.add_argument("--threshold", required=True)
    run_loop.add_argument("--notify-mode", required=True)
    run_loop.add_argument("--comment-target", required=True)
    run_loop.add_argument("--comment-pr-number", default="")
    run_loop.add_argument("--fix-command", default="")
    run_loop.add_argument(
        "--json-output", default=_tmp_path("mutation-ralph-loop.json")
    )
    run_loop.add_argument("--output", default=_tmp_path("mutation-ralph-loop.md"))

    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.command == "resolve-config":
        return _resolve_config_command(args)
    if args.command == "extract-failure-reason":
        return _extract_failure_reason_command(args)
    if args.command == "run-loop":
        return _run_loop_command(args)
    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
