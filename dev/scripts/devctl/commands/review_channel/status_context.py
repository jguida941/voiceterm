"""Shared status-context attachers for review-channel status/doctor."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ...review_channel.lifecycle_state import (
    read_publisher_state,
    read_reviewer_supervisor_state,
)
from ...review_channel.reviewer_worker import (
    check_review_needed,
    reviewer_worker_tick_to_dict,
)
from ...review_channel.state import (
    build_attach_auth_policy,
    build_service_identity,
)
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths


def attach_status_context(
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


def _read_publisher_state_safe(
    paths: RuntimePaths | Mapping[str, object],
) -> dict[str, object]:
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
    runtime_paths = _coerce_runtime_paths(paths)
    if runtime_paths.status_dir is None:
        return {"running": False, "detail": "status_dir not resolved"}
    try:
        return read_reviewer_supervisor_state(runtime_paths.status_dir)
    except (OSError, ValueError):
        return {"running": False, "detail": "reviewer supervisor state read failed"}


def _attach_backend_contract(
    report: dict[str, object],
    *,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> None:
    _attach_service_identity(report, repo_root=repo_root, paths=paths)
    _attach_attach_auth_policy(report)


def _attach_service_identity(
    report: dict[str, object],
    *,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> None:
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
    service_identity = report.get("service_identity")
    if not isinstance(service_identity, dict):
        report["attach_auth_policy"] = None
        return
    report["attach_auth_policy"] = build_attach_auth_policy(
        service_identity=service_identity,
    )


def _attach_reviewer_worker(
    report: dict[str, object],
    *,
    repo_root: Path,
    bridge_path: Path | object,
) -> None:
    if not isinstance(bridge_path, Path):
        report["reviewer_worker"] = None
        return
    tick = check_review_needed(repo_root=repo_root, bridge_path=bridge_path)
    report["review_needed"] = tick.review_needed
    report["reviewer_worker"] = reviewer_worker_tick_to_dict(tick)
