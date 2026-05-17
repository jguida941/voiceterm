"""Shared helpers for a bounded mutation remediation loop."""

from __future__ import annotations

from dataclasses import dataclass
import os
import shlex
import subprocess
from datetime import datetime, timezone
from typing import Any

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
DEFAULT_WORKFLOW = "Mutation Testing"

try:
    from dev.scripts.checks.workflow_loop_utils import (
        download_run_artifacts,
        gh_json,
        resolve_repo,
        run_capture,
        wait_for_latest_completed,
        wait_for_new_completed_run,
    )
except ModuleNotFoundError:
    from checks.workflow_loop_utils import (
        download_run_artifacts,
        gh_json,
        resolve_repo,
        run_capture,
        wait_for_latest_completed,
        wait_for_new_completed_run,
    )
try:
    from dev.scripts.checks.mutation_outcome_parse import aggregate_outcomes
except ModuleNotFoundError:
    from checks.mutation_outcome_parse import aggregate_outcomes
if __package__:
    from .outcome import (
        AttemptScoreContext,
        FixCommandContext,
        handle_attempt_score,
        load_attempt_outcome,
        record_attempt_result,
        record_outcome_summary,
    )
else:  # pragma: no cover - standalone script fallback
    from outcome import (
        AttemptScoreContext,
        FixCommandContext,
        handle_attempt_score,
        load_attempt_outcome,
        record_attempt_result,
        record_outcome_summary,
    )


@dataclass(frozen=True)
class LoopConfig:
    repo: str
    branch: str
    workflow: str
    mode: str
    max_attempts: int
    run_list_limit: int
    poll_seconds: int
    timeout_seconds: int
    threshold: float
    fix_command: str | None
    fix_block_reason: str | None


def _coerce_loop_config(config_kwargs: dict[str, Any]) -> LoopConfig:
    return LoopConfig(
        repo=str(config_kwargs["repo"]),
        branch=str(config_kwargs["branch"]),
        workflow=str(config_kwargs["workflow"]),
        mode=str(config_kwargs["mode"]),
        max_attempts=int(config_kwargs["max_attempts"]),
        run_list_limit=int(config_kwargs["run_list_limit"]),
        poll_seconds=int(config_kwargs["poll_seconds"]),
        timeout_seconds=int(config_kwargs["timeout_seconds"]),
        threshold=float(config_kwargs["threshold"]),
        fix_command=config_kwargs.get("fix_command"),
        fix_block_reason=config_kwargs.get("fix_block_reason"),
    )


def run_fix_command(
    command: str,
    context: FixCommandContext,
) -> tuple[int, str | None]:
    env = os.environ.copy()
    env["MUTATION_ATTEMPT"] = str(context.attempt)
    env["MUTATION_REPO"] = context.repo
    env["MUTATION_BRANCH"] = context.branch
    env["MUTATION_SOURCE_RUN_ID"] = str(context.run_id)
    env["MUTATION_SOURCE_SHA"] = context.run_sha
    env["MUTATION_THRESHOLD"] = str(context.threshold)
    try:
        argv = shlex.split(command, posix=True)
    except ValueError as exc:
        return 2, f"invalid --fix-command: {exc}"
    if not argv:
        return 2, "invalid --fix-command: empty command"
    try:
        completed = subprocess.run(argv, cwd=REPO_ROOT, env=env, check=False)
    except OSError as exc:
        return 127, str(exc)
    return completed.returncode, None


def build_report(config: LoopConfig) -> dict:
    return {
        "command": "mutation_loop",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": False,
        "repo": config.repo,
        "branch": config.branch,
        "workflow": config.workflow,
        "mode": config.mode,
        "max_attempts": config.max_attempts,
        "threshold": config.threshold,
        "completed_attempts": 0,
        "attempts": [],
        "reason": "",
        "fix_command_configured": bool(config.fix_command),
        "fix_block_reason": config.fix_block_reason,
    }


def _wait_for_completed_run(
    config: LoopConfig,
    *,
    attempt: int,
    previous_sha: str,
) -> tuple[dict[str, Any], str | None]:
    wait_kwargs = {
        "repo": config.repo,
        "workflow": config.workflow,
        "branch": config.branch,
        "limit": config.run_list_limit,
        "poll_seconds": config.poll_seconds,
        "timeout_seconds": config.timeout_seconds,
    }
    if attempt == 1:
        return wait_for_latest_completed(**wait_kwargs)
    return wait_for_new_completed_run(
        previous_sha=previous_sha,
        **wait_kwargs,
    )


def execute_loop(**config_kwargs: Any) -> dict:
    config = _coerce_loop_config(config_kwargs)
    report = build_report(config)
    previous_sha = ""

    for attempt in range(1, config.max_attempts + 1):
        run, run_error = _wait_for_completed_run(
            config,
            attempt=attempt,
            previous_sha=previous_sha,
        )
        if run_error:
            report["reason"] = run_error
            break

        run_id = int(run.get("databaseId") or 0)
        run_sha = str(run.get("headSha") or "").strip()
        attempt_row: dict[str, Any] = {
            "attempt": attempt,
            "run_id": run_id,
            "run_sha": run_sha,
            "run_url": str(run.get("url") or "").strip(),
            "run_conclusion": str(run.get("conclusion") or "").strip().lower(),
            "status": "analyzing-outcomes",
        }
        if run_id <= 0:
            record_attempt_result(
                report=report,
                attempt_row=attempt_row,
                status="failed",
                message="latest run missing databaseId",
                reason="latest run missing databaseId",
            )
            break

        outcome_report, outcome_message, outcome_reason = load_attempt_outcome(
            repo=config.repo,
            run_id=run_id,
            attempt=attempt,
        )
        if outcome_report is None:
            record_attempt_result(
                report=report,
                attempt_row=attempt_row,
                status="failed",
                message=outcome_message or "unknown outcome error",
                reason=outcome_reason or "outcome error",
            )
            break

        score, counts, missed = record_outcome_summary(
            report=report,
            attempt_row=attempt_row,
            attempt=attempt,
            outcome_report=outcome_report,
        )
        should_continue, next_previous_sha = handle_attempt_score(
            AttemptScoreContext(
                report=report,
                attempt_row=attempt_row,
                score=score,
                threshold=config.threshold,
                mode=config.mode,
                fix_command=config.fix_command,
                fix_block_reason=config.fix_block_reason,
                missed=missed,
                fix_context=FixCommandContext(
                    attempt=attempt,
                    repo=config.repo,
                    branch=config.branch,
                    run_id=run_id,
                    run_sha=run_sha,
                    threshold=config.threshold,
                ),
                run_fix_command_fn=run_fix_command,
            )
        )
        if not should_continue:
            break
        previous_sha = next_previous_sha
    else:
        report["reason"] = "max_attempts_reached_below_threshold"
    return report
