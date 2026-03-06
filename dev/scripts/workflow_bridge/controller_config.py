"""Controller workflow configuration resolution helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .common import (
    append_multiline_output,
    append_output,
    validate_decimal_hours,
    validate_positive_int,
)


def resolve_controller_config_from_env(
    *, event_name: str, env: Mapping[str, str]
) -> dict[str, str]:
    """Resolve controller inputs for dispatch or scheduled workflow runs."""
    if event_name == "workflow_dispatch":
        plan_id = env.get("INPUT_PLAN_ID", "")
        branch_base = env.get("INPUT_BRANCH_BASE", "") or "develop"
        mode = env.get("INPUT_MODE", "") or env.get("DEFAULT_MODE", "")
        max_rounds = env.get("INPUT_MAX_ROUNDS", "") or env.get("DEFAULT_MAX_ROUNDS", "")
        max_hours = env.get("INPUT_MAX_HOURS", "") or env.get("DEFAULT_MAX_HOURS", "")
        max_tasks = env.get("INPUT_MAX_TASKS", "") or env.get("DEFAULT_MAX_TASKS", "")
        checkpoint_every = env.get("INPUT_CHECKPOINT_EVERY", "") or env.get(
            "DEFAULT_CHECKPOINT_EVERY", ""
        )
        loop_max_attempts = env.get("INPUT_LOOP_MAX_ATTEMPTS", "") or env.get(
            "DEFAULT_LOOP_MAX_ATTEMPTS", ""
        )
        notify_mode = env.get("INPUT_NOTIFY_MODE", "") or env.get("DEFAULT_NOTIFY_MODE", "")
        comment_target = env.get("INPUT_COMMENT_TARGET", "") or env.get(
            "DEFAULT_COMMENT_TARGET", ""
        )
        comment_pr_number = env.get("INPUT_COMMENT_PR_NUMBER", "")
        allow_auto_send = env.get("INPUT_ALLOW_AUTO_SEND", "")
        fix_command = env.get("INPUT_FIX_COMMAND", "")
    else:
        plan_id = "scheduled-autonomy"
        branch_base = "develop"
        mode = env.get("DEFAULT_MODE", "")
        max_rounds = env.get("DEFAULT_MAX_ROUNDS", "")
        max_hours = env.get("DEFAULT_MAX_HOURS", "")
        max_tasks = env.get("DEFAULT_MAX_TASKS", "")
        checkpoint_every = env.get("DEFAULT_CHECKPOINT_EVERY", "")
        loop_max_attempts = env.get("DEFAULT_LOOP_MAX_ATTEMPTS", "")
        notify_mode = env.get("DEFAULT_NOTIFY_MODE", "")
        comment_target = env.get("DEFAULT_COMMENT_TARGET", "")
        comment_pr_number = ""
        allow_auto_send = "false"
        fix_command = ""

    if not plan_id:
        raise ValueError("plan_id is required")
    if not branch_base:
        raise ValueError("branch_base is required")

    return {
        "plan_id": plan_id,
        "branch_base": branch_base,
        "mode": mode,
        "max_rounds": validate_positive_int(
            max_rounds,
            minimum=1,
            message=f"Invalid max_rounds: {max_rounds}",
        ),
        "max_hours": validate_decimal_hours(
            max_hours,
            message=f"Invalid max_hours: {max_hours}",
        ),
        "max_tasks": validate_positive_int(
            max_tasks,
            minimum=1,
            message=f"Invalid max_tasks: {max_tasks}",
        ),
        "checkpoint_every": validate_positive_int(
            checkpoint_every,
            minimum=1,
            message=f"Invalid checkpoint_every: {checkpoint_every}",
        ),
        "loop_max_attempts": validate_positive_int(
            loop_max_attempts,
            minimum=1,
            message=f"Invalid loop_max_attempts: {loop_max_attempts}",
        ),
        "notify_mode": notify_mode,
        "comment_target": comment_target,
        "comment_pr_number": comment_pr_number,
        "allow_auto_send": allow_auto_send,
        "fix_command": fix_command,
    }


def write_controller_config_outputs(config: Mapping[str, str], output_path: Path) -> None:
    """Write controller config fields to GitHub output format."""
    append_output(
        output_path,
        [
            ("plan_id", config["plan_id"]),
            ("branch_base", config["branch_base"]),
            ("mode", config["mode"]),
            ("max_rounds", config["max_rounds"]),
            ("max_hours", config["max_hours"]),
            ("max_tasks", config["max_tasks"]),
            ("checkpoint_every", config["checkpoint_every"]),
            ("loop_max_attempts", config["loop_max_attempts"]),
            ("notify_mode", config["notify_mode"]),
            ("comment_target", config["comment_target"]),
            ("comment_pr_number", config["comment_pr_number"]),
            ("allow_auto_send", config["allow_auto_send"]),
        ],
    )
    append_multiline_output(output_path, "fix_command", config["fix_command"])
