"""Stage precondition helpers for the governed VCS pipeline."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ...runtime import ActionResult, TypedAction
from ...runtime.action_contracts import ActionOutcome
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.startup_receipt import load_startup_receipt
from .governed_executor_actions import _ACTIVE_PIPELINE_STATES
from .governed_executor_field_access import (
    bool_field,
    field,
    string_field,
)
from .governed_executor_git import pipeline_is_stale_for_current_repo

ResultBuilder = Callable[..., ActionResult]


def check_stage_preconditions(
    action: TypedAction,
    *,
    repo_root: Path,
    startup_context: Any,
    load_pipeline: Callable[[], RemoteCommitPipelineContract],
    pipeline_artifact_relpath: str,
    result_builder: ResultBuilder,
) -> ActionResult | None:
    """Return an early-exit ActionResult if stage preconditions fail, else None."""
    reviewer_gate = field(startup_context, "reviewer_gate")
    checkpoint_stage_allowed = (
        string_field(field(startup_context, "push_decision"), "action")
        == "await_checkpoint"
        and bool_field(reviewer_gate, "checkpoint_permitted", default=True)
    )
    if (
        bool_field(reviewer_gate, "implementation_blocked")
        and not checkpoint_stage_allowed
    ):
        return result_builder(
            action_id=action.action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason=string_field(reviewer_gate, "implementation_block_reason")
            or "reviewer_gate_blocked",
            operator_guidance=(
                "Repair the review/startup state before staging a remote "
                "commit pipeline."
            ),
        )
    attention_block = attention_revision_block(
        action=action,
        repo_root=repo_root,
        startup_context=startup_context,
        result_builder=result_builder,
    )
    if attention_block is not None:
        return attention_block
    current = load_pipeline()
    if (
        current.pipeline_id
        and current.state in _ACTIVE_PIPELINE_STATES
        and not pipeline_is_stale_for_current_repo(current, repo_root=repo_root)
    ):
        return result_builder(
            action_id=action.action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason="active_pipeline_exists",
            operator_guidance=(
                "Recover or complete the current remote commit pipeline "
                "before staging another one."
            ),
            warnings=(f"active_pipeline_id={current.pipeline_id}",),
            artifact_paths=(pipeline_artifact_relpath,),
        )
    return None


def attention_revision_block(
    *,
    action: TypedAction,
    repo_root: Path,
    startup_context: Any,
    result_builder: ResultBuilder,
) -> ActionResult | None:
    packet_inbox = field(startup_context, "packet_inbox")
    current_attention_revision = string_field(packet_inbox, "attention_revision")
    if not current_attention_revision:
        return None
    agents = field(packet_inbox, "agents")
    if not isinstance(agents, (tuple, list)):
        return None
    target_agent = _startup_context_active_implementation_owner(startup_context)
    if not _target_agent_has_actionable_packet_attention(
        agents=agents,
        target_agent=target_agent,
    ):
        return None
    receipt = load_startup_receipt(repo_root=repo_root)
    if receipt is not None and receipt.attention_revision == current_attention_revision:
        return None
    return result_builder(
        action_id=action.action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason="attention_revision_stale",
        operator_guidance=(
            "Typed packet attention changed since the last startup receipt. "
            "Rerun `python3 dev/scripts/devctl.py startup-context --format summary`, "
            "refresh `session-resume`, then acknowledge the new typed inbox state "
            "before staging more work."
        ),
    )


def _has_actionable_packet_attention(row: object) -> bool:
    pending_actionable_total = 0
    if isinstance(row, dict):
        pending_actionable_total = int(row.get("pending_actionable_total") or 0)
        wake_reason = str(row.get("wake_reason") or "").strip()
    else:
        pending_actionable_total = int(getattr(row, "pending_actionable_total", 0) or 0)
        wake_reason = str(getattr(row, "wake_reason", "") or "").strip()
    if pending_actionable_total > 0:
        return True
    return wake_reason == "finding_pending"


def _target_agent_has_actionable_packet_attention(
    *,
    agents: tuple[object, ...] | list[object],
    target_agent: str,
) -> bool:
    if target_agent:
        normalized_target = target_agent.strip().lower()
        for row in agents:
            if string_field(row, "agent").lower() != normalized_target:
                continue
            return _has_actionable_packet_attention(row)
        return False
    return any(_has_actionable_packet_attention(row) for row in agents)


def _startup_context_active_implementation_owner(startup_context: object) -> str:
    work_intake = field(startup_context, "work_intake")
    coordination = field(work_intake, "coordination")
    return string_field(coordination, "active_implementation_owner").lower()
