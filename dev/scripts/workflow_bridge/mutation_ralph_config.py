"""Config resolution helpers for the mutation Ralph workflow bridge."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Mapping

ALLOWED_EXECUTION_MODES = {"report-only", "plan-then-fix", "fix-only"}
ALLOWED_NOTIFY_MODES = {"summary-only", "summary-and-comment"}
ALLOWED_COMMENT_TARGETS = {"auto", "pr", "commit"}


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
        "max_attempts": _validate_positive_int(max_attempts, minimum=1, label="max attempts"),
        "poll_seconds": _validate_positive_int(poll_seconds, minimum=5, label="poll seconds"),
        "timeout_seconds": _validate_positive_int(timeout_seconds, minimum=60, label="timeout seconds"),
        "execution_mode": _validate_allowed(execution_mode, allowed=ALLOWED_EXECUTION_MODES, label="execution mode"),
        "threshold": _validate_threshold(threshold),
        "notify_mode": _validate_allowed(notify_mode, allowed=ALLOWED_NOTIFY_MODES, label="notify mode"),
        "comment_target": _validate_allowed(comment_target, allowed=ALLOWED_COMMENT_TARGETS, label="comment target"),
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


def resolve_config_command(args) -> int:
    event_name = args.event_name or os.getenv("EVENT_NAME", "")
    try:
        config = resolve_config_from_env(event_name=event_name, env=os.environ)
    except ValueError as exc:
        print(str(exc))
        return 1
    write_config_outputs(config, Path(args.github_output))
    return 0
