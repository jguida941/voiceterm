"""Shared helpers for a bounded mutation remediation loop."""

from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
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


def run_fix_command(
    command: str,
    *,
    attempt: int,
    repo: str,
    branch: str,
    run_id: int,
    run_sha: str,
    threshold: float,
) -> tuple[int, str | None]:
    env = os.environ.copy()
    env["MUTATION_ATTEMPT"] = str(attempt)
    env["MUTATION_REPO"] = repo
    env["MUTATION_BRANCH"] = branch
    env["MUTATION_SOURCE_RUN_ID"] = str(run_id)
    env["MUTATION_SOURCE_SHA"] = run_sha
    env["MUTATION_THRESHOLD"] = str(threshold)
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


def build_report(
    *,
    repo: str,
    branch: str,
    workflow: str,
    mode: str,
    max_attempts: int,
    threshold: float,
    fix_command: str | None,
    fix_block_reason: str | None,
) -> dict:
    return {
        "command": "mutation_loop",
        "timestamp": datetime.now().isoformat(),
        "ok": False,
        "repo": repo,
        "branch": branch,
        "workflow": workflow,
        "mode": mode,
        "max_attempts": max_attempts,
        "threshold": threshold,
        "completed_attempts": 0,
        "attempts": [],
        "reason": "",
        "fix_command_configured": bool(fix_command),
        "fix_block_reason": fix_block_reason,
    }


def execute_loop(
    *,
    repo: str,
    branch: str,
    workflow: str,
    mode: str,
    max_attempts: int,
    run_list_limit: int,
    poll_seconds: int,
    timeout_seconds: int,
    threshold: float,
    fix_command: str | None,
    fix_block_reason: str | None = None,
) -> dict:
    report = build_report(
        repo=repo,
        branch=branch,
        workflow=workflow,
        mode=mode,
        max_attempts=max_attempts,
        threshold=threshold,
        fix_command=fix_command,
        fix_block_reason=fix_block_reason,
    )
    previous_sha = ""

    for attempt in range(1, max_attempts + 1):
        if attempt == 1:
            run, run_error = wait_for_latest_completed(
                repo=repo,
                workflow=workflow,
                branch=branch,
                limit=run_list_limit,
                poll_seconds=poll_seconds,
                timeout_seconds=timeout_seconds,
            )
        else:
            run, run_error = wait_for_new_completed_run(
                repo=repo,
                workflow=workflow,
                branch=branch,
                previous_sha=previous_sha,
                limit=run_list_limit,
                poll_seconds=poll_seconds,
                timeout_seconds=timeout_seconds,
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
            attempt_row["status"] = "failed"
            attempt_row["message"] = "latest run missing databaseId"
            report["attempts"].append(attempt_row)
            report["reason"] = "latest run missing databaseId"
            break

        with tempfile.TemporaryDirectory(prefix="mutation-loop-") as temp_dir:
            download_root = Path(temp_dir) / f"attempt-{attempt}"
            download_error = download_run_artifacts(repo, run_id, download_root)
            if download_error:
                attempt_row["status"] = "failed"
                attempt_row["message"] = f"artifact download failed: {download_error}"
                report["attempts"].append(attempt_row)
                report["reason"] = "artifact download failed"
                break

            outcome_report, outcome_error = aggregate_outcomes(download_root)
            if outcome_error:
                attempt_row["status"] = "failed"
                attempt_row["message"] = f"outcome parse failed: {outcome_error}"
                report["attempts"].append(attempt_row)
                report["reason"] = "outcome parse failed"
                break

            score = float(outcome_report.get("score") or 0.0)
            counts = outcome_report.get("counts", {})
            missed = int(counts.get("missed", 0)) if isinstance(counts, dict) else 0
            attempt_row["score"] = round(score, 6)
            attempt_row["counts"] = counts
            attempt_row["hotspots"] = outcome_report.get("hotspots", [])[:10]
            attempt_row["freshness"] = outcome_report.get("freshness", [])
            report["completed_attempts"] = attempt
            report["last_score"] = round(score, 6)
            report["last_counts"] = counts
            report["last_hotspots"] = outcome_report.get("hotspots", [])[:10]
            report["last_freshness"] = outcome_report.get("freshness", [])

            if score >= threshold:
                attempt_row["status"] = "resolved"
                attempt_row["message"] = (
                    f"mutation score {score:.2%} meets threshold {threshold:.2%}"
                )
                report["attempts"].append(attempt_row)
                report["ok"] = True
                report["reason"] = "threshold_met"
                break

            if mode == "report-only":
                attempt_row["status"] = "reported"
                attempt_row["message"] = (
                    f"mutation score {score:.2%} below threshold {threshold:.2%}; report-only mode"
                )
                report["attempts"].append(attempt_row)
                report["reason"] = "report_only_below_threshold"
                break

            if not fix_command:
                attempt_row["status"] = "blocked"
                attempt_row["message"] = (
                    f"mutation score {score:.2%} below threshold with no --fix-command configured"
                )
                report["attempts"].append(attempt_row)
                report["reason"] = "no_fix_command_configured"
                break

            if fix_block_reason:
                attempt_row["status"] = "blocked"
                attempt_row["message"] = fix_block_reason
                attempt_row["missed_survivors"] = missed
                report["attempts"].append(attempt_row)
                report["reason"] = "fix_command_policy_blocked"
                break

            fix_rc, fix_error = run_fix_command(
                fix_command,
                attempt=attempt,
                repo=repo,
                branch=branch,
                run_id=run_id,
                run_sha=run_sha,
                threshold=threshold,
            )
            attempt_row["fix_exit_code"] = fix_rc
            if fix_error:
                attempt_row["status"] = "failed"
                attempt_row["message"] = f"fix command error: {fix_error}"
                report["attempts"].append(attempt_row)
                report["reason"] = "fix_command_error"
                break
            if fix_rc != 0:
                attempt_row["status"] = "failed"
                attempt_row["message"] = "fix command returned non-zero exit code"
                report["attempts"].append(attempt_row)
                report["reason"] = "fix_command_failed"
                break

            attempt_row["status"] = "waiting-for-new-run"
            attempt_row["message"] = (
                f"mutation score {score:.2%} below threshold; fix command applied"
            )
            report["attempts"].append(attempt_row)
            previous_sha = run_sha
    else:
        report["reason"] = "max_attempts_reached_below_threshold"
    return report
