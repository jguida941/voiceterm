"""Status-action helpers for `devctl review-channel`.

Handles the status action, bridge-status fallback, publisher/reviewer state
reads, and the shared status-context attachers used by both status and ensure.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ...review_channel.core import bridge_is_active, filter_provider_lanes
from ...review_channel.events import event_state_exists
from ...review_channel.event_store import (
    build_bridge_status_fallback_warning,
    summarize_review_state_errors,
)
from ...review_channel.lifecycle_state import (
    read_publisher_state,
    read_reviewer_supervisor_state,
)
from ...review_channel.reviewer_worker import (
    check_review_needed,
    reviewer_worker_tick_to_dict,
)
from ...repo_packs import active_path_config
from ...review_channel.state import (
    build_attach_auth_policy,
    projection_paths_to_dict,
    refresh_status_snapshot,
    build_service_identity,
)
from ..review_channel_bridge_handler import _run_bridge_action
from ..review_channel_command import (
    RuntimePaths,
    _coerce_runtime_paths,
    _event_report_error_detail,
)
from ..review_channel_event_handler import _run_event_action


def _read_publisher_state_safe(
    paths: RuntimePaths | Mapping[str, object],
) -> dict[str, object]:
    """Read publisher state without failing status."""
    runtime_paths = _coerce_runtime_paths(paths)

    if runtime_paths.status_dir is None:
        return {"running": False, "detail": "status_dir not resolved"}

    try:
        return read_publisher_state(runtime_paths.status_dir)
    except (OSError, ValueError):
        return {"running": False, "detail": "publisher state read failed"}


def _read_reviewer_supervisor_state_safe(
    paths: RuntimePaths | Mapping[str, object],
) -> dict[str, object]:
    """Read reviewer supervisor state without failing status."""
    runtime_paths = _coerce_runtime_paths(paths)

    if runtime_paths.status_dir is None:
        return {"running": False, "detail": "status_dir not resolved"}

    try:
        return read_reviewer_supervisor_state(runtime_paths.status_dir)
    except (OSError, ValueError):
        return {"running": False, "detail": "reviewer supervisor state read failed"}


def _attach_service_identity(
    report: dict[str, object],
    *,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> None:
    """Attach the repo/worktree service identity."""
    runtime_paths = _coerce_runtime_paths(paths)

    if runtime_paths.bridge_path is None:
        report["service_identity"] = None
        return

    if runtime_paths.review_channel_path is None:
        report["service_identity"] = None
        return

    if runtime_paths.status_dir is None:
        report["service_identity"] = None
        return

    report["service_identity"] = build_service_identity(
        repo_root=repo_root,
        bridge_path=runtime_paths.bridge_path,
        review_channel_path=runtime_paths.review_channel_path,
        output_root=runtime_paths.status_dir,
    )


def _attach_attach_auth_policy(report: dict[str, object]) -> None:
    """Attach the current attach/auth policy."""
    service_identity = report.get("service_identity")

    if not isinstance(service_identity, dict):
        report["attach_auth_policy"] = None
        return

    report["attach_auth_policy"] = build_attach_auth_policy(
        service_identity=service_identity,
    )


def _attach_backend_contract(
    report: dict[str, object],
    *,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> None:
    """Attach backend-contract metadata."""
    _attach_service_identity(report, repo_root=repo_root, paths=paths)
    _attach_attach_auth_policy(report)


def _attach_reviewer_worker(
    report: dict[str, object],
    *,
    repo_root: Path,
    bridge_path: Path | object,
) -> None:
    """Attach reviewer-worker status."""
    if not isinstance(bridge_path, Path):
        report["reviewer_worker"] = None
        return

    tick = check_review_needed(repo_root=repo_root, bridge_path=bridge_path)
    report["review_needed"] = tick.review_needed
    report["reviewer_worker"] = reviewer_worker_tick_to_dict(tick)


def _attach_status_context(
    report: dict[str, object],
    *,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> None:
    """Attach status-side lifecycle context."""
    runtime_paths = _coerce_runtime_paths(paths)

    report["publisher"] = _read_publisher_state_safe(runtime_paths)
    report["reviewer_supervisor"] = _read_reviewer_supervisor_state_safe(runtime_paths)

    _attach_backend_contract(report, repo_root=repo_root, paths=runtime_paths)

    if report.get("reviewer_worker") is None:
        _attach_reviewer_worker(
            report,
            repo_root=repo_root,
            bridge_path=runtime_paths.bridge_path,
        )


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
    return report, exit_code


def _refresh_bridge_status_report(
    report: dict[str, object],
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
) -> None:
    """Refresh the on-disk bridge-backed projection bundle for status reads."""
    bridge_path = paths.bridge_path if isinstance(paths.bridge_path, Path) else None
    review_channel_path, status_dir = _resolve_bridge_refresh_paths(
        repo_root=repo_root,
        paths=paths,
    )
    if bridge_path is None:
        return
    if review_channel_path is None or status_dir is None:
        return

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
    report["bridge_liveness"] = snapshot.bridge_liveness
    report["attention"] = snapshot.attention
    report["reviewer_worker"] = snapshot.reviewer_worker
    report["push_decision"] = snapshot.push_decision
    report["projection_paths"] = projection_paths_to_dict(snapshot.projection_paths)
    report["warnings"] = _merge_status_messages(
        report.get("warnings"),
        snapshot.warnings,
    )
    report["errors"] = _merge_status_messages(
        report.get("errors"),
        snapshot.errors,
    )
    if isinstance(snapshot.reviewer_worker, dict):
        report["review_needed"] = bool(snapshot.reviewer_worker.get("review_needed"))
    if report.get("errors"):
        report["ok"] = False


def _resolve_bridge_refresh_paths(
    *,
    repo_root: Path,
    paths: RuntimePaths,
) -> tuple[Path | None, Path | None]:
    """Resolve canonical refresh paths when callers pass partial runtime-path bundles."""
    config = active_path_config()
    review_channel_path = paths.review_channel_path
    if not isinstance(review_channel_path, Path):
        review_channel_path = repo_root / config.review_channel_rel
    status_dir = paths.status_dir
    if not isinstance(status_dir, Path):
        status_dir = repo_root / config.review_status_dir_rel
    return review_channel_path, status_dir


def _merge_status_messages(
    base_messages: object,
    refreshed_messages: list[str],
) -> list[str]:
    merged: list[str] = []
    if isinstance(base_messages, list):
        merged.extend(str(message) for message in base_messages)
    for message in refreshed_messages:
        if message not in merged:
            merged.append(message)
    return merged


def _auto_mode_prefers_markdown_bridge(paths: RuntimePaths) -> bool:
    """Prefer bridge-backed status when the transitional bridge is active."""
    bridge_path = paths.bridge_path
    review_channel_path = paths.review_channel_path
    if not isinstance(bridge_path, Path) or not isinstance(review_channel_path, Path):
        return False
    if not bridge_path.exists() or not review_channel_path.exists():
        return False
    try:
        return bridge_is_active(review_channel_path.read_text(encoding="utf-8"))
    except OSError:
        return False


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
    if execution_mode == "auto" and _auto_mode_prefers_markdown_bridge(runtime_paths):
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
