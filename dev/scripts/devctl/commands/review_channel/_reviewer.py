"""Reviewer-state report builder for the review-channel command package."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ...review_channel.core import filter_provider_lanes
from ...review_channel.plan_resolution import resolve_promotion_plan_path
from ..review_channel_bridge_render import build_bridge_success_report
from ...review_channel.reviewer_state import (
    ReviewerCheckpointUpdate,
    reviewer_state_write_to_dict,
    write_reviewer_checkpoint,
    write_reviewer_heartbeat,
)
from ..review_channel_command import (
    REVIEWER_STATE_REPORT_DEFAULTS,
    ReviewChannelAction,
    RuntimePaths,
    _coerce_action,
    _coerce_runtime_paths,
)
from ..review_channel_command.reviewer_support import resolve_checkpoint_instruction
from ..review_channel_command.reviewer_support import resolve_checkpoint_body
from .status import _attach_backend_contract


def build_reviewer_state_report(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Build the current reviewer-state report."""
    from . import refresh_status_snapshot

    runtime_paths = _coerce_runtime_paths(paths)
    assert runtime_paths.bridge_path is not None
    assert runtime_paths.review_channel_path is not None
    assert runtime_paths.status_dir is not None
    plan_resolution = resolve_promotion_plan_path(
        repo_root=repo_root,
        bridge_path=runtime_paths.bridge_path,
        explicit_plan_path=runtime_paths.promotion_plan_path,
    )

    status_snapshot = refresh_status_snapshot(
        repo_root=repo_root,
        bridge_path=runtime_paths.bridge_path,
        review_channel_path=runtime_paths.review_channel_path,
        output_root=runtime_paths.status_dir,
        promotion_plan_path=plan_resolution.path,
        execution_mode=args.execution_mode,
        warnings=[],
        errors=[],
    )

    codex_lanes = filter_provider_lanes(status_snapshot.lanes, provider="codex")
    claude_lanes = filter_provider_lanes(status_snapshot.lanes, provider="claude")
    report, exit_code = build_bridge_success_report(
        args=args,
        bridge_liveness=status_snapshot.bridge_liveness,
        attention=status_snapshot.attention,
        reviewer_worker=status_snapshot.reviewer_worker,
        codex_lanes=codex_lanes,
        claude_lanes=claude_lanes,
        warnings=status_snapshot.warnings,
        projection_paths=status_snapshot.projection_paths,
        **REVIEWER_STATE_REPORT_DEFAULTS,
    )

    _attach_backend_contract(report, repo_root=repo_root, paths=runtime_paths)
    if args.action in {"reviewer-heartbeat", "reviewer-checkpoint"}:
        report["ok"] = True
        report["exit_ok"] = True
        report["exit_code"] = 0
        return report, 0
    return report, exit_code


def run_reviewer_state_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    run_reviewer_follow_action_fn,
) -> tuple[dict, int]:
    """Run one reviewer heartbeat/checkpoint write."""
    action = _coerce_action(args.action)
    runtime_paths = _coerce_runtime_paths(paths)
    auto_instruction_candidate = None

    if (
        action is ReviewChannelAction.REVIEWER_HEARTBEAT
        and getattr(args, "follow", False)
    ):
        return run_reviewer_follow_action_fn(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
        )

    assert runtime_paths.bridge_path is not None

    if action is ReviewChannelAction.REVIEWER_HEARTBEAT:
        state_write = write_reviewer_heartbeat(
            repo_root=repo_root,
            bridge_path=runtime_paths.bridge_path,
            reviewer_mode=args.reviewer_mode,
            reason=args.reason,
        )
    else:
        verdict_body = resolve_checkpoint_body(
            repo_root=repo_root,
            inline_value=getattr(args, "verdict", None),
            file_value=getattr(args, "verdict_file", None),
            inline_flag="--verdict",
            file_flag="--verdict-file",
        )
        open_findings_body = resolve_checkpoint_body(
            repo_root=repo_root,
            inline_value=getattr(args, "open_findings", None),
            file_value=getattr(args, "open_findings_file", None),
            inline_flag="--open-findings",
            file_flag="--open-findings-file",
        )
        instruction_body = resolve_checkpoint_body(
            repo_root=repo_root,
            inline_value=getattr(args, "instruction", None),
            file_value=getattr(args, "instruction_file", None),
            inline_flag="--instruction",
            file_flag="--instruction-file",
        )
        checkpoint_instruction, auto_instruction_candidate = (
            resolve_checkpoint_instruction(
                repo_root=repo_root,
                bridge_path=runtime_paths.bridge_path,
                promotion_plan_path=runtime_paths.promotion_plan_path,
                instruction=instruction_body,
            )
        )
        state_write = write_reviewer_checkpoint(
            repo_root=repo_root,
            bridge_path=runtime_paths.bridge_path,
            reviewer_mode=args.reviewer_mode,
            reason=args.reason,
            checkpoint=ReviewerCheckpointUpdate(
                current_verdict=verdict_body,
                open_findings=open_findings_body,
                current_instruction=checkpoint_instruction,
                reviewed_scope_items=tuple(args.reviewed_scope_item),
                rotate_instruction_revision=bool(
                    getattr(args, "rotate_instruction_revision", False)
                ),
                expected_instruction_revision=getattr(
                    args,
                    "expected_instruction_revision",
                    None,
                ),
            ),
        )

    report, exit_code = build_reviewer_state_report(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
    )

    report["reviewer_state_write"] = reviewer_state_write_to_dict(state_write)
    if action is ReviewChannelAction.REVIEWER_CHECKPOINT:
        report["instruction_auto_promoted"] = bool(
            auto_instruction_candidate is not None
        )
        if auto_instruction_candidate is not None:
            report["instruction_auto_promoted_source"] = {
                "source_path": auto_instruction_candidate.source_path,
                "checklist_item": auto_instruction_candidate.checklist_item,
            }
    return report, exit_code
