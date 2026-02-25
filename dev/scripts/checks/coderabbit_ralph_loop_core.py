"""Shared helpers for the bounded CodeRabbit remediation loop."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORKFLOW = "CodeRabbit Triage Bridge"

try:
    from dev.scripts.checks.workflow_loop_utils import (
        download_run_artifacts,
        gh_json,
        resolve_repo,
        run_capture,
        wait_for_latest_completed,
        wait_for_new_completed_run,
        wait_for_run_completed_by_id,
    )
except ModuleNotFoundError:
    from checks.workflow_loop_utils import (
        download_run_artifacts,
        gh_json,
        resolve_repo,
        run_capture,
        wait_for_latest_completed,
        wait_for_new_completed_run,
        wait_for_run_completed_by_id,
    )


def normalize_sha(value: str | None) -> str:
    return str(value or "").strip().lower()


def load_backlog_payload(root: Path) -> tuple[dict, str | None]:
    candidates = sorted(root.rglob("backlog-medium.json"))
    if not candidates:
        return {}, "missing backlog-medium.json in downloaded artifacts"
    path = candidates[0]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return {}, str(exc)
    except json.JSONDecodeError as exc:
        return {}, f"invalid json ({exc})"
    if not isinstance(payload, dict):
        return {}, "backlog payload is not an object"
    return payload, None


def run_fix_command(
    command: str,
    *,
    attempt: int,
    repo: str,
    branch: str,
    backlog_count: int,
    backlog_dir: Path,
    run_id: int,
    run_sha: str,
) -> tuple[int, str | None]:
    env = os.environ.copy()
    env["RALPH_ATTEMPT"] = str(attempt)
    env["RALPH_REPO"] = repo
    env["RALPH_BRANCH"] = branch
    env["RALPH_BACKLOG_COUNT"] = str(backlog_count)
    env["RALPH_BACKLOG_DIR"] = str(backlog_dir)
    env["RALPH_SOURCE_RUN_ID"] = str(run_id)
    env["RALPH_SOURCE_SHA"] = run_sha
    try:
        argv = shlex.split(command, posix=True)
    except ValueError as exc:
        return 2, f"invalid --fix-command: {exc}"
    if not argv:
        return 2, "invalid --fix-command: empty command"
    try:
        completed = subprocess.run(
            argv,
            cwd=REPO_ROOT,
            env=env,
            check=False,
        )
    except OSError as exc:
        return 127, str(exc)
    return completed.returncode, None


def build_report(
    *,
    repo: str,
    branch: str,
    workflow: str,
    max_attempts: int,
    fix_command: str | None,
    fix_block_reason: str | None = None,
    source_run_id: int | None = None,
    source_run_sha: str | None = None,
    source_event: str | None = None,
) -> dict:
    normalized_source_sha = normalize_sha(source_run_sha)
    return {
        "command": "run_coderabbit_ralph_loop",
        "timestamp": datetime.now().isoformat(),
        "ok": False,
        "repo": repo,
        "branch": branch,
        "workflow": workflow,
        "max_attempts": max_attempts,
        "completed_attempts": 0,
        "attempts": [],
        "unresolved_count": 0,
        "reason": "",
        "fix_command_configured": bool(fix_command),
        "fix_block_reason": fix_block_reason,
        "escalation_needed": False,
        "source_run_id": source_run_id if source_run_id and source_run_id > 0 else None,
        "source_run_sha": normalized_source_sha or None,
        "source_event": str(source_event or "workflow_dispatch"),
        "source_correlation": "pending" if source_run_id else "branch_latest_fallback",
        "backlog_pr_number": None,
        "backlog_head_sha": None,
    }


def execute_loop(
    *,
    repo: str,
    branch: str,
    workflow: str,
    max_attempts: int,
    run_list_limit: int,
    poll_seconds: int,
    timeout_seconds: int,
    fix_command: str | None,
    fix_block_reason: str | None = None,
    source_run_id: int | None = None,
    source_run_sha: str | None = None,
    source_event: str | None = None,
) -> dict:
    report = build_report(
        repo=repo,
        branch=branch,
        workflow=workflow,
        max_attempts=max_attempts,
        fix_command=fix_command,
        fix_block_reason=fix_block_reason,
        source_run_id=source_run_id,
        source_run_sha=source_run_sha,
        source_event=source_event,
    )
    normalized_source_sha = normalize_sha(source_run_sha)
    if source_run_id is not None and source_run_id <= 0:
        report["reason"] = "invalid source run id"
        report["source_correlation"] = "invalid_source_run_id"
        return report

    for attempt in range(1, max_attempts + 1):
        if attempt == 1 and source_run_id:
            run, run_error = wait_for_run_completed_by_id(
                repo=repo,
                run_id=source_run_id,
                poll_seconds=poll_seconds,
                timeout_seconds=timeout_seconds,
            )
        else:
            run, run_error = wait_for_latest_completed(
                repo=repo,
                workflow=workflow,
                branch=branch,
                limit=run_list_limit,
                poll_seconds=poll_seconds,
                timeout_seconds=timeout_seconds,
            )
        if run_error:
            report["reason"] = run_error
            break

        run_id = int(run.get("databaseId") or 0)
        run_sha = normalize_sha(str(run.get("headSha") or ""))
        attempt_row: dict[str, Any] = {
            "attempt": attempt,
            "run_id": run_id,
            "run_sha": run_sha,
            "run_url": str(run.get("url") or "").strip(),
            "run_conclusion": str(run.get("conclusion") or "").strip().lower(),
            "status": "analyzing-backlog",
        }
        if attempt == 1 and source_run_id:
            attempt_row["source_run_id"] = source_run_id
            attempt_row["source_run_sha_expected"] = normalized_source_sha or None

        if run_id <= 0:
            attempt_row["status"] = "failed"
            attempt_row["message"] = "latest run missing databaseId"
            report["attempts"].append(attempt_row)
            report["reason"] = "latest run missing databaseId"
            break
        if attempt == 1 and source_run_id and run_id != source_run_id:
            attempt_row["status"] = "failed"
            attempt_row["message"] = (
                f"source run mismatch: expected {source_run_id}, resolved {run_id}"
            )
            attempt_row["source_correlation"] = "source_run_id_mismatch"
            report["attempts"].append(attempt_row)
            report["reason"] = "source_run_id_mismatch"
            report["source_correlation"] = "source_run_id_mismatch"
            break
        if attempt == 1 and source_run_id and normalized_source_sha:
            if not run_sha or run_sha != normalized_source_sha:
                attempt_row["status"] = "failed"
                attempt_row["message"] = (
                    "source run sha mismatch: "
                    f"expected {normalized_source_sha}, got {run_sha or '(missing)'}"
                )
                attempt_row["source_correlation"] = "source_run_sha_mismatch"
                report["attempts"].append(attempt_row)
                report["reason"] = "source_run_sha_mismatch"
                report["source_correlation"] = "source_run_sha_mismatch"
                break
            report["source_run_sha"] = run_sha
            report["source_correlation"] = "source_run_validated"

        with tempfile.TemporaryDirectory(prefix="ralph-loop-") as temp_dir:
            download_root = Path(temp_dir) / f"attempt-{attempt}"
            download_error = download_run_artifacts(repo, run_id, download_root)
            if download_error:
                attempt_row["status"] = "failed"
                attempt_row["message"] = f"artifact download failed: {download_error}"
                report["attempts"].append(attempt_row)
                report["reason"] = "artifact download failed"
                break

            backlog_payload, backlog_error = load_backlog_payload(download_root)
            if backlog_error:
                attempt_row["status"] = "failed"
                attempt_row["message"] = f"backlog parse failed: {backlog_error}"
                report["attempts"].append(attempt_row)
                report["reason"] = "backlog parse failed"
                break
            backlog_items = backlog_payload.get("items", [])
            if not isinstance(backlog_items, list):
                attempt_row["status"] = "failed"
                attempt_row["message"] = "backlog parse failed: backlog items is not a list"
                report["attempts"].append(attempt_row)
                report["reason"] = "backlog parse failed"
                break
            backlog_items = [row for row in backlog_items if isinstance(row, dict)]
            backlog_pr_number = backlog_payload.get("pr_number")
            if isinstance(backlog_pr_number, int):
                attempt_row["backlog_pr_number"] = backlog_pr_number
                report["backlog_pr_number"] = backlog_pr_number
            backlog_head_sha = normalize_sha(str(backlog_payload.get("head_sha") or ""))
            if backlog_head_sha:
                attempt_row["backlog_head_sha"] = backlog_head_sha
                report["backlog_head_sha"] = backlog_head_sha
            if attempt == 1 and source_run_id and normalized_source_sha:
                if not backlog_head_sha or backlog_head_sha != normalized_source_sha:
                    attempt_row["status"] = "failed"
                    attempt_row["message"] = (
                        "source artifact sha mismatch: "
                        f"expected {normalized_source_sha}, got {backlog_head_sha or '(missing)'}"
                    )
                    attempt_row["source_correlation"] = "source_run_sha_mismatch"
                    report["attempts"].append(attempt_row)
                    report["reason"] = "source_run_sha_mismatch"
                    report["source_correlation"] = "source_run_sha_mismatch"
                    break
                report["source_correlation"] = "source_artifact_sha_validated"

            backlog_count = len(backlog_items)
            attempt_row["backlog_count"] = backlog_count
            report["unresolved_count"] = backlog_count
            if backlog_count == 0:
                attempt_row["status"] = "resolved"
                attempt_row["message"] = "medium+ backlog is empty"
                report["attempts"].append(attempt_row)
                report["completed_attempts"] = attempt
                report["ok"] = True
                report["reason"] = "resolved"
                break

            if not fix_command:
                attempt_row["status"] = "blocked"
                attempt_row["message"] = "medium+ backlog remains but no --fix-command configured"
                report["attempts"].append(attempt_row)
                report["completed_attempts"] = attempt
                report["reason"] = "no fix command configured"
                break

            if fix_block_reason:
                attempt_row["status"] = "blocked"
                attempt_row["message"] = fix_block_reason
                report["attempts"].append(attempt_row)
                report["completed_attempts"] = attempt
                report["reason"] = "fix_command_policy_blocked"
                break

            fix_rc, fix_error = run_fix_command(
                fix_command,
                attempt=attempt,
                repo=repo,
                branch=branch,
                backlog_count=backlog_count,
                backlog_dir=download_root,
                run_id=run_id,
                run_sha=run_sha,
            )
            attempt_row["fix_exit_code"] = fix_rc
            if fix_error:
                attempt_row["status"] = "failed"
                attempt_row["message"] = f"fix command error: {fix_error}"
                report["attempts"].append(attempt_row)
                report["completed_attempts"] = attempt
                report["reason"] = "fix command error"
                break
            if fix_rc != 0:
                attempt_row["status"] = "failed"
                attempt_row["message"] = "fix command returned non-zero exit code"
                report["attempts"].append(attempt_row)
                report["completed_attempts"] = attempt
                report["reason"] = "fix command failed"
                break

            attempt_row["status"] = "waiting-for-new-run"
            report["attempts"].append(attempt_row)
            report["completed_attempts"] = attempt
            _, wait_error = wait_for_new_completed_run(
                repo=repo,
                workflow=workflow,
                branch=branch,
                previous_sha=run_sha,
                limit=run_list_limit,
                poll_seconds=poll_seconds,
                timeout_seconds=timeout_seconds,
            )
            if wait_error:
                report["reason"] = wait_error
                break
    else:
        report["reason"] = "max attempts reached with unresolved medium+ backlog"
        report["escalation_needed"] = True
    return report
