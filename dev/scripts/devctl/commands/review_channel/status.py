"""Status-action helpers for `devctl review-channel`.

Handles the status action, bridge-status fallback, publisher/reviewer state
reads, and the shared status-context attachers used by both status and ensure.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ...review_channel.core import filter_provider_lanes
from ...review_channel.events import event_state_exists
from ...review_channel.event_store import (
    build_bridge_status_fallback_warning,
    summarize_review_state_errors,
)
from ...repo_packs import active_path_config
from ...review_channel.projection_bundle import (
    canonical_projection_root_for_status_root,
)
from ...review_channel.state import (
    projection_paths_to_dict,
    read_publisher_state,
    read_reviewer_supervisor_state,
    refresh_status_snapshot,
)
from ...runtime.authority_snapshot import project_authority_snapshot
from .bridge_handler import _run_bridge_action
from . import status_context as _status_context_mod
from .status_bridge_sync import (
    bridge_current_session_drifted as _bridge_current_session_drifted,
    sync_bridge_from_typed_projection_if_needed as _sync_bridge_from_typed_projection_if_needed,
    without_bridge_current_session_drift as _without_bridge_current_session_drift,
)
from .status_context import (
    _attach_backend_contract,
    _attach_reviewer_worker,
    attach_status_context as _attach_status_context,
)
from .doctor_support import (
    attach_status_runtime_snapshot,
    build_doctor_report,
    resolve_status_recommended_command,
)
from .status_runtime_projection import (
    refresh_report_runtime_snapshot as _refresh_report_runtime_snapshot,
)
from .status_action_support import (
    auto_mode_prefers_markdown_bridge,
    dry_run_stale_heartbeat_projection_sync_requested,
    normalize_read_only_status_ok,
    read_review_state_sync_payload,
)
from ..review_channel_command import (
    RuntimePaths,
    _coerce_runtime_paths,
    _event_report_error_detail,
)
from ..review_channel_event_handler import _run_event_action
from .status_support import merge_status_messages, resolve_bridge_refresh_paths

_attach_backend_contract = _status_context_mod._attach_backend_contract
_attach_reviewer_worker = _status_context_mod._attach_reviewer_worker
_ORIG_ATTACH_STATUS_CONTEXT = _status_context_mod.attach_status_context
_ORIG_READ_PUBLISHER_STATE_SAFE = _status_context_mod._read_publisher_state_safe
_ORIG_READ_REVIEWER_SUPERVISOR_STATE_SAFE = (
    _status_context_mod._read_reviewer_supervisor_state_safe
)


def _read_publisher_state_safe(paths: RuntimePaths | Mapping[str, object]) -> dict[str, object]:
    _status_context_mod.read_publisher_state = read_publisher_state
    return _ORIG_READ_PUBLISHER_STATE_SAFE(paths)


def _read_reviewer_supervisor_state_safe(
    paths: RuntimePaths | Mapping[str, object],
) -> dict[str, object]:
    _status_context_mod.read_reviewer_supervisor_state = read_reviewer_supervisor_state
    return _ORIG_READ_REVIEWER_SUPERVISOR_STATE_SAFE(paths)


def _attach_status_context(
    report: dict[str, object],
    *,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> None:
    _sync_status_context_hooks()
    _ORIG_ATTACH_STATUS_CONTEXT(report, repo_root=repo_root, paths=paths)


def _run_bridge_status(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    extra_warnings: list[str] | None = None,
    report_execution_mode: str | None = None,
) -> tuple[dict, int]:
    """Run bridge-backed status and attach shared context."""
    runtime_paths = _coerce_runtime_paths(paths)
    report, exit_code = _run_bridge_action(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        extra_warnings=extra_warnings,
        report_execution_mode=report_execution_mode,
    )
    _refresh_bridge_status_report(
        report,
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
    )

    _attach_status_context(report, repo_root=repo_root, paths=runtime_paths)
    _refresh_report_runtime_snapshot(report)
    if not isinstance(report.get("authority_snapshot"), dict):
        project_authority_snapshot(report, caller_role="observer")
    recommended_command, command_source = resolve_status_recommended_command(report)
    report["recommended_command"] = recommended_command
    report["recommended_command_source"] = command_source
    normalize_read_only_status_ok(report)
    return report, exit_code


def _sync_status_context_hooks() -> None:
    _status_context_mod.read_publisher_state = read_publisher_state
    _status_context_mod.read_reviewer_supervisor_state = read_reviewer_supervisor_state
    _status_context_mod._attach_backend_contract = _attach_backend_contract
    _status_context_mod._attach_reviewer_worker = _attach_reviewer_worker
    _status_context_mod._read_publisher_state_safe = _read_publisher_state_safe
    _status_context_mod._read_reviewer_supervisor_state_safe = (
        _read_reviewer_supervisor_state_safe
    )


def _refresh_bridge_status_report(
    report: dict[str, object],
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
) -> None:
    """Refresh the on-disk bridge-backed projection bundle for status reads."""
    bridge_path = paths.bridge_path if isinstance(paths.bridge_path, Path) else None
    review_channel_path, status_dir = resolve_bridge_refresh_paths(
        repo_root=repo_root,
        paths=paths,
    )
    if bridge_path is None:
        return
    if review_channel_path is None or status_dir is None:
        return
    projection_root = canonical_projection_root_for_status_root(status_dir)
    prior_sync_review_state = read_review_state_sync_payload(
        projection_root / "review_state.json"
    )

    snapshot = refresh_status_snapshot(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=status_dir,
        promotion_plan_path=paths.promotion_plan_path,
        execution_mode=getattr(args, "execution_mode", "markdown-bridge"),
        warnings=[],
        errors=[],
        reviewer_overdue_threshold_seconds=getattr(
            args,
            "reviewer_overdue_seconds",
            None,
        ),
    )
    sync_warning = ""
    bridge_synced = False
    bridge_projection_sync_required = _bridge_current_session_drifted(
        snapshot.warnings,
        bridge_path=bridge_path,
        review_state_path=Path(snapshot.projection_paths.review_state_path),
        review_state_payload=prior_sync_review_state,
        bridge_liveness=snapshot.bridge_liveness,
    ) or dry_run_stale_heartbeat_projection_sync_requested(args, snapshot)
    if bridge_projection_sync_required:
        bridge_synced, sync_warning = _sync_bridge_from_typed_projection_if_needed(
            repo_root=repo_root,
            bridge_path=bridge_path,
            snapshot=snapshot,
        )
        if bridge_synced:
            snapshot = refresh_status_snapshot(
                repo_root=repo_root,
                bridge_path=bridge_path,
                review_channel_path=review_channel_path,
                output_root=status_dir,
                promotion_plan_path=paths.promotion_plan_path,
                execution_mode=getattr(args, "execution_mode", "markdown-bridge"),
                warnings=[
                    "Synchronized `bridge.md` from typed review-state during status refresh."
                ],
                errors=[],
                reviewer_overdue_threshold_seconds=getattr(
                    args,
                    "reviewer_overdue_seconds",
                    None,
                ),
            )
    report["bridge_liveness"] = snapshot.bridge_liveness
    report["attention"] = snapshot.attention
    report["reviewer_worker"] = snapshot.reviewer_worker
    report["push_decision"] = snapshot.push_decision
    report["projection_paths"] = projection_paths_to_dict(snapshot.projection_paths)
    report["_typed_review_state"] = snapshot.review_state
    attach_status_runtime_snapshot(report)
    if not isinstance(report.get("authority_snapshot"), dict):
        project_authority_snapshot(report, caller_role="observer")
    recommended_command, command_source = resolve_status_recommended_command(report)
    report["recommended_command"] = recommended_command
    report["recommended_command_source"] = command_source
    existing_warnings = report.get("warnings")
    if bridge_synced:
        existing_warnings = _without_bridge_current_session_drift(existing_warnings)
    report["warnings"] = merge_status_messages(
        existing_warnings,
        merge_status_messages(
            snapshot.warnings,
            [sync_warning] if sync_warning else [],
        ),
    )
    report["errors"] = merge_status_messages(
        report.get("errors"),
        snapshot.errors,
    )
    normalize_read_only_status_ok(report)
    if isinstance(snapshot.reviewer_worker, dict):
        report["review_needed"] = bool(snapshot.reviewer_worker.get("review_needed"))
    if report.get("errors"):
        report["ok"] = False


def _run_status_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Run status with event-backed fallback."""
    runtime_paths = _coerce_runtime_paths(paths)
    artifact_paths = runtime_paths.artifact_paths
    execution_mode = getattr(args, "execution_mode", "auto")
    if execution_mode == "auto" and auto_mode_prefers_markdown_bridge(runtime_paths):
        execution_mode = "markdown-bridge"
    fallback_warnings: list[str] = []

    if (
        execution_mode != "markdown-bridge"
        and artifact_paths is not None
        and event_state_exists(artifact_paths)
    ):
        try:
            report, exit_code = _run_event_action(
                args=args,
                repo_root=repo_root,
                paths=runtime_paths,
            )
        except (OSError, ValueError) as exc:
            fallback_warnings.append(build_bridge_status_fallback_warning(str(exc)))
        else:
            state_errors = summarize_review_state_errors(
                {"ok": report.get("ok"), "errors": report.get("errors")}
            )

            if exit_code == 0 and state_errors is None:
                _attach_status_context(
                    report,
                    repo_root=repo_root,
                    paths=runtime_paths,
                )
                attach_status_runtime_snapshot(report)
                recommended_command, command_source = resolve_status_recommended_command(
                    report
                )
                report["recommended_command"] = recommended_command
                report["recommended_command_source"] = command_source
                if not isinstance(report.get("authority_snapshot"), dict):
                    project_authority_snapshot(report, caller_role="observer")
                normalize_read_only_status_ok(report)
                return report, exit_code

            fallback_warnings.append(
                build_bridge_status_fallback_warning(
                    state_errors or _event_report_error_detail(report)
                )
            )

    if not fallback_warnings:
        return _run_bridge_status(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
        )

    try:
        return _run_bridge_status(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
            extra_warnings=fallback_warnings,
            report_execution_mode="markdown-bridge",
        )
    except ValueError as exc:
        raise ValueError(
            f"{fallback_warnings[-1]} Markdown-bridge fallback was unavailable: {exc}"
        ) from exc


def _run_doctor_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Run doctor by reusing the canonical status path and reducing the payload."""
    status_report, exit_code = _run_status_action(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    attach_status_runtime_snapshot(status_report)
    return build_doctor_report(status_report=status_report, exit_code=exit_code)
