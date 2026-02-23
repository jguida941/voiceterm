"""Shared helpers for the bounded CodeRabbit remediation loop."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORKFLOW = "CodeRabbit Triage Bridge"


def run_capture(cmd: list[str], *, cwd: Path = REPO_ROOT) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return 127, "", str(exc)
    return completed.returncode, completed.stdout or "", completed.stderr or ""


def gh_json(repo: str, args: list[str]) -> tuple[Any | None, str | None]:
    cmd = ["gh", *args]
    if repo:
        cmd.extend(["--repo", repo])
    rc, stdout, stderr = run_capture(cmd)
    if rc != 0:
        return None, (stderr or stdout or "gh command failed").strip()
    try:
        return json.loads(stdout), None
    except json.JSONDecodeError as exc:
        return None, f"invalid json from gh ({exc})"


def resolve_repo(raw: str | None) -> str:
    value = str(raw or "").strip()
    if value:
        return value
    return str(os.getenv("GITHUB_REPOSITORY", "")).strip()


def list_runs(repo: str, workflow: str, branch: str, limit: int) -> tuple[list[dict], str | None]:
    payload, error = gh_json(
        repo,
        [
            "run",
            "list",
            "--workflow",
            workflow,
            "--branch",
            branch,
            "--limit",
            str(limit),
            "--json",
            "databaseId,status,conclusion,headSha,url,createdAt",
        ],
    )
    if error:
        return [], error
    if not isinstance(payload, list):
        return [], "unexpected gh run list payload"
    return [row for row in payload if isinstance(row, dict)], None


def latest_run(repo: str, workflow: str, branch: str, limit: int) -> tuple[dict | None, str | None]:
    runs, error = list_runs(repo, workflow, branch, limit)
    if error:
        return None, error
    if not runs:
        return None, "no workflow runs found"
    return runs[0], None


def wait_for_latest_completed(
    *,
    repo: str,
    workflow: str,
    branch: str,
    limit: int,
    poll_seconds: int,
    timeout_seconds: int,
) -> tuple[dict | None, str | None]:
    deadline = time.time() + timeout_seconds
    last_error = ""
    while time.time() < deadline:
        run, error = latest_run(repo, workflow, branch, limit)
        if error:
            last_error = error
            time.sleep(poll_seconds)
            continue
        if str(run.get("status") or "").lower() == "completed":
            return run, None
        time.sleep(poll_seconds)
    return None, f"timeout waiting for completed run ({last_error or 'no completed run yet'})"


def wait_for_new_completed_run(
    *,
    repo: str,
    workflow: str,
    branch: str,
    previous_sha: str,
    limit: int,
    poll_seconds: int,
    timeout_seconds: int,
) -> tuple[dict | None, str | None]:
    deadline = time.time() + timeout_seconds
    last_seen = ""
    while time.time() < deadline:
        run, error = latest_run(repo, workflow, branch, limit)
        if error:
            time.sleep(poll_seconds)
            continue
        sha = str(run.get("headSha") or "").strip()
        status = str(run.get("status") or "").lower()
        if sha:
            last_seen = sha
        if sha and sha != previous_sha and status == "completed":
            return run, None
        time.sleep(poll_seconds)
    return None, f"timeout waiting for new completed run (last_seen_sha={last_seen or previous_sha})"


def download_run_artifacts(repo: str, run_id: int, out_dir: Path) -> str | None:
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["gh", "run", "download", str(run_id), "--dir", str(out_dir)]
    if repo:
        cmd.extend(["--repo", repo])
    rc, stdout, stderr = run_capture(cmd)
    if rc != 0:
        return (stderr or stdout or "gh run download failed").strip()
    return None


def load_backlog_items(root: Path) -> tuple[list[dict], str | None]:
    candidates = sorted(root.rglob("backlog-medium.json"))
    if not candidates:
        return [], "missing backlog-medium.json in downloaded artifacts"
    path = candidates[0]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return [], str(exc)
    except json.JSONDecodeError as exc:
        return [], f"invalid json ({exc})"
    items = payload.get("items", []) if isinstance(payload, dict) else []
    if not isinstance(items, list):
        return [], "backlog payload items is not a list"
    return [row for row in items if isinstance(row, dict)], None


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


def build_report(*, repo: str, branch: str, workflow: str, max_attempts: int, fix_command: str | None) -> dict:
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
) -> dict:
    report = build_report(
        repo=repo,
        branch=branch,
        workflow=workflow,
        max_attempts=max_attempts,
        fix_command=fix_command,
    )

    for attempt in range(1, max_attempts + 1):
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
        run_sha = str(run.get("headSha") or "").strip()
        attempt_row: dict[str, Any] = {
            "attempt": attempt,
            "run_id": run_id,
            "run_sha": run_sha,
            "run_url": str(run.get("url") or "").strip(),
            "run_conclusion": str(run.get("conclusion") or "").strip().lower(),
            "status": "analyzing-backlog",
        }
        if run_id <= 0:
            attempt_row["status"] = "failed"
            attempt_row["message"] = "latest run missing databaseId"
            report["attempts"].append(attempt_row)
            report["reason"] = "latest run missing databaseId"
            break

        with tempfile.TemporaryDirectory(prefix="ralph-loop-") as temp_dir:
            download_root = Path(temp_dir) / f"attempt-{attempt}"
            download_error = download_run_artifacts(repo, run_id, download_root)
            if download_error:
                attempt_row["status"] = "failed"
                attempt_row["message"] = f"artifact download failed: {download_error}"
                report["attempts"].append(attempt_row)
                report["reason"] = "artifact download failed"
                break

            backlog_items, backlog_error = load_backlog_items(download_root)
            if backlog_error:
                attempt_row["status"] = "failed"
                attempt_row["message"] = f"backlog parse failed: {backlog_error}"
                report["attempts"].append(attempt_row)
                report["reason"] = "backlog parse failed"
                break

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
    return report
