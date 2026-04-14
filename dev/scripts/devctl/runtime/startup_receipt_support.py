"""Support helpers for startup receipt persistence and projection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..config import get_repo_root
from ..time_utils import utc_timestamp
from .authority_snapshot import (
    AuthoritySnapshot,
    authority_snapshot_from_mapping,
    build_authority_snapshot,
)
from .startup_receipt_freshness import _git_stdout as _freshness_git_stdout
from .startup_receipt_freshness import IMPLEMENTATION_STRICT_STARTUP_INTENT
from .startup_receipt_core import (
    StartupReceipt,
    startup_receipt_path,
)

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .startup_context import StartupContext


def build_startup_receipt(
    ctx: "StartupContext",
    *,
    authority_report: dict[str, Any],
    intent_scope: str = IMPLEMENTATION_STRICT_STARTUP_INTENT,
    authority_snapshot: AuthoritySnapshot | None = None,
    repo_root: Path | None = None,
) -> "StartupReceipt":
    """Build the persistent receipt written by startup-context."""
    resolved_root = repo_root or get_repo_root()
    governance = ctx.governance
    repo_identity = governance.repo_identity if governance is not None else None
    push = governance.push_enforcement if governance is not None else None
    authority_errors = tuple(
        str(row).strip()
        for row in authority_report.get("errors", ())
        if str(row).strip()
    )
    authority_warnings = tuple(
        str(row).strip()
        for row in authority_report.get("warnings", ())
        if str(row).strip()
    )
    current_head = _freshness_git_stdout(resolved_root, "rev-parse", "HEAD")
    reviewer_loop_blocked = bool(
        ctx.reviewer_gate.implementation_blocked
        and not ctx.reviewer_gate.review_gate_allows_push
    )
    resolved_authority_snapshot = authority_snapshot or ctx.authority_snapshot
    if resolved_authority_snapshot is None:
        resolved_authority_snapshot = build_authority_snapshot(ctx.to_dict())
    return StartupReceipt(
        generated_at_utc=utc_timestamp(),
        repo_name=repo_identity.repo_name if repo_identity is not None else "",
        current_branch=repo_identity.current_branch if repo_identity is not None else "",
        head_commit_sha=current_head,
        receipt_intent_scope=str(intent_scope or "").strip()
        or IMPLEMENTATION_STRICT_STARTUP_INTENT,
        reviewer_loop_blocked=reviewer_loop_blocked,
        implementation_block_reason=str(
            ctx.reviewer_gate.implementation_block_reason or ""
        ).strip(),
        review_gate_allows_push=bool(ctx.reviewer_gate.review_gate_allows_push),
        receipt_source_tree_head_sha=current_head,
        receipt_admin_drift_allowed=(
            reviewer_loop_blocked
            and not (bool(push.checkpoint_required) if push is not None else False)
            and (bool(push.safe_to_continue_editing) if push is not None else True)
        ),
        advisory_action=str(ctx.advisory_action or "").strip(),
        advisory_reason=str(ctx.advisory_reason or "").strip(),
        recommended_action=(
            str(push.recommended_action or "").strip() if push is not None else ""
        ),
        push_action=str(ctx.push_decision.action or "").strip(),
        push_reason=str(ctx.push_decision.reason or "").strip(),
        push_eligible_now=bool(ctx.push_decision.push_eligible_now),
        push_next_step_summary=str(ctx.push_decision.next_step_summary or "").strip(),
        push_next_step_command=str(ctx.push_decision.next_step_command or "").strip(),
        publication_backlog_state=(
            str(ctx.push_decision.publication_backlog.backlog_state or "").strip()
            or "none"
        ),
        publication_backlog_summary=str(
            ctx.push_decision.publication_backlog.backlog_summary or ""
        ).strip(),
        publication_backlog_recommended=bool(
            ctx.push_decision.publication_backlog.backlog_recommended
        ),
        publication_backlog_urgent=bool(
            ctx.push_decision.publication_backlog.backlog_urgent
        ),
        publication_guidance=str(ctx.push_decision.publication_guidance or "").strip(),
        attention_revision=str(
            getattr(ctx.packet_inbox, "attention_revision", "") or ""
        ).strip(),
        staged_path_count=int(getattr(push, "staged_path_count", 0) or 0),
        unstaged_path_count=int(getattr(push, "unstaged_path_count", 0) or 0),
        checkpoint_required=bool(push.checkpoint_required) if push is not None else False,
        safe_to_continue_editing=(
            bool(push.safe_to_continue_editing) if push is not None else True
        ),
        startup_authority_ok=bool(authority_report.get("ok", False)),
        startup_authority_errors=authority_errors,
        startup_authority_warnings=authority_warnings,
        authority_snapshot=resolved_authority_snapshot,
    )


def write_startup_receipt(
    receipt: "StartupReceipt",
    *,
    governance: "ProjectGovernance | None" = None,
    repo_root: Path | None = None,
) -> Path:
    """Persist one startup receipt to the managed startup artifact path."""
    path = startup_receipt_path(
        governance=governance,
        repo_root=repo_root,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt.to_dict(), indent=2), encoding="utf-8")
    return path


def load_startup_receipt(
    *,
    governance: "ProjectGovernance | None" = None,
    repo_root: Path | None = None,
) -> "StartupReceipt | None":
    """Load the latest startup receipt when it exists."""
    path = startup_receipt_path(governance=governance, repo_root=repo_root)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    return startup_receipt_from_mapping(payload)


def startup_receipt_from_mapping(payload: dict[str, object]) -> "StartupReceipt":
    """Restore a startup receipt from a JSON-like mapping."""
    return StartupReceipt(
        schema_version=int(payload.get("schema_version") or 1),
        contract_id=str(payload.get("contract_id") or "StartupReceipt").strip(),
        generated_at_utc=str(payload.get("generated_at_utc") or "").strip(),
        repo_name=str(payload.get("repo_name") or "").strip(),
        current_branch=str(payload.get("current_branch") or "").strip(),
        head_commit_sha=str(payload.get("head_commit_sha") or "").strip(),
        receipt_intent_scope=(
            str(payload.get("receipt_intent_scope") or "").strip()
            or IMPLEMENTATION_STRICT_STARTUP_INTENT
        ),
        reviewer_loop_blocked=bool(payload.get("reviewer_loop_blocked", False)),
        implementation_block_reason=str(
            payload.get("implementation_block_reason") or ""
        ).strip(),
        review_gate_allows_push=bool(payload.get("review_gate_allows_push", False)),
        receipt_source_tree_head_sha=str(
            payload.get("receipt_source_tree_head_sha") or ""
        ).strip(),
        receipt_admin_drift_allowed=bool(
            payload.get("receipt_admin_drift_allowed", False)
        ),
        advisory_action=str(payload.get("advisory_action") or "").strip(),
        advisory_reason=str(payload.get("advisory_reason") or "").strip(),
        recommended_action=str(payload.get("recommended_action") or "").strip(),
        push_action=str(payload.get("push_action") or "").strip(),
        push_reason=str(payload.get("push_reason") or "").strip(),
        push_eligible_now=bool(payload.get("push_eligible_now", False)),
        push_next_step_summary=str(payload.get("push_next_step_summary") or "").strip(),
        push_next_step_command=str(payload.get("push_next_step_command") or "").strip(),
        publication_backlog_state=(
            str(payload.get("publication_backlog_state") or "").strip() or "none"
        ),
        publication_backlog_summary=str(
            payload.get("publication_backlog_summary") or ""
        ).strip(),
        publication_backlog_recommended=bool(
            payload.get("publication_backlog_recommended", False)
        ),
        publication_backlog_urgent=bool(
            payload.get("publication_backlog_urgent", False)
        ),
        publication_guidance=str(payload.get("publication_guidance") or "").strip(),
        attention_revision=str(payload.get("attention_revision") or "").strip(),
        staged_path_count=int(payload.get("staged_path_count") or 0),
        unstaged_path_count=int(payload.get("unstaged_path_count") or 0),
        checkpoint_required=bool(payload.get("checkpoint_required", False)),
        safe_to_continue_editing=bool(payload.get("safe_to_continue_editing", True)),
        startup_authority_ok=bool(payload.get("startup_authority_ok", False)),
        startup_authority_errors=tuple(
            str(row).strip()
            for row in payload.get("startup_authority_errors", ())
            if str(row).strip()
        ),
        startup_authority_warnings=tuple(
            str(row).strip()
            for row in payload.get("startup_authority_warnings", ())
            if str(row).strip()
        ),
        authority_snapshot=authority_snapshot_from_mapping(payload.get("authority_snapshot")),
    )
