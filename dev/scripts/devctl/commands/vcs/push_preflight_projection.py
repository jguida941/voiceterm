"""Managed projection refresh helpers for governed push preflight."""

from __future__ import annotations

from pathlib import Path

from ...common import run_cmd
from ...config import REPO_ROOT
from ...runtime.review_snapshot_refresh import refresh_review_snapshot_file
from .push_preflight_commit import auto_commit_preflight_generated_changes
from .push_preflight_snapshot_receipt import (
    auto_commit_review_snapshot_freshness_receipt,
    current_head_sha,
)
from .push_review_snapshot_receipt_guard import (
    current_head_is_managed_review_snapshot_receipt,
)
from .push_projection_runtime_refresh import (
    refresh_stale_reviewer_heartbeat_before_publication,
    refresh_runtime_surfaces_after_projection_receipt,
)
from .push_projection_receipt import auto_commit_managed_projection_receipt
from .push_recovery_loop_repair import run_pre_validation_recovery_loop_repair_phase
from .push_render_surface_sync import (
    POLICY_RENDER_SURFACE_SYNC,
    refresh_policy_owned_render_surfaces_before_preflight,
    render_surface_pre_validation_fields,
)

PRE_VALIDATION_MANAGED_PROJECTION_SYNC = "pre_validation_managed_projection_sync"


def refresh_managed_projections_before_preflight(
    state,
    policy,
    *,
    repo_root: Path = REPO_ROOT,
    command_runner=None,
    quality_policy_path: str | None = None,
) -> dict[str, object]:
    """Refresh ReviewSnapshot and commit managed projection drift before preflight."""
    runner = run_cmd if command_runner is None else command_runner
    render_result = refresh_policy_owned_render_surfaces_before_preflight(
        state,
        policy,
        repo_root=repo_root,
        command_runner=runner,
        quality_policy_path=quality_policy_path,
    )
    if getattr(state, "errors", ()):
        result = _base_pre_validation_result(render_result=render_result)
        result["status"] = "blocked"
        result["ok"] = False
        _record_phase_state(state, PRE_VALIDATION_MANAGED_PROJECTION_SYNC, result)
        return result
    result = _base_pre_validation_result(render_result=render_result)
    if current_head_is_managed_review_snapshot_receipt(repo_root=repo_root):
        errors_before_refresh = len(getattr(state, "errors", ()))
        refresh_runtime_surfaces_after_projection_receipt(
            state,
            command_runner=runner,
            repo_root=repo_root,
            next_step_label="push preflight receipt head",
            repo_pack_id=str(getattr(policy, "repo_pack_id", "") or ""),
        )
        result["status"] = "completed"
        result["ok"] = True
        result["reason"] = "managed_review_snapshot_receipt_head"
        refresh_errors = tuple(getattr(state, "errors", ())[errors_before_refresh:])
        if refresh_errors:
            del state.errors[errors_before_refresh:]
            state.warnings.extend(refresh_errors)
        result["runtime_surfaces_refreshed"] = not bool(refresh_errors)
        result["runtime_surface_refresh_warnings"] = refresh_errors
        result["receipt_committed"] = False
        result["paths"] = ()
        result["snapshot_warning_count"] = 0
        return _finish_pre_validation_managed_projection_sync(
            state,
            policy,
            result,
            repo_root=repo_root,
            command_runner=runner,
        )
    heartbeat_result = refresh_stale_reviewer_heartbeat_before_publication(
        state,
        command_runner=runner,
        repo_root=repo_root,
        next_step_label="push preflight",
    )
    if heartbeat_result.get("status") != "skipped":
        result["reviewer_heartbeat_refresh"] = heartbeat_result
    if getattr(state, "errors", ()):
        result["status"] = "blocked"
        result["ok"] = False
        _record_phase_state(state, PRE_VALIDATION_MANAGED_PROJECTION_SYNC, result)
        return result
    warnings = refresh_review_snapshot_file(repo_root=repo_root)
    state.warnings.extend(warning for warning in warnings if warning)
    receipt_result = auto_commit_managed_projection_receipt(
        state,
        policy,
        repo_root=repo_root,
    )
    if not isinstance(receipt_result, dict):
        receipt_result = {}
    result["status"] = (
        "completed" if bool(receipt_result.get("ok", True)) else "failed"
    )
    result["ok"] = bool(receipt_result.get("ok", True))
    result["receipt_committed"] = bool(receipt_result.get("committed")) or bool(
        str(receipt_result.get("commit_sha", "") or "").strip()
    )
    result["paths"] = tuple(
        str(path) for path in receipt_result.get("paths", ()) or ()
    )
    result["snapshot_warning_count"] = len(
        [warning for warning in warnings if warning]
    )
    if result["receipt_committed"] and not getattr(state, "errors", ()):
        refresh_runtime_surfaces_after_projection_receipt(
            state,
            command_runner=runner,
            repo_root=repo_root,
            next_step_label="push preflight",
            repo_pack_id=str(getattr(policy, "repo_pack_id", "") or ""),
        )
        if getattr(state, "errors", ()):
            return result
        snapshot_receipt = auto_commit_review_snapshot_freshness_receipt(
            state,
            command_runner=runner,
            repo_root=repo_root,
            next_step_label="push preflight",
        )
        result["snapshot_receipt_committed"] = bool(snapshot_receipt.get("committed"))
        result["snapshot_receipt_commit_sha"] = str(
            snapshot_receipt.get("commit_sha", "") or ""
        )
        if snapshot_receipt.get("committed") and not getattr(state, "errors", ()):
            refresh_runtime_surfaces_after_projection_receipt(
                state,
                command_runner=runner,
                repo_root=repo_root,
                next_step_label="push preflight snapshot receipt",
                repo_pack_id=str(getattr(policy, "repo_pack_id", "") or ""),
            )
    elif render_result.get("committed") and not getattr(state, "errors", ()):
        refresh_runtime_surfaces_after_projection_receipt(
            state,
            command_runner=runner,
            repo_root=repo_root,
            next_step_label="push preflight generated-surface receipt",
            repo_pack_id=str(getattr(policy, "repo_pack_id", "") or ""),
        )
    return _finish_pre_validation_managed_projection_sync(
        state,
        policy,
        result,
        repo_root=repo_root,
        command_runner=runner,
    )


