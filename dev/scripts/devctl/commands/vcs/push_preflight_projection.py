"""Managed projection refresh helpers for governed push preflight."""

from __future__ import annotations

import sys
from pathlib import Path

from ...common import run_cmd
from ...config import REPO_ROOT
from ...runtime.review_snapshot_refresh import refresh_review_snapshot_file
from ...runtime.vcs import run_git_capture
from .push_preflight_commit import auto_commit_preflight_generated_changes
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
    _record_phase_state(
        state,
        "pre_validation_managed_projection_sync",
        result,
    )
    if not getattr(state, "errors", ()):
        run_pre_validation_recovery_loop_repair_phase(
            state,
            policy,
            repo_root=repo_root,
            command_runner=runner,
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


def auto_commit_review_snapshot_freshness_receipt(
    state,
    *,
    command_runner=run_cmd,
    repo_root: Path,
    next_step_label: str,
) -> dict[str, object]:
    """Run the governed snapshot receipt command after managed HEAD movement."""
    before_head = _current_head_sha(repo_root=repo_root)
    step = command_runner(
        "push-refresh-review-snapshot-receipt",
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "review-snapshot",
            "--write",
            "--receipt-commit",
            "--format",
            "json",
        ],
        cwd=repo_root,
    )
    if step.get("returncode", 1) != 0:
        detail = str(step.get("failure_output") or step.get("error") or "").strip()
        suffix = f": {detail}" if detail else ""
        state.errors.append(
            f"ReviewSnapshot receipt refresh failed before {next_step_label}{suffix}"
        )
        return {"ok": False, "committed": False, "step": step}

    after_head = _current_head_sha(repo_root=repo_root)
    committed = bool(after_head and after_head != before_head)
    if committed:
        state.warnings.append(
            "Committed ReviewSnapshot freshness receipt "
            f"{after_head[:12]} before {next_step_label}."
        )
    return {
        "ok": True,
        "committed": committed,
        "commit_sha": after_head if committed else "",
        "step": step,
    }


def refresh_preflight_generated_changes_before_authorization(
    state,
    policy,
    *,
    repo_root: Path,
    command_runner=run_cmd,
) -> None:
    """Commit preflight-generated drift and refresh projection receipts."""
    before_generated_commit = _current_head_sha(repo_root=repo_root)
    auto_commit_preflight_generated_changes(state, policy, repo_root=repo_root)
    generated_commit_moved_head = (
        bool(before_generated_commit)
        and _current_head_sha(repo_root=repo_root) != before_generated_commit
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


def _current_head_sha(*, repo_root: Path) -> str:
    code, stdout, _ = run_git_capture(["rev-parse", "HEAD"], repo_root=repo_root)
    return stdout.strip() if code == 0 else ""


def _record_phase_state(state, attr: str, result: dict[str, object]) -> None:
    try:
        setattr(state, attr, dict(result))
    except (AttributeError, TypeError):
        return


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
