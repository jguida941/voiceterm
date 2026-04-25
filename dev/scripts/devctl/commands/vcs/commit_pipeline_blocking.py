"""Helpers for governed-commit reports blocked by an active publish pipeline."""

from __future__ import annotations

from pathlib import Path

from ...runtime.post_checkpoint_dirty_support import requires_commit_before_push
from ...runtime.governance_scan import scan_repo_governance_safely
from ..pipeline.refresh_authorization_action import apply_refresh_authorization
from ..pipeline.status_action import build_status_view
from ..pipeline.support import resolve_pipeline_paths
from .commit_visibility import commit_visibility_payload
from .governed_executor_actions import _build_report

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
