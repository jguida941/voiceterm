"""Read-only status action for ``devctl pipeline --action status``.

Reads the current commit pipeline artifact and renders a typed summary
(no mutation, no receipts). The returned payload is stable enough for
tests to snapshot and for other tooling to consume as JSON.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .head_movement import (
    head_movement_context,
    managed_receipt_parent_for_current_head,
)
from .status_git import git_reconcile_state
from .status_push_report import (
    load_pipeline_push_report,
    push_report_view,
)
from .status_reconcile import (
    operation_reconcile_state,
)
from .support import (
    PipelinePaths,
    authorization_is_expired,
    authorized_head_sha_of,
    expires_at_of,
    load_pipeline_payload,
    parse_iso,
    pipeline_id_of,
    pipeline_state_of,
    recommended_next_action,
    recommended_next_command,
    resolve_current_head,
)
from ...runtime.commit_receipt import commit_receipt_artifact_relpath


def build_status_view(
    paths: PipelinePaths,
    *,
    now: datetime | None = None,
    git_state_fn=None,
    push_report_loader=None,
) -> dict[str, Any]:
    """Return the typed status dict without touching the filesystem twice."""
    payload = load_pipeline_payload(paths)
    current_head = resolve_current_head(repo_root=paths.repo_root)
    reference_now = now or datetime.now(timezone.utc)
    git_state = (git_state_fn or git_reconcile_state)(paths.repo_root)
    current_branch = str(git_state.get("current_branch") or "")

    pipeline_id = pipeline_id_of(payload)
    state = pipeline_state_of(payload)
    commit_sha = str(payload.get("commit_sha") or "")
    commit_receipt_relpath = (
        commit_receipt_artifact_relpath(commit_sha) if commit_sha else ""
    )
    commit_receipt_path = paths.repo_root / commit_receipt_relpath
    if not commit_receipt_relpath:
        commit_receipt_path = Path()
    authorized_head = authorized_head_sha_of(payload)
    expires_at = expires_at_of(payload)
    receipt_parent = managed_receipt_parent_for_current_head(
        payload,
        current_head=current_head,
        repo_root=paths.repo_root,
    )
    head_movement = head_movement_context(
        payload,
        current_head=current_head,
        receipt_parent_sha=receipt_parent,
    )
    approved_at = _approved_at_of(payload)
    age_seconds = _compute_age_seconds(
        approved_at=approved_at,
        reference_now=reference_now,
    )
    latest_push_report = (
        push_report_loader(repo_root=paths.repo_root)
        if push_report_loader is not None
        else load_pipeline_push_report(paths.repo_root)
    )
    push_report_summary = push_report_view(
        latest_push_report,
        repo_root=paths.repo_root,
        current_branch=current_branch,
        current_head=current_head,
    )

    view = {
        "ok": bool(payload),
        "pipeline_artifact_path": str(paths.pipeline_path),
        "pipeline_exists": bool(payload),
        "pipeline_id": pipeline_id,
        "state": state,
        "commit_sha": commit_sha,
        "commit_receipt_artifact_path": commit_receipt_relpath,
        "commit_receipt_exists": bool(
            commit_receipt_relpath and commit_receipt_path.exists()
        ),
        "authorized_head_sha": authorized_head,
        "current_head_sha": current_head,
        "expires_at_utc": expires_at,
        "age_seconds": age_seconds,
        "authorization_expired": authorization_is_expired(
            payload,
            now=reference_now,
        ),
        "head_has_moved": head_movement.head_has_moved,
        "head_movement_classification": head_movement.classification,
        "managed_receipt_parent_sha": head_movement.managed_receipt_parent_sha,
        "current_branch": current_branch,
        "upstream_ref": str(git_state.get("upstream_ref") or ""),
        "ahead_of_upstream_commits": git_state.get("ahead_of_upstream_commits"),
        "behind_upstream_commits": git_state.get("behind_upstream_commits"),
        "worktree_clean": git_state.get("worktree_clean"),
        "latest_push_report_path": push_report_summary["path"],
        "latest_push_report_exists": push_report_summary["exists"],
        "latest_push_report_status": push_report_summary["status"],
        "latest_push_report_reason": push_report_summary["reason"],
        "latest_push_report_head_commit": push_report_summary["head_commit"],
        "latest_push_report_branch": push_report_summary["branch"],
        "latest_push_report_published_remote": push_report_summary["published_remote"],
        "latest_push_report_post_push_green": push_report_summary["post_push_green"],
        "latest_push_report_matches_current_head": push_report_summary[
            "matches_current_head"
        ],
        "latest_push_report_matches_current_branch": push_report_summary[
            "matches_current_branch"
        ],
        "recommended_next_action": recommended_next_action(
            payload,
            current_head=current_head,
            receipt_parent_sha=receipt_parent,
            now=reference_now,
        ),
        "next_command": recommended_next_command(
            payload,
            current_head=current_head,
            receipt_parent_sha=receipt_parent,
            now=reference_now,
        ),
    }
    view["operation_reconcile_state"] = operation_reconcile_state(
        view,
        commit_sha=commit_sha,
        current_head=current_head,
        receipt_parent=head_movement.managed_receipt_parent_sha,
    )
    return view


def _approved_at_of(payload: dict[str, Any]) -> str:
    auth = payload.get("push_authorization")
    if isinstance(auth, dict):
        value = auth.get("approved_at_utc")
        if isinstance(value, str):
            return value
    return ""


def _compute_age_seconds(
    *,
    approved_at: str,
    reference_now: datetime,
) -> int | None:
    parsed = parse_iso(approved_at)
    if parsed is None:
        return None
    delta = reference_now - parsed
    return int(delta.total_seconds())


def render_status_markdown(view: dict[str, Any]) -> str:
    """Render the status view as a compact markdown block."""
    lines: list[str] = ["# pipeline status", ""]
    if not view.get("pipeline_exists"):
        lines.append("- pipeline: (no commit_pipeline.json artifact found)")
        lines.append(f"- artifact: `{view.get('pipeline_artifact_path','')}`")
        lines.append("- recommended next action: `none`")
        lines.append("- next command: ``")
        return "\n".join(lines) + "\n"
    lines.extend([
        f"- artifact: `{view['pipeline_artifact_path']}`",
        f"- pipeline_id: `{view['pipeline_id']}`",
        f"- state: `{view['state']}`",
        f"- operation_reconcile_state: `{view['operation_reconcile_state']}`",
        f"- commit_sha: `{view['commit_sha']}`",
        f"- commit_receipt_artifact: `{view['commit_receipt_artifact_path']}`",
        f"- commit_receipt_exists: `{view['commit_receipt_exists']}`",
        f"- authorized_head_sha: `{view['authorized_head_sha']}`",
        f"- current_head_sha: `{view['current_head_sha']}`",
        f"- current_branch: `{view['current_branch']}`",
        f"- upstream_ref: `{view['upstream_ref']}`",
        f"- ahead_of_upstream_commits: `{view['ahead_of_upstream_commits']}`",
        f"- behind_upstream_commits: `{view['behind_upstream_commits']}`",
        f"- worktree_clean: `{view['worktree_clean']}`",
        f"- latest_push_report: `{view['latest_push_report_path']}`",
        f"- latest_push_report_exists: `{view['latest_push_report_exists']}`",
        f"- latest_push_report_status: `{view['latest_push_report_status']}`",
        f"- latest_push_report_reason: `{view['latest_push_report_reason']}`",
        f"- latest_push_report_head_commit: `{view['latest_push_report_head_commit']}`",
        f"- latest_push_report_matches_current_head: `{view['latest_push_report_matches_current_head']}`",
        f"- latest_push_report_published_remote: `{view['latest_push_report_published_remote']}`",
        f"- latest_push_report_post_push_green: `{view['latest_push_report_post_push_green']}`",
        f"- expires_at_utc: `{view['expires_at_utc']}`",
        f"- age_seconds: `{view['age_seconds']}`",
        f"- authorization_expired: `{view['authorization_expired']}`",
        f"- head_has_moved: `{view['head_has_moved']}`",
        f"- head_movement_classification: `{view['head_movement_classification']}`",
        f"- managed_receipt_parent_sha: `{view['managed_receipt_parent_sha']}`",
        f"- recommended next action: `{view['recommended_next_action']}`",
        f"- next command: `{view['next_command']}`",
    ])
    return "\n".join(lines) + "\n"


def render_status_json(view: dict[str, Any]) -> str:
    """Render the status view as pretty JSON."""
    return json.dumps(view, indent=2)


def run_status(args) -> int:
    """Entry point for ``devctl pipeline --action status``."""
    from .support import resolve_pipeline_paths

    paths = resolve_pipeline_paths(
        repo_root=getattr(args, "repo_root_override", None),
        pipeline_root_override=_maybe_path(
            getattr(args, "pipeline_root_override", None)
        ),
        receipts_root_override=_maybe_path(
            getattr(args, "receipts_root_override", None)
        ),
    )
    view = build_status_view(paths)
    fmt = str(getattr(args, "format", "md") or "md")
    if fmt == "json":
        print(render_status_json(view))
    else:
        print(render_status_markdown(view))
    return 0 if view["ok"] else 1


def _maybe_path(value: Any) -> Path | None:
    if value is None:
        return None
    return Path(value)
