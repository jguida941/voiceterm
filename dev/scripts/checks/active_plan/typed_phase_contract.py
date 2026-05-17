"""Validation helpers for the typed umbrella-plan phase/task contract."""

from __future__ import annotations

from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, import_repo_module
except ModuleNotFoundError:  # pragma: no cover - package execution fallback
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, import_repo_module

_plan_content = import_repo_module(
    "dev.scripts.devctl.platform.planning_ir_plan_content",
    repo_root=REPO_ROOT,
)
parse_execution_plan_phases = _plan_content.parse_execution_plan_phases


def validate_typed_phase_plan_contract(
    *,
    repo_root: Path,
    required_plan_paths: tuple[str, ...],
) -> list[str]:
    """Validate typed phase/task metadata on the consolidated umbrella plan."""
    issues: list[str] = []
    seen_task_ids: set[str] = set()

    for relative in required_plan_paths:
        plan_path = repo_root / relative
        if not plan_path.is_file():
            issues.append(f"{relative} is missing")
            continue
        phases = parse_execution_plan_phases(plan_path.read_text(encoding="utf-8"))
        if not phases:
            issues.append(f"{relative} missing typed phase registry")
            continue

        phase_ids = {phase.phase_id for phase in phases if phase.phase_id}
        task_ids = {
            task.task_id
            for phase in phases
            for task in phase.tasks
            if task.task_id
        }
        for phase in phases:
            if not phase.phase_id:
                issues.append(f"{relative} phase `{phase.title}` missing phase_id")
            if not phase.owner_doc:
                issues.append(
                    f"{relative} phase `{phase.phase_id or phase.title}` missing owner_doc"
                )
            if not phase.status:
                issues.append(
                    f"{relative} phase `{phase.phase_id or phase.title}` missing status"
                )
            if not phase.tasks:
                issues.append(
                    f"{relative} phase `{phase.phase_id or phase.title}` has no typed tasks"
                )
            for dependency in phase.dependencies:
                if not _dependency_exists(
                    dependency.dependency_id,
                    phase_ids=phase_ids,
                    task_ids=task_ids,
                ):
                    issues.append(
                        f"{relative} phase `{phase.phase_id or phase.title}` depends on unknown id `{dependency.dependency_id}`"
                    )
            for task in phase.tasks:
                if not task.task_id:
                    issues.append(
                        f"{relative} task under `{phase.phase_id or phase.title}` missing task_id"
                    )
                    continue
                if task.task_id in seen_task_ids:
                    issues.append(f"{relative} duplicate task_id `{task.task_id}`")
                seen_task_ids.add(task.task_id)
                if not task.owner_doc:
                    issues.append(f"{relative} task `{task.task_id}` missing owner_doc")
                if not task.status:
                    issues.append(f"{relative} task `{task.task_id}` missing status")
                for dependency in task.dependencies:
                    if not _dependency_exists(
                        dependency.dependency_id,
                        phase_ids=phase_ids,
                        task_ids=task_ids,
                    ):
                        issues.append(
                            f"{relative} task `{task.task_id}` depends on unknown id `{dependency.dependency_id}`"
                        )

    return issues


def _dependency_exists(
    dependency_id: str,
    *,
    phase_ids: set[str],
    task_ids: set[str],
) -> bool:
    return dependency_id in task_ids or dependency_id in phase_ids


__all__ = ["validate_typed_phase_plan_contract"]