def _finish_pre_validation_managed_projection_sync(
    state,
    policy,
    result: dict[str, object],
    *,
    repo_root: Path,
    command_runner,
) -> dict[str, object]:
    _merge_existing_phase_state(
        result,
        getattr(state, "pre_validation_managed_projection_sync", {}),
    )
    recovery_record = getattr(
        state,
        "pre_validation_recovery_loop_repair_startup",
        {},
    )
    if isinstance(recovery_record, dict) and recovery_record:
        result["startup_context_recovery_required"] = bool(
            recovery_record.get("required")
        )
        result["startup_context_recovery"] = dict(recovery_record)
    if getattr(state, "errors", ()):
        result["status"] = "blocked"
        result["ok"] = False
    _record_phase_state(
        state,
        "pre_validation_managed_projection_sync",
        result,
    )
    if not getattr(state, "errors", ()):
        recovery_result = run_pre_validation_recovery_loop_repair_phase(
            state,
            policy,
            repo_root=repo_root,
            command_runner=command_runner,
        )
        if (
            isinstance(recovery_result, dict)
            and recovery_result.get("status") != "not_needed"
        ):
            result["pre_validation_recovery_loop_repair"] = dict(recovery_result)
        if getattr(state, "errors", ()):
            result["status"] = "blocked"
            result["ok"] = False
            _record_phase_state(
                state,
                "pre_validation_managed_projection_sync",
                result,
            )
    return result


