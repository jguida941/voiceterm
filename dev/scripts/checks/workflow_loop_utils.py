"""Shared GitHub workflow-run helpers for bounded remediation loops."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]


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
            "databaseId,status,conclusion,headSha,headBranch,url,createdAt",
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


def run_by_id(repo: str, run_id: int) -> tuple[dict | None, str | None]:
    payload, error = gh_json(
        repo,
        [
            "run",
            "view",
            str(run_id),
            "--json",
            "databaseId,status,conclusion,headSha,headBranch,url,createdAt",
        ],
    )
    if error:
        return None, error
    if not isinstance(payload, dict):
        return None, "unexpected gh run view payload"
    return payload, None


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


def wait_for_run_completed_by_id(
    *,
    repo: str,
    run_id: int,
    poll_seconds: int,
    timeout_seconds: int,
) -> tuple[dict | None, str | None]:
    deadline = time.time() + timeout_seconds
    last_error = ""
    while time.time() < deadline:
        run, error = run_by_id(repo, run_id)
        if error:
            last_error = error
            time.sleep(poll_seconds)
            continue
        if str(run.get("status") or "").lower() == "completed":
            return run, None
        time.sleep(poll_seconds)
    return None, f"timeout waiting for source run {run_id} to complete ({last_error or 'still running'})"


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
