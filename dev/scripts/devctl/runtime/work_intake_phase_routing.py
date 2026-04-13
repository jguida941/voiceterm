"""Phase-aware routing derived from typed plan-content metadata."""

from __future__ import annotations

from pathlib import Path

from ..platform.planning_ir_models import PlanPhase
from ..platform.planning_ir_plan_content import (
    first_actionable_task,
    parse_execution_plan_phases,
)
from .work_intake_models import PlanTargetRef
from .work_intake_plan_routing import PlanRoutingState


def build_plan_routing_state(
    *,
    repo_root: Path,
    active_target: PlanTargetRef | None,
) -> PlanRoutingState:
    """Project the current phase/task route from the active target plan."""
    if active_target is None or not active_target.plan_path:
        return PlanRoutingState()
    plan_path = repo_root / active_target.plan_path
    try:
        plan_text = plan_path.read_text(encoding="utf-8")
    except OSError:
        return PlanRoutingState()
    phases = parse_execution_plan_phases(plan_text)
    if not phases:
        return PlanRoutingState()
    phase = _select_phase(phases)
    task = first_actionable_task((phase,)) if phase is not None else None
    if phase is None:
        return PlanRoutingState()
    dependencies = tuple(
        dependency.dependency_id for dependency in (task.dependencies if task else ())
    )
    return PlanRoutingState(
        phase_id=phase.phase_id,
        phase_title=phase.title,
        phase_status=phase.status,
        phase_owner_doc=phase.owner_doc,
        task_id=task.task_id if task is not None else "",
        task_summary=task.summary if task is not None else "",
        task_status=task.status if task is not None else "",
        task_owner_doc=task.owner_doc if task is not None else "",
        dependencies=dependencies,
    )


def _select_phase(phases: tuple[PlanPhase, ...]) -> PlanPhase | None:
    for desired_status in ("in_progress", "pending", "blocked", "done"):
        for phase in phases:
            if phase.status == desired_status:
                return phase
    return phases[0] if phases else None


__all__ = ["build_plan_routing_state"]
