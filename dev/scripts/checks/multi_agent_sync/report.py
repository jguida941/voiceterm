"""Report assembly for the multi-agent sync guard."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

if __package__:
    from .instruction_validation import (
        _validate_instruction_rows,
        _validate_signoff_rows,
    )
    from .collision_validation import _validate_mp_collisions
    from .lane_lock_validation import _validate_lane_locks
    from .lane_validation import (
        _cycle_complete_for_signoff,
        _extend_runtime_truth_errors,
        _validate_agent_names,
        _validate_agent_presence,
        _validate_lane_alignment,
        _warn_unknown_ledger_statuses,
    )
    from .master_lane_validation import _validate_master_lane_rows
    from .markdown_tables import (
        _extract_table_rows,
        _rows_by_key,
        _sorted_agents,
        _sorted_signers,
    )
    from .models import (
        AgentBundle,
        MASTER_BOARD_HEADING,
        RUNBOOK_BOARD_HEADING,
        RUNBOOK_INSTRUCTION_HEADING,
        RUNBOOK_LEDGER_HEADING,
        RUNBOOK_SIGNOFF_HEADING,
        TableBundle,
    )
    from .runtime_truth import evaluate_runtime_truth
else:  # pragma: no cover - standalone package fallback
    from instruction_validation import _validate_instruction_rows, _validate_signoff_rows
    from collision_validation import _validate_mp_collisions
    from lane_lock_validation import _validate_lane_locks
    from lane_validation import (
        _cycle_complete_for_signoff,
        _extend_runtime_truth_errors,
        _validate_agent_names,
        _validate_agent_presence,
        _validate_lane_alignment,
        _warn_unknown_ledger_statuses,
    )
    from master_lane_validation import _validate_master_lane_rows
    from markdown_tables import (
        _extract_table_rows,
        _rows_by_key,
        _sorted_agents,
        _sorted_signers,
    )
    from models import (
        AgentBundle,
        MASTER_BOARD_HEADING,
        RUNBOOK_BOARD_HEADING,
        RUNBOOK_INSTRUCTION_HEADING,
        RUNBOOK_LEDGER_HEADING,
        RUNBOOK_SIGNOFF_HEADING,
        TableBundle,
    )
    from runtime_truth import evaluate_runtime_truth


def build_report(
    *,
    repo_root: Path,
    master_plan_path: Path,
    runbook_path: Path,
    extract_table_rows_fn: Callable[[str, str], tuple[list[dict], str | None]] | None = None,
    evaluate_runtime_truth_fn: Callable[..., dict[str, object]] | None = None,
) -> dict:
    """Build the multi-agent parity report for one repo."""
    table_loader = extract_table_rows_fn or _extract_table_rows
    runtime_truth_loader = evaluate_runtime_truth_fn or evaluate_runtime_truth
    missing = _missing_path_report(
        repo_root=repo_root,
        master_plan_path=master_plan_path,
        runbook_path=runbook_path,
    )
    if missing is not None:
        return missing

    tables = _load_tables(
        master_plan_path=master_plan_path,
        runbook_path=runbook_path,
        extract_table_rows_fn=table_loader,
    )
    errors = list(tables.errors)
    warnings: list[str] = []
    agents = _build_agent_bundle(
        master_rows=tables.master_rows,
        runbook_rows=tables.runbook_rows,
        signoff_rows=tables.signoff_rows,
    )
    _validate_agent_presence(agents=agents, errors=errors)
    _validate_agent_names(agents=agents, errors=errors)
    _validate_lane_alignment(agents=agents, errors=errors)
    _validate_master_lane_rows(
        agents=agents,
        ledger_rows=tables.ledger_rows,
        errors=errors,
    )
    _validate_lane_locks(agents=agents, errors=errors)
    _validate_mp_collisions(agents=agents, errors=errors)
    _validate_instruction_rows(
        instruction_rows=tables.instruction_rows,
        required_agents=agents.required_agents,
        errors=errors,
        warnings=warnings,
    )
    _warn_unknown_ledger_statuses(tables.ledger_rows, warnings)
    runtime_truth = runtime_truth_loader(
        repo_root=repo_root,
        planned_agent_ids=_sorted_agents(agents.required_agents | agents.runbook_agents),
    )
    _extend_runtime_truth_errors(runtime_truth=runtime_truth, errors=errors)
    warnings.extend(_string_items(runtime_truth.get("warnings")))
    cycle_complete_for_signoff = _cycle_complete_for_signoff(
        master_by_agent=agents.master_by_agent,
        required_agents=agents.required_agents,
    )
    if cycle_complete_for_signoff:
        _validate_signoff_rows(agents=agents, errors=errors)
    return {
        "command": "check_multi_agent_sync",
        "ok": not errors,
        "master_plan_path": str(master_plan_path.relative_to(repo_root)),
        "coordination_path": str(runbook_path.relative_to(repo_root)),
        "required_agents": _sorted_agents(agents.required_agents),
        "master_agents": _sorted_agents(agents.master_agents),
        "coordination_agents": _sorted_agents(agents.runbook_agents),
        "runtime_truth_checked": bool(runtime_truth.get("checked")),
        "runtime_review_state_path": runtime_truth.get("review_state_path", ""),
        "runtime_coordination_topology": runtime_truth.get(
            "coordination_topology",
            "",
        ),
        "runtime_legacy_reviewer_mode": runtime_truth.get(
            "legacy_reviewer_mode",
            "",
        ),
        "runtime_active_runtime_providers": runtime_truth.get(
            "active_runtime_providers",
            [],
        ),
        "runtime_agent_work_board_rows": runtime_truth.get(
            "agent_work_board_row_count",
            0,
        ),
        "runtime_agent_loop_decisions": runtime_truth.get(
            "agent_loop_decision_row_count",
            0,
        ),
        "runtime_pending_packet_agents": runtime_truth.get(
            "pending_packet_agents",
            [],
        ),
        "instruction_entries": len(tables.instruction_rows),
        "ledger_entries": len(tables.ledger_rows),
        "signoff_signers": _sorted_signers(agents.signoff_signers),
        "cycle_complete_for_signoff": cycle_complete_for_signoff,
        "errors": errors,
        "warnings": warnings,
    }


def render_md(report: dict) -> str:
    lines = ["# check_multi_agent_sync", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    if "error" in report:
        lines.append(f"- error: {report['error']}")
        return "\n".join(lines)
    lines.append(f"- master_plan: {report['master_plan_path']}")
    lines.append(f"- coordination_doc: {report['coordination_path']}")
    lines.append("- required_agents: " + ", ".join(report.get("required_agents", [])))
    lines.append(
        "- master_agents: " + (", ".join(report.get("master_agents", [])) or "none")
    )
    lines.append(
        "- coordination_agents: "
        + (", ".join(report.get("coordination_agents", [])) or "none")
    )
    lines.append(
        f"- runtime_truth_checked: {report.get('runtime_truth_checked', False)}"
    )
    if report.get("runtime_review_state_path"):
        lines.append(
            f"- runtime_review_state: {report.get('runtime_review_state_path')}"
        )
    lines.append(
        "- runtime_coordination_topology: "
        + (str(report.get("runtime_coordination_topology") or "unavailable"))
    )
    lines.append(
        "- runtime_legacy_reviewer_mode: "
        + (str(report.get("runtime_legacy_reviewer_mode") or "unavailable"))
    )
    work_board_rows = report.get("runtime_agent_work_board_rows", 0)
    lines.append(f"- runtime_agent_work_board_rows: {work_board_rows}")
    decision_rows = report.get("runtime_agent_loop_decisions", 0)
    lines.append(f"- runtime_agent_loop_decisions: {decision_rows}")
    lines.append(
        "- runtime_active_runtime_providers: "
        + (
            ", ".join(report.get("runtime_active_runtime_providers", []))
            or "none"
        )
    )
    lines.append(
        "- runtime_pending_packet_agents: "
        + (", ".join(report.get("runtime_pending_packet_agents", [])) or "none")
    )
    lines.append(f"- instruction_entries: {report.get('instruction_entries', 0)}")
    lines.append(f"- ledger_entries: {report.get('ledger_entries', 0)}")
    lines.append(
        "- signoff_signers: "
        + (", ".join(report.get("signoff_signers", [])) or "none")
    )
    lines.append(
        f"- cycle_complete_for_signoff: {report.get('cycle_complete_for_signoff', False)}"
    )
    lines.append(
        "- warnings: "
        + (", ".join(report.get("warnings", [])) if report.get("warnings") else "none")
    )
    lines.append(
        "- errors: "
        + (", ".join(report.get("errors", [])) if report.get("errors") else "none")
    )
    return "\n".join(lines)


def _missing_path_report(
    *,
    repo_root: Path,
    master_plan_path: Path,
    runbook_path: Path,
) -> dict[str, object] | None:
    for path in (master_plan_path, runbook_path):
        if path.exists():
            continue
        return {
            "command": "check_multi_agent_sync",
            "ok": False,
            "error": f"Missing file: {path.relative_to(repo_root)}",
        }
    return None


def _load_tables(
    *,
    master_plan_path: Path,
    runbook_path: Path,
    extract_table_rows_fn: Callable[[str, str], tuple[list[dict], str | None]],
) -> TableBundle:
    master_text = master_plan_path.read_text(encoding="utf-8")
    runbook_text = runbook_path.read_text(encoding="utf-8")
    extracted = [
        extract_table_rows_fn(master_text, MASTER_BOARD_HEADING),
        extract_table_rows_fn(runbook_text, RUNBOOK_BOARD_HEADING),
        extract_table_rows_fn(runbook_text, RUNBOOK_INSTRUCTION_HEADING),
        extract_table_rows_fn(runbook_text, RUNBOOK_LEDGER_HEADING),
        extract_table_rows_fn(runbook_text, RUNBOOK_SIGNOFF_HEADING),
    ]
    errors = tuple(error for _, error in extracted if error)
    return TableBundle(
        master_rows=extracted[0][0],
        runbook_rows=extracted[1][0],
        instruction_rows=extracted[2][0],
        ledger_rows=extracted[3][0],
        signoff_rows=extracted[4][0],
        errors=errors,
    )


def _build_agent_bundle(
    *,
    master_rows: list[dict],
    runbook_rows: list[dict],
    signoff_rows: list[dict],
) -> AgentBundle:
    master_by_agent = _rows_by_key(master_rows, "Agent")
    runbook_by_agent = _rows_by_key(runbook_rows, "Agent")
    signoff_by_signer = _rows_by_key(signoff_rows, "Signer")
    master_agents = set(master_by_agent)
    runbook_agents = set(runbook_by_agent)
    required_agents = set(master_agents)
    signoff_signers = set(signoff_by_signer)
    return AgentBundle(
        master_by_agent=master_by_agent,
        runbook_by_agent=runbook_by_agent,
        master_agents=master_agents,
        runbook_agents=runbook_agents,
        required_agents=required_agents,
        signoff_by_signer=signoff_by_signer,
        signoff_signers=signoff_signers,
        expected_signers=required_agents | {"ORCHESTRATOR"},
    )


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
