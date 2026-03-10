"""Shared workflow-surface state for Operator Console layout chrome."""

from __future__ import annotations

from dataclasses import dataclass

from ..state.activity.activity_reports import recommended_next_step
from ..state.core.models import AgentLaneData, OperatorConsoleSnapshot
from ..state.repo.repo_state import RepoStateSnapshot
from .workflow_presets import resolve_workflow_preset


@dataclass(frozen=True)
class WorkflowStageState:
    """One workflow transition stage for footer rendering."""

    stage_id: str
    label: str
    status_level: str
    detail: str


@dataclass(frozen=True)
class WorkflowSurfaceState:
    """Display-ready top-strip and footer state for the shared workflow layout."""

    current_slice: str
    shared_goal: str
    current_writer: str
    branch: str
    swarm_health: str
    codex_last_seen: str
    codex_last_applied: str
    claude_last_seen: str
    claude_last_applied: str
    stages: tuple[WorkflowStageState, ...]
    next_action: str


def build_workflow_surface_state(
    snapshot: OperatorConsoleSnapshot,
    *,
    repo_state: RepoStateSnapshot,
    workflow_preset_id: str,
    swarm_health_label: str,
) -> WorkflowSurfaceState:
    """Build one state payload for workflow top-strip + bottom timeline."""
    preset = resolve_workflow_preset(workflow_preset_id)
    codex_last_seen = _codex_last_seen(snapshot)
    codex_last_applied = _codex_last_applied(snapshot)
    claude_last_seen = _lane_row(snapshot.claude_lane, "Updated")
    claude_last_applied = _lane_row(snapshot.claude_lane, "Ack")
    stages = _build_stages(snapshot)
    return WorkflowSurfaceState(
        current_slice=f"{preset.mp_scope} ({preset.label})",
        shared_goal=preset.summary,
        current_writer=_current_writer(snapshot),
        branch=repo_state.branch or "(unknown)",
        swarm_health=swarm_health_label or "Swarm Idle",
        codex_last_seen=codex_last_seen,
        codex_last_applied=codex_last_applied,
        claude_last_seen=claude_last_seen,
        claude_last_applied=claude_last_applied,
        stages=stages,
        next_action=recommended_next_step(snapshot),
    )


def _build_stages(snapshot: OperatorConsoleSnapshot) -> tuple[WorkflowStageState, ...]:
    instruction = _lane_row(snapshot.operator_lane, "Instruction")
    has_instruction = _is_present(instruction)
    has_review_poll = _is_present(snapshot.last_codex_poll)
    ack_text = _lane_row(snapshot.claude_lane, "Ack")
    has_ack = _is_present(ack_text)
    claude_state = _lane_state(snapshot.claude_lane)
    codex_state = _lane_state(snapshot.codex_lane)
    pending = len(snapshot.pending_approvals)
    verdict = _lane_row(snapshot.codex_lane, "Verdict")
    findings = _lane_row(snapshot.codex_lane, "Findings")

    stages = (
        WorkflowStageState(
            stage_id="posted",
            label="Posted",
            status_level="active" if has_instruction else "idle",
            detail=instruction,
        ),
        WorkflowStageState(
            stage_id="read",
            label="Read",
            status_level="active" if has_review_poll else "idle",
            detail=snapshot.last_codex_poll or "(missing)",
        ),
        WorkflowStageState(
            stage_id="acked",
            label="Acked",
            status_level="active" if has_ack else "idle",
            detail=ack_text,
        ),
        WorkflowStageState(
            stage_id="implementing",
            label="Implementing",
            status_level=_implementing_level(claude_state),
            detail=claude_state,
        ),
        WorkflowStageState(
            stage_id="tests",
            label="Tests",
            status_level="active" if _looks_testing(verdict, findings) else "idle",
            detail=verdict,
        ),
        WorkflowStageState(
            stage_id="reviewed",
            label="Reviewed",
            status_level="active" if codex_state in {"Reviewing", "Ready"} else "idle",
            detail=codex_state,
        ),
        WorkflowStageState(
            stage_id="apply",
            label="Apply",
            status_level="warning" if pending else "active",
            detail=f"pending approvals: {pending}",
        ),
    )
    return stages


def _current_writer(snapshot: OperatorConsoleSnapshot) -> str:
    if _lane_state(snapshot.claude_lane) == "Implementing":
        return "Claude"
    cursor_state = _lane_state(getattr(snapshot, "cursor_lane", None))
    if cursor_state in {"Editing", "Implementing", "Active"}:
        return "Cursor"
    if len(snapshot.pending_approvals) > 0:
        return "Operator"
    if _lane_state(snapshot.codex_lane) in {"Reviewing", "Ready"}:
        return "Codex"
    return "Operator"


def _codex_last_seen(snapshot: OperatorConsoleSnapshot) -> str:
    live_updated = _lane_row(snapshot.codex_lane, "Updated")
    if _is_present(live_updated):
        return live_updated
    return snapshot.last_codex_poll or "(missing)"


def _codex_last_applied(snapshot: OperatorConsoleSnapshot) -> str:
    worktree = _lane_row(snapshot.codex_lane, "Worktree")
    if _is_present(worktree):
        return worktree
    return snapshot.last_worktree_hash or "(missing)"


def _lane_state(lane: AgentLaneData | None) -> str:
    if lane is None:
        return "Idle"
    return lane.state_label or "Idle"


def _lane_row(lane: AgentLaneData | None, key: str) -> str:
    if lane is None:
        return "(missing)"
    for row_key, row_value in lane.rows:
        if row_key == key:
            return row_value
    return "(missing)"


def _is_present(value: str | None) -> bool:
    if value is None:
        return False
    cleaned = " ".join(str(value).split()).lower()
    return cleaned not in {"", "(missing)", "(empty)", "(unknown)", "(none)"}


def _implementing_level(claude_state: str) -> str:
    if claude_state == "Implementing":
        return "active"
    if claude_state in {"Waiting", "Blocked"}:
        return "warning"
    return "idle"


def _looks_testing(verdict: str, findings: str) -> bool:
    combined = f"{verdict}\n{findings}".lower()
    hints = (
        "test",
        "ci",
        "clippy",
        "cargo",
        "mutation",
        "green",
        "passed",
    )
    return any(hint in combined for hint in hints)
