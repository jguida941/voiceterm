"""Reviewer-state report builder for the review-channel command package."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from ...review_channel.core import filter_provider_lanes
from ...review_channel.peer_liveness import reviewer_mode_is_active
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
from ..review_channel_command.reviewer_support import resolve_checkpoint_payload_file
from ._stop import run_stop_action as _run_stop_action
from .reviewer_runtime_snapshot import attach_reviewer_runtime_snapshot
from .status import _attach_backend_contract


def build_reviewer_state_report(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    reviewer_accepted_implementer_state_hash_override: str | None = None,
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
        reviewer_accepted_implementer_state_hash_override=(
            reviewer_accepted_implementer_state_hash_override
        ),
    )

    codex_lanes = filter_provider_lanes(status_snapshot.lanes, provider="codex")
    claude_lanes = filter_provider_lanes(status_snapshot.lanes, provider="claude")
    report, exit_code = build_bridge_success_report(
        args=args,
        bridge_liveness=status_snapshot.bridge_liveness,
        attention=status_snapshot.attention,
        reviewer_worker=status_snapshot.reviewer_worker,
        collaboration=(
            asdict(status_snapshot.review_state.collaboration)
            if status_snapshot.review_state is not None
            and status_snapshot.review_state.collaboration is not None
            else None
        ),
        codex_lanes=codex_lanes,
        claude_lanes=claude_lanes,
        warnings=status_snapshot.warnings,
        projection_paths=status_snapshot.projection_paths,
        **REVIEWER_STATE_REPORT_DEFAULTS,
    )

    _attach_backend_contract(report, repo_root=repo_root, paths=runtime_paths)
    attach_reviewer_runtime_snapshot(
        report,
        review_state=status_snapshot.review_state,
        attention=status_snapshot.attention,
    )
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
        checkpoint_payload_file = getattr(args, "checkpoint_payload_file", None)
        if checkpoint_payload_file:
            payload = resolve_checkpoint_payload_file(
                repo_root=repo_root,
                file_value=checkpoint_payload_file,
            )
            verdict_body = payload.verdict
            open_findings_body = payload.open_findings
            instruction_body = payload.instruction
            reviewed_scope_items = payload.reviewed_scope_items
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
            reviewed_scope_items = tuple(args.reviewed_scope_item)
        checkpoint_instruction, auto_instruction_candidate = (
            resolve_checkpoint_instruction(
                repo_root=repo_root,
                bridge_path=runtime_paths.bridge_path,
                promotion_plan_path=runtime_paths.promotion_plan_path,
                instruction=instruction_body,
            )
        )
        # Reviewer actor defaults to Codex (the canonical reviewer in this
        # repo-pack). Explicit `--actor claude` selects the symmetric Claude
        # reviewer path so the inbox gate checks the correct inbox.
        raw_actor = getattr(args, "actor", None)
        actor_value = (raw_actor or "").strip() or "codex"
        state_write = write_reviewer_checkpoint(
            repo_root=repo_root,
            bridge_path=runtime_paths.bridge_path,
            reviewer_mode=args.reviewer_mode,
            reason=args.reason,
            checkpoint=ReviewerCheckpointUpdate(
                current_verdict=verdict_body,
                open_findings=open_findings_body,
                current_instruction=checkpoint_instruction,
                reviewed_scope_items=reviewed_scope_items,
                rotate_instruction_revision=bool(
                    getattr(args, "rotate_instruction_revision", False)
                ),
                expected_instruction_revision=getattr(
                    args,
                    "expected_instruction_revision",
                    None,
                ),
                expected_implementer_state_hash=getattr(
                    args,
                    "expected_implementer_state_hash",
                    None,
                ),
                actor=actor_value,
                allow_unread_inbox=bool(
                    getattr(args, "allow_unread_inbox", False)
                ),
            ),
        )

    lifecycle_stop_report, lifecycle_stop_exit_code = _maybe_stop_detached_review_runtime(
        action=action,
        args=args,
        repo_root=repo_root,
        runtime_paths=runtime_paths,
    )
    report, exit_code = build_reviewer_state_report(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        reviewer_accepted_implementer_state_hash_override=(
            state_write.reviewer_accepted_implementer_state_hash
        ),
    )

    report["reviewer_state_write"] = reviewer_state_write_to_dict(state_write)
    if lifecycle_stop_report is not None:
        report["lifecycle_stop"] = lifecycle_stop_report
    if action is ReviewChannelAction.REVIEWER_CHECKPOINT:
        report["instruction_auto_promoted"] = bool(
            auto_instruction_candidate is not None
        )
        if auto_instruction_candidate is not None:
            report["instruction_auto_promoted_source"] = {
                "source_path": auto_instruction_candidate.source_path,
                "checklist_item": auto_instruction_candidate.checklist_item,
            }
    if lifecycle_stop_exit_code != 0:
        errors = list(report.get("errors") or [])
        errors.extend(
            str(item)
            for item in (lifecycle_stop_report or {}).get("errors", [])
            if str(item).strip()
        )
        report["errors"] = errors
        report["ok"] = False
        report["exit_ok"] = False
        report["exit_code"] = 1
        return report, 1
    return report, exit_code


def _maybe_stop_detached_review_runtime(
    *,
    action: ReviewChannelAction,
    args,
    repo_root: Path,
    runtime_paths: RuntimePaths,
) -> tuple[dict[str, object] | None, int]:
    """Retire detached follow daemons when a reviewer takes local single-agent control."""
    if action not in {
        ReviewChannelAction.REVIEWER_HEARTBEAT,
        ReviewChannelAction.REVIEWER_CHECKPOINT,
    }:
        return None, 0
    if reviewer_mode_is_active(getattr(args, "reviewer_mode", None)):
        return None, 0
    stop_args = SimpleNamespace(
        daemon_kind="all",
        stop_grace_seconds=float(getattr(args, "stop_grace_seconds", 5.0) or 5.0),
    )
    return _run_stop_action(
        args=stop_args,
        repo_root=repo_root,
        paths=runtime_paths,
    )
