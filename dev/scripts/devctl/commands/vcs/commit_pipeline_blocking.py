"""Helpers for governed-commit reports blocked by an active publish pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from ...runtime.post_checkpoint_dirty_support import requires_commit_before_push
from ...runtime.governance_scan import scan_repo_governance_safely
from ..pipeline.refresh_authorization_action import apply_refresh_authorization
from ..pipeline.status_action import build_status_view
from ..pipeline.support import resolve_pipeline_paths
from .commit_visibility import commit_visibility_payload
from .governed_executor_actions import _build_report
from .push_pipeline_state_sync import sync_commit_pipeline_with_push_report

_MARK_DELIVERED_LOCAL_COMMAND = (
    'python3 dev/scripts/devctl.py pipeline --action mark-delivered-local '
    '--reason "<descriptive reason>" --format json'
)


def build_active_pipeline_block_report(*, repo_root: Path, pipeline) -> dict[str, object]:
    """Return the typed block report for a live publish/recovery pipeline."""
    status_view, refresh_result = _load_status_view(repo_root=repo_root)
    next_command = str(status_view.get("next_command") or "").strip()
    recommended_next_action = str(status_view.get("recommended_next_action") or "").strip()
    if _commit_recorded_pipeline_superseded(
        repo_root=repo_root,
        pipeline=pipeline,
        status_view=status_view,
    ):
        recommended_next_action = "mark-delivered-local"
        next_command = _MARK_DELIVERED_LOCAL_COMMAND
    report = _build_report(
        status="blocked",
        reason="active_pipeline_requires_publish_or_recovery",
        pipeline_id=pipeline.pipeline_id,
        pipeline_state=pipeline.state,
        recommended_next_action=recommended_next_action,
        next_command=next_command,
        operator_guidance=_next_command_guidance(next_command),
        **commit_visibility_payload(pipeline),
    )
    if refresh_result is not None:
        report["authorization_refreshed"] = bool(refresh_result.get("ok"))
        receipt_path = str(refresh_result.get("receipt_path") or "").strip()
        if receipt_path:
            report["refresh_receipt_path"] = receipt_path
    return report


def auto_transition_non_destructive_push_failure(
    *,
    repo_root: Path,
    pipeline,
) -> bool:
    """Apply the push-failure state rule to a legacy stuck pipeline."""
    if str(getattr(pipeline, "state", "") or "").strip() != "push_blocked":
        return False
    report = _load_pipeline_push_report(repo_root=repo_root, pipeline=pipeline)
    if not report:
        report = _push_result_report_from_pipeline(pipeline)
    if not report:
        return False
    status_view = build_status_view(resolve_pipeline_paths(repo_root=repo_root))
    current_head = str(status_view.get("current_head_sha") or "").strip()
    if not current_head:
        return False
    return sync_commit_pipeline_with_push_report(
        repo_root=repo_root,
        current_branch=str(getattr(pipeline, "branch", "") or "").strip(),
        current_remote=str(getattr(pipeline, "remote", "") or "").strip(),
        current_head_commit=current_head,
        approved_target_identity=str(
            getattr(pipeline, "approved_target_identity", "") or ""
        ).strip(),
        report=report,
    )


def _load_status_view(*, repo_root: Path) -> tuple[dict[str, object], dict[str, object] | None]:
    """Return the status view, auto-refreshing same-HEAD auth when safe."""
    paths = resolve_pipeline_paths(repo_root=repo_root)
    status_view = build_status_view(paths)
    if not _can_auto_refresh(status_view):
        return status_view, None
    refresh_result = apply_refresh_authorization(
        repo_root=repo_root,
        operator_actor="operator",
        reason=(
            "devctl.commit auto-refreshed same-HEAD publication authorization "
            "while projecting an active pipeline block"
        ),
    )
    if not bool(refresh_result.get("ok")):
        return status_view, refresh_result
    return build_status_view(paths), refresh_result


def _can_auto_refresh(status_view: dict[str, object]) -> bool:
    """Return True when the active pipeline can self-heal in place."""
    state = str(
        status_view.get("state") or status_view.get("pipeline_state") or ""
    ).strip()
    if state == "push_blocked":
        return False
    if str(status_view.get("recommended_next_action") or "").strip() != "refresh-authorization":
        return False
    authorized_head = str(status_view.get("authorized_head_sha") or "").strip()
    current_head = str(status_view.get("current_head_sha") or "").strip()
    return bool(authorized_head) and authorized_head == current_head


def _load_pipeline_push_report(*, repo_root: Path, pipeline) -> dict[str, object]:
    relpath = str(getattr(pipeline, "push_report_path", "") or "").strip()
    if not relpath:
        return {}
    path = Path(relpath)
    if not path.is_absolute():
        path = repo_root / relpath
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload if _report_matches_pipeline(payload, pipeline=pipeline) else {}


def _report_matches_pipeline(report: dict[str, object], *, pipeline) -> bool:
    report_branch = str(report.get("branch") or "").strip()
    pipeline_branch = str(getattr(pipeline, "branch", "") or "").strip()
    if report_branch and pipeline_branch and report_branch != pipeline_branch:
        return False
    report_head = str(report.get("head_commit") or "").strip()
    pipeline_commit = str(getattr(pipeline, "commit_sha", "") or "").strip()
    if report_head and pipeline_commit and report_head != pipeline_commit:
        return False
    report_target = str(report.get("approved_target_identity") or "").strip()
    pipeline_target = str(
        getattr(pipeline, "approved_target_identity", "") or ""
    ).strip()
    if report_target and pipeline_target and report_target != pipeline_target:
        return False
    return True


def _push_result_report_from_pipeline(pipeline) -> dict[str, object]:
    result = getattr(pipeline, "push_result", None)
    if result is None:
        return {}
    reason = str(getattr(result, "reason", "") or "").strip()
    if not reason:
        return {}
    partial_progress = bool(getattr(result, "partial_progress", False))
    return {
        "reason": reason,
        "push_stages": {
            "validation_ready": partial_progress,
            "published_remote": partial_progress,
            "post_push_green": False,
        },
        "action_result": (
            result.to_dict() if hasattr(result, "to_dict") else {}
        ),
    }


def _next_command_guidance(next_command: str) -> str:
    """Render operator guidance directly from the typed next command."""
    if not next_command:
        return ""
    return f"Run `{next_command}` before creating another commit."


def _commit_recorded_pipeline_superseded(
    *,
    repo_root: Path,
    pipeline,
    status_view: dict[str, object],
) -> bool:
    """Return True when newer dirty work should supersede a recorded pipeline."""
    if str(getattr(pipeline, "state", "") or "").strip() != "commit_recorded":
        return False
    if str(status_view.get("current_head_sha") or "").strip() != str(
        getattr(pipeline, "commit_sha", "") or ""
    ).strip():
        return False
    push = scan_repo_governance_safely(repo_root).push_enforcement
    return requires_commit_before_push(push)
