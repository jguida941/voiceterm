"""Shared GitHub PR/commit comment upsert helpers for loop commands."""

from __future__ import annotations

import json
from typing import Any, Callable

JsonGetter = Callable[[str, list[str]], tuple[Any | None, str | None]]
CommandRunner = Callable[..., tuple[int, str, str]]


def coerce_pr_number(value: Any) -> int | None:
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.isdigit():
        parsed = int(value)
        return parsed if parsed > 0 else None
    return None


def _list_target_comments(
    repo: str,
    target: dict[str, Any],
    *,
    gh_json_fn: JsonGetter,
) -> tuple[list[dict[str, Any]], str | None]:
    if target["kind"] == "pr":
        payload, error = gh_json_fn(
            repo,
            ["api", f"/repos/{repo}/issues/{target['id']}/comments?per_page=100"],
        )
    else:
        payload, error = gh_json_fn(
            repo,
            ["api", f"/repos/{repo}/commits/{target['id']}/comments?per_page=100"],
        )
    if error:
        return [], error
    if not isinstance(payload, list):
        return [], "unexpected comments payload"
    return [row for row in payload if isinstance(row, dict)], None


def _mutate_comment(
    repo: str,
    *,
    method: str,
    endpoint: str,
    body: str,
    run_capture_fn: CommandRunner,
) -> tuple[dict[str, Any], str | None]:
    cmd = ["gh", "api", "--method", method, endpoint, "-f", f"body={body}"]
    if repo:
        cmd.extend(["--repo", repo])
    rc, stdout, stderr = run_capture_fn(cmd)
    if rc != 0:
        return {}, (stderr or stdout or "gh api failed").strip()
    try:
        payload = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        return {}, "unexpected gh api response payload"
    return payload, None


def upsert_comment(
    repo: str,
    target: dict[str, Any],
    *,
    marker: str,
    body: str,
    gh_json_fn: JsonGetter,
    run_capture_fn: CommandRunner,
) -> tuple[dict[str, Any], str | None]:
    comments, error = _list_target_comments(repo, target, gh_json_fn=gh_json_fn)
    if error:
        return {}, error
    existing: dict[str, Any] | None = None
    for row in comments:
        if marker in str(row.get("body") or ""):
            existing = row

    if existing:
        comment_id = existing.get("id")
        if not isinstance(comment_id, int):
            return {}, "existing marker comment missing numeric id"
        if target["kind"] == "pr":
            endpoint = f"/repos/{repo}/issues/comments/{comment_id}"
        else:
            endpoint = f"/repos/{repo}/comments/{comment_id}"
        payload, patch_error = _mutate_comment(
            repo,
            method="PATCH",
            endpoint=endpoint,
            body=body,
            run_capture_fn=run_capture_fn,
        )
        if patch_error:
            return {}, patch_error
        payload["action"] = "updated"
        return payload, None

    if target["kind"] == "pr":
        endpoint = f"/repos/{repo}/issues/{target['id']}/comments"
    else:
        endpoint = f"/repos/{repo}/commits/{target['id']}/comments"
    payload, create_error = _mutate_comment(
        repo,
        method="POST",
        endpoint=endpoint,
        body=body,
        run_capture_fn=run_capture_fn,
    )
    if create_error:
        return {}, create_error
    payload["action"] = "created"
    return payload, None
