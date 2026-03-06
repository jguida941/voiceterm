"""CodeRabbit Ralph workflow configuration resolution helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

from .common import (
    ALLOWED_COMMENT_TARGETS,
    ALLOWED_LOOP_MODES,
    ALLOWED_NOTIFY_MODES,
    append_multiline_output,
    append_output,
    validate_allowed,
    validate_positive_int,
)


def resolve_ralph_config_from_env(
    *, event_name: str, env: Mapping[str, str]
) -> dict[str, str]:
    """Resolve ralph-loop settings for dispatch and workflow-run triggers."""
    if event_name == "workflow_dispatch":
        branch = env.get("DISPATCH_BRANCH", "")
        max_attempts = env.get("DISPATCH_MAX_ATTEMPTS", "") or "3"
        poll_seconds = env.get("DISPATCH_POLL_SECONDS", "") or "20"
        timeout_seconds = env.get("DISPATCH_TIMEOUT_SECONDS", "") or "1800"
        execution_mode = env.get("DISPATCH_EXECUTION_MODE", "") or "plan-then-fix"
        notify_mode = env.get("DISPATCH_NOTIFY_MODE", "") or "summary-and-comment"
        comment_target = env.get("DISPATCH_COMMENT_TARGET", "") or "auto"
        comment_pr_number = env.get("DISPATCH_COMMENT_PR_NUMBER", "")
        source_event = "workflow_dispatch"
        source_run_id = ""
        source_run_sha = ""
        fix_command = env.get("DISPATCH_FIX_COMMAND", "")
    else:
        branch = env.get("WORKFLOW_BRANCH", "")
        max_attempts = env.get("LOOP_MAX_ATTEMPTS", "") or "3"
        poll_seconds = env.get("LOOP_POLL_SECONDS", "") or "20"
        timeout_seconds = env.get("LOOP_TIMEOUT_SECONDS", "") or "1800"
        execution_mode = env.get("LOOP_EXECUTION_MODE", "") or "plan-then-fix"
        notify_mode = env.get("LOOP_NOTIFY_MODE", "") or "summary-and-comment"
        comment_target = env.get("LOOP_COMMENT_TARGET", "") or "auto"
        comment_pr_number = env.get("LOOP_COMMENT_PR_NUMBER", "")
        source_event = "workflow_run"
        source_run_id = env.get("WORKFLOW_RUN_ID", "")
        source_run_sha = env.get("WORKFLOW_HEAD_SHA", "")
        fix_command = env.get("LOOP_FIX_COMMAND", "") or (
            "python3 dev/scripts/devctl.py check --profile ci"
        )

    if not branch:
        raise ValueError("Branch is required.")
    if source_event == "workflow_run":
        if not re.fullmatch(r"[0-9]+", source_run_id or ""):
            raise ValueError("workflow_run source requires numeric run id")
        if not source_run_sha:
            raise ValueError("workflow_run source requires head sha")

    return {
        "branch": branch,
        "max_attempts": validate_positive_int(
            max_attempts,
            minimum=1,
            message=f"Invalid max attempts: {max_attempts}",
        ),
        "poll_seconds": validate_positive_int(
            poll_seconds,
            minimum=5,
            message=f"Invalid poll seconds: {poll_seconds}",
        ),
        "timeout_seconds": validate_positive_int(
            timeout_seconds,
            minimum=60,
            message=f"Invalid timeout seconds: {timeout_seconds}",
        ),
        "execution_mode": validate_allowed(
            execution_mode,
            allowed=ALLOWED_LOOP_MODES,
            message=f"Invalid execution mode: {execution_mode}",
        ),
        "notify_mode": validate_allowed(
            notify_mode,
            allowed=ALLOWED_NOTIFY_MODES,
            message=f"Invalid notify mode: {notify_mode}",
        ),
        "comment_target": validate_allowed(
            comment_target,
            allowed=ALLOWED_COMMENT_TARGETS,
            message=f"Invalid comment target: {comment_target}",
        ),
        "comment_pr_number": comment_pr_number,
        "source_event": source_event,
        "source_run_id": source_run_id,
        "source_run_sha": source_run_sha,
        "fix_command": fix_command,
    }


def write_ralph_config_outputs(config: Mapping[str, str], output_path: Path) -> None:
    """Write resolved ralph-loop settings to GitHub output format."""
    append_output(
        output_path,
        [
            ("branch", config["branch"]),
            ("max_attempts", config["max_attempts"]),
            ("poll_seconds", config["poll_seconds"]),
            ("timeout_seconds", config["timeout_seconds"]),
            ("execution_mode", config["execution_mode"]),
            ("notify_mode", config["notify_mode"]),
            ("comment_target", config["comment_target"]),
            ("comment_pr_number", config["comment_pr_number"]),
            ("source_event", config["source_event"]),
            ("source_run_id", config["source_run_id"]),
            ("source_run_sha", config["source_run_sha"]),
        ],
    )
    append_multiline_output(output_path, "fix_command", config["fix_command"])