def auto_commit_managed_projection_receipt_before_authorization(
    state,
    policy,
    *,
    repo_root: Path,
    command_runner=run_cmd,
) -> dict[str, object]:
    """Commit managed projection drift and refresh proof inputs before auth."""
    receipt_result = auto_commit_managed_projection_receipt(
        state,
        policy,
        repo_root=repo_root,
    )
    if not state.errors and _receipt_result_committed(receipt_result):
        refresh_runtime_surfaces_after_projection_receipt(
            state,
            command_runner=command_runner,
            repo_root=repo_root,
            next_step_label="publication authorization",
            repo_pack_id=str(getattr(policy, "repo_pack_id", "") or ""),
        )
        if not state.errors:
            auto_commit_review_snapshot_freshness_receipt(
                state,
                command_runner=command_runner,
                repo_root=repo_root,
                next_step_label="publication authorization",
            )
    return receipt_result


def refresh_preflight_generated_changes_before_authorization(
    state,
    policy,
    *,
    repo_root: Path,
    command_runner=run_cmd,
) -> None:
    """Commit preflight-generated drift and refresh projection receipts."""
    before_generated_commit = current_head_sha(repo_root=repo_root)
    auto_commit_preflight_generated_changes(state, policy, repo_root=repo_root)
    generated_commit_moved_head = (
        bool(before_generated_commit)
        and current_head_sha(repo_root=repo_root) != before_generated_commit
    )
    receipt_result = auto_commit_managed_projection_receipt_before_authorization(
        state,
        policy,
        repo_root=repo_root,
        command_runner=command_runner,
    )
    if (
        generated_commit_moved_head
        and not state.errors
        and not _receipt_result_committed(receipt_result)
    ):
        auto_commit_review_snapshot_freshness_receipt(
            state,
            command_runner=command_runner,
            repo_root=repo_root,
            next_step_label="publication authorization",
        )


def repair_preflight_generated_changes_for_push(
    state,
    policy,
    *,
    repo_root: Path,
) -> None:
    """Run the real push repair path with the repo-owned command runner."""
    refresh_preflight_generated_changes_before_authorization(
        state,
        policy,
        repo_root=repo_root,
        command_runner=run_cmd,
    )


def _receipt_result_committed(receipt_result: object) -> bool:
    if not isinstance(receipt_result, dict):
        return False
    return bool(receipt_result.get("committed")) or bool(
        str(receipt_result.get("commit_sha", "") or "").strip()
    )


def _base_pre_validation_result(
    *,
    render_result: dict[str, object],
) -> dict[str, object]:
    result: dict[str, object] = {}
    result["phase"] = PRE_VALIDATION_MANAGED_PROJECTION_SYNC
    result["allowed"] = True
    result.update(render_surface_pre_validation_fields(render_result))
    return result


def _record_phase_state(state, attr: str, result: dict[str, object]) -> None:
    try:
        setattr(state, attr, dict(result))
    except (AttributeError, TypeError):
        return


def _merge_existing_phase_state(
    result: dict[str, object],
    existing: object,
) -> None:
    if not isinstance(existing, dict):
        return
    for key in (
        "startup_context_checkpoint_gate_deferred",
        "startup_context_checkpoint_gate",
    ):
        if key in existing:
            result[key] = existing[key]


__all__ = [
    "auto_commit_managed_projection_receipt_before_authorization",
    "auto_commit_review_snapshot_freshness_receipt",
    "PRE_VALIDATION_MANAGED_PROJECTION_SYNC",
    "POLICY_RENDER_SURFACE_SYNC",
    "repair_preflight_generated_changes_for_push",
    "refresh_managed_projections_before_preflight",
    "refresh_policy_owned_render_surfaces_before_preflight",
    "refresh_preflight_generated_changes_before_authorization",
    "refresh_stale_reviewer_heartbeat_before_publication",
    "refresh_runtime_surfaces_after_projection_receipt",
]
