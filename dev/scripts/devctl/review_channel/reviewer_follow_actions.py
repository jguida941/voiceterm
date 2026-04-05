"""Shared report-refresh helpers for reviewer follow-loop automation."""

from __future__ import annotations

from pathlib import Path

from .follow_loop import build_claude_progress_token
from .reviewer_follow_runtime import attach_reviewer_runtime_contract


def refresh_follow_report(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    bridge_path: Path,
    build_reviewer_state_report_fn,
) -> tuple[dict, int]:
    report, frame_exit_code = build_reviewer_state_report_fn(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    attach_reviewer_runtime_contract(
        report=report,
        bridge_path=bridge_path,
        status_dir=paths.get("status_dir"),
    )
    return report, frame_exit_code


def apply_auto_action(
    *,
    action_key: str,
    success_key: str,
    action_payload: dict[str, object] | None,
    report: dict[str, object],
    frame_exit_code: int,
    progress_token: str,
    args,
    repo_root: Path,
    paths: dict[str, object],
    bridge_path: Path,
    build_reviewer_state_report_fn,
) -> tuple[dict, int, str]:
    if action_payload is None:
        return report, frame_exit_code, progress_token
    report[action_key] = action_payload
    if not bool(action_payload.get(success_key)):
        return report, frame_exit_code, progress_token
    report, frame_exit_code = refresh_follow_report(
        args=args,
        repo_root=repo_root,
        paths=paths,
        bridge_path=bridge_path,
        build_reviewer_state_report_fn=build_reviewer_state_report_fn,
    )
    report[action_key] = action_payload
    return report, frame_exit_code, build_claude_progress_token(
        repo_root=repo_root,
        bridge_path=bridge_path,
    )
