"""Managed projection refresh helpers for governed push preflight."""

from __future__ import annotations

import sys
from pathlib import Path

from ...common import run_cmd
from ...config import REPO_ROOT
from ...repo_packs import active_path_config
from ...review_channel.event_reducer import load_or_refresh_event_bundle
from ...review_channel.event_store import resolve_artifact_paths
from ...review_channel.state import refresh_status_snapshot
from ...runtime.review_snapshot_refresh import refresh_review_snapshot_file
from ...runtime.vcs import run_git_capture
from .push_preflight_commit import auto_commit_preflight_generated_changes
from .push_projection_receipt import auto_commit_managed_projection_receipt


def refresh_managed_projections_before_preflight(
    state,
    policy,
    *,
    repo_root: Path = REPO_ROOT,
    command_runner=None,
) -> dict[str, object]:
    """Refresh ReviewSnapshot and commit managed projection drift before preflight."""
    warnings = refresh_review_snapshot_file(repo_root=repo_root)
    state.warnings.extend(warning for warning in warnings if warning)
    receipt_result = auto_commit_managed_projection_receipt(
        state,
        policy,
        repo_root=repo_root,
    )
    if not isinstance(receipt_result, dict):
        receipt_result = {}
    result = {
        "ok": bool(receipt_result.get("ok", True)),
        "receipt_committed": bool(receipt_result.get("committed"))
        or bool(str(receipt_result.get("commit_sha", "") or "").strip()),
        "paths": tuple(str(path) for path in receipt_result.get("paths", ()) or ()),
        "snapshot_warning_count": len([warning for warning in warnings if warning]),
    }
    if result["receipt_committed"] and not getattr(state, "errors", ()):
        refresh_runtime_surfaces_after_projection_receipt(
            state,
            command_runner=run_cmd if command_runner is None else command_runner,
            repo_root=repo_root,
            next_step_label="push preflight",
        )
        if getattr(state, "errors", ()):
            return result
        snapshot_receipt = auto_commit_review_snapshot_freshness_receipt(
            state,
            command_runner=run_cmd if command_runner is None else command_runner,
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
                command_runner=run_cmd if command_runner is None else command_runner,
                repo_root=repo_root,
                next_step_label="push preflight snapshot receipt",
            )
    return result


def refresh_runtime_surfaces_after_projection_receipt(
    state,
    *,
    command_runner,
    repo_root: Path,
    next_step_label: str,
) -> None:
    """Refresh freshness-guard inputs after a managed receipt moves HEAD."""
    if not _refresh_review_channel_projection_bundle_after_projection_receipt(
        state,
        repo_root=repo_root,
        next_step_label=next_step_label,
    ):
        return
    refresh_steps = (
        (
            "push-refresh-startup-context",
            (
                sys.executable,
                "dev/scripts/devctl.py",
                "startup-context",
                "--format",
                "summary",
            ),
            "startup-context",
        ),
        (
            "push-refresh-context-graph",
            (
                sys.executable,
                "dev/scripts/devctl.py",
                "context-graph",
                "--mode",
                "bootstrap",
                "--format",
                "md",
            ),
            "context-graph",
        ),
    )
    for step_name, command, label in refresh_steps:
        step = command_runner(step_name, list(command), cwd=repo_root)
        if step.get("returncode", 1) != 0:
            state.errors.append(
                "Managed projection receipt moved HEAD, but "
                f"{label} refresh failed before {next_step_label}."
            )
            return
    state.warnings.append(
        "Refreshed startup-context and context-graph after managed projection "
        f"receipt before {next_step_label}."
    )


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


def _receipt_result_committed(receipt_result: object) -> bool:
    if not isinstance(receipt_result, dict):
        return False
    return bool(receipt_result.get("committed")) or bool(
        str(receipt_result.get("commit_sha", "") or "").strip()
    )


def _current_head_sha(*, repo_root: Path) -> str:
    code, stdout, _ = run_git_capture(["rev-parse", "HEAD"], repo_root=repo_root)
    return stdout.strip() if code == 0 else ""


def _refresh_review_channel_projection_bundle_after_projection_receipt(
    state,
    *,
    repo_root: Path,
    next_step_label: str,
) -> bool:
    """Keep review-state sibling projections on the same proof tick as HEAD."""
    config = active_path_config()
    review_channel_path = repo_root / config.review_channel_rel
    if not review_channel_path.is_file():
        return True
    try:
        artifact_paths = resolve_artifact_paths(repo_root=repo_root)
        event_log_path = Path(artifact_paths.event_log_path)
        state_path = Path(artifact_paths.state_path)
        if event_log_path.exists() or state_path.exists():
            load_or_refresh_event_bundle(
                repo_root=repo_root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )
            state.warnings.append(
                "Refreshed review-channel projections after managed projection "
                f"receipt before {next_step_label}."
            )
            return True
        bridge_path = repo_root / config.bridge_rel
        if bridge_path.is_file():
            refresh_status_snapshot(
                repo_root=repo_root,
                bridge_path=bridge_path,
                review_channel_path=review_channel_path,
                output_root=repo_root / config.review_status_dir_rel,
            )
            state.warnings.append(
                "Refreshed bridge-backed review projections after managed "
                f"projection receipt before {next_step_label}."
            )
    except (OSError, ValueError) as exc:
        state.errors.append(
            "Managed projection receipt moved HEAD, but review-channel "
            f"projection refresh failed before {next_step_label}: {exc}"
        )
        return False
    return True


__all__ = [
    "auto_commit_managed_projection_receipt_before_authorization",
    "auto_commit_review_snapshot_freshness_receipt",
    "refresh_managed_projections_before_preflight",
    "refresh_preflight_generated_changes_before_authorization",
    "refresh_runtime_surfaces_after_projection_receipt",
]
