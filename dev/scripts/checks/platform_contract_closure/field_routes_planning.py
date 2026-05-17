"""Planning and backlog field-route closure proofs for platform enforcement."""

from __future__ import annotations

from .field_routes_surface_state import (
    _build_coverage,
    _build_violation,
    _source_contains_any,
)


def _module_references(module_path: str, *token_groups: tuple[str, ...]) -> bool:
    """Return True when every token group has an executable reference."""
    return all(_source_contains_any(module_path, tokens) for tokens in token_groups)


def check_plan_phase_phase_id_startup_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify PlanPhase.phase_id reaches the startup plan-routing surfaces."""
    builder = "dev.scripts.devctl.runtime.work_intake_phase_routing"
    renderer = "dev.scripts.devctl.runtime.work_intake_plan_routing"
    summary = "dev.scripts.devctl.commands.governance.startup_context_summary"
    coverage = _build_coverage(
        "PlanPhase",
        "phase_id",
        "startup_plan_routing",
        builder,
    )
    if (
        _module_references(builder, ("phase.phase_id", "phase_id"))
        and _module_references(renderer, ("phase_id",))
        and _module_references(summary, ("phase_id",))
    ):
        coverage["detail"] = (
            "PlanPhase.phase_id is read by the plan-routing builder and "
            "rendered through the startup plan-routing projections."
        )
        return coverage, None

    detail = (
        "PlanPhase.phase_id does not reach the startup plan-routing builder "
        "plus summary/render surfaces."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_plan_task_task_id_startup_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify PlanTask.task_id reaches the startup plan-routing surfaces."""
    builder = "dev.scripts.devctl.runtime.work_intake_phase_routing"
    renderer = "dev.scripts.devctl.runtime.work_intake_plan_routing"
    summary = "dev.scripts.devctl.commands.governance.startup_context_summary"
    coverage = _build_coverage(
        "PlanTask",
        "task_id",
        "startup_plan_routing",
        builder,
    )
    if (
        _module_references(builder, ("task.task_id", "task_id"))
        and _module_references(renderer, ("task_id",))
        and _module_references(summary, ("task_id",))
    ):
        coverage["detail"] = (
            "PlanTask.task_id is read by the plan-routing builder and "
            "rendered through the startup plan-routing projections."
        )
        return coverage, None

    detail = (
        "PlanTask.task_id does not reach the startup plan-routing builder "
        "plus summary/render surfaces."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_finding_backlog_latest_rows_findings_priority_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify FindingBacklog.latest_rows reaches findings-priority."""
    consumer = "dev.scripts.devctl.commands.reporting.findings_priority"
    coverage = _build_coverage(
        "FindingBacklog",
        "latest_rows",
        "findings_priority",
        consumer,
    )
    if _module_references(
        consumer,
        ("load_finding_backlog_from_log",),
        ("backlog.latest_rows", "latest_rows"),
        ("accumulated_findings_from_governance_rows",),
    ):
        coverage["detail"] = (
            "FindingBacklog.latest_rows is consumed by findings-priority "
            "before the governed rows are ranked."
        )
        return coverage, None

    detail = (
        "FindingBacklog.latest_rows does not reach the governed "
        "findings-priority consumer."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_finding_backlog_open_findings_planning_ir_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify FindingBacklog.open_findings reaches the planning reducer."""
    consumer = "dev.scripts.devctl.platform.planning_ir_sources"
    coverage = _build_coverage(
        "FindingBacklog",
        "open_findings",
        "planning_ir",
        consumer,
    )
    if _module_references(
        consumer,
        ("backlog.open_findings", "open_findings"),
        ("live_findings",),
    ):
        coverage["detail"] = (
            "FindingBacklog.open_findings is consumed by planning IR as the "
            "canonical live-finding input."
        )
        return coverage, None

    detail = (
        "FindingBacklog.open_findings does not reach the planning reducer's "
        "live-finding projection."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_finding_backlog_open_rows_startup_quality_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify FindingBacklog.open_rows reaches startup quality signals."""
    consumer = "dev.scripts.devctl.runtime.startup_signals"
    coverage = _build_coverage(
        "FindingBacklog",
        "open_rows",
        "startup_quality_signals",
        consumer,
    )
    if _module_references(
        consumer,
        ("load_finding_backlog",),
        ("backlog.open_rows", "open_rows"),
        ("open_finding_count",),
    ):
        coverage["detail"] = (
            "FindingBacklog.open_rows is consumed by startup quality signals "
            "when projecting governed open-finding counts."
        )
        return coverage, None

    detail = (
        "FindingBacklog.open_rows does not reach the startup quality-signals "
        "projection."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)
