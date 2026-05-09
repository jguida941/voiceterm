"""Staged import/index atomicity preflight for governed commit."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.checks.startup_authority_contract.runtime_import_staged import (
    collect_staged_import_index_atomicity_findings,
)
from dev.scripts.checks.startup_authority_contract.runtime_import_git import (
    list_staged_new_python_module_paths,
)

from .commit_visibility import commit_visibility_payload
from .governed_executor_actions import _build_report


def preflight_import_index_atomicity(
    *,
    repo_root: Path,
    pipeline,
    stage_warnings: list[str],
) -> tuple[list[str], dict[str, object] | None]:
    """Block governed commit before the guard bundle when staged imports drift."""
    warnings = list(stage_warnings)
    staged_new_module_paths, staged_paths_warning = (
        list_staged_new_python_module_paths(repo_root)
    )
    if staged_paths_warning:
        warnings.append(staged_paths_warning)
    if not staged_new_module_paths:
        return warnings, None

    errors, atomicity_warnings = collect_staged_import_index_atomicity_findings(
        repo_root
    )
    warnings.extend(atomicity_warnings)
    if not errors:
        return warnings, None

    guidance = (
        "Fix the staged import/index atomicity violations before rerunning "
        "`devctl commit`."
    )
    first_violation = str(errors[0]).strip()
    if first_violation:
        guidance = f"{guidance} First violation: {first_violation}"
    return warnings, _build_report(
        status="blocked",
        reason="import_index_atomicity_violation",
        pipeline_id=getattr(pipeline, "pipeline_id", ""),
        pipeline_state=getattr(pipeline, "state", ""),
        approval_state=getattr(pipeline, "approval_state", ""),
        **commit_visibility_payload(pipeline),
        staged_new_python_module_paths=list(staged_new_module_paths),
        import_index_atomicity_findings=list(errors),
        operator_guidance=guidance,
        warnings=warnings,
    )
