"""Report builder for the read-only develop controller."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...governance.system_catalog import build_system_catalog
from ...runtime.development_team import build_default_development_topology
from ...runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL, PlanRow
from ...runtime.master_plan_store import read_plan_rows_jsonl
from .models import (
    DevelopmentControllerInputs,
    DevelopmentDiscoverySnapshot,
    DevelopmentLearningSnapshot,
    DevelopmentLoopReport,
    DevelopmentNextSlice,
    DevelopmentTopologySummary,
    DevelopmentWorkstreamSummary,
    scaling_summary_from_contract,
)


def build_report(args: Any) -> DevelopmentLoopReport:
    """Build the read-only controller report from existing typed surfaces."""
    action = _resolve_action(args)
    topology = build_default_development_topology()
    rows = read_plan_rows_jsonl(REPO_ROOT / DEFAULT_MASTER_PLAN_STORE_REL)
    blockers, warnings = _action_findings(action, args)

    return DevelopmentLoopReport(
        action=action,
        status="blocked" if blockers else "ready",
        ok=not blockers,
        controller_state=_controller_state(action),
        summary=_summary_for_action(action, blockers=blockers),
        topology=_topology_summary(topology),
        next_slice=_select_next_slice(rows),
        learning=_learning_snapshot(REPO_ROOT),
        discovery=_discovery_snapshot(),
        required_checks=_required_checks(action),
        next_commands=_next_commands(action),
        blockers=blockers,
        warnings=warnings,
        inputs=_controller_inputs(args, plan_rows=len(rows)),
    )


def _resolve_action(args: Any) -> str:
    return str(
        getattr(args, "action_flag", None)
        or getattr(args, "action", None)
        or "status"
    )


def _controller_state(action: str) -> str:
    if action == "launch":
        return "read_only_launch_preview"
    if action in {"pause", "resume"}:
        return f"read_only_{action}_preview"
    if action == "audit-guards":
        return "read_only_guard_audit"
    return "read_only"


def _controller_inputs(args: Any, *, plan_rows: int) -> DevelopmentControllerInputs:
    return DevelopmentControllerInputs(
        master_plan_store=DEFAULT_MASTER_PLAN_STORE_REL,
        plan_rows=plan_rows,
        fleet=str(getattr(args, "fleet", "default") or "default"),
        max_cycles=int(getattr(args, "max_cycles", 1) or 1),
        max_workers=int(getattr(args, "max_workers", 0) or 0),
        dry_run=bool(getattr(args, "dry_run", False)),
    )


def _topology_summary(topology) -> DevelopmentTopologySummary:
    return DevelopmentTopologySummary(
        contract_id=topology.contract_id,
        schema_version=topology.schema_version,
        topology_id=topology.topology_id,
        workstreams=tuple(
            DevelopmentWorkstreamSummary(
                workstream_id=item.workstream_id,
                display_name=item.display_name,
                mutation_policy=item.mutation_policy,
                runtime_role=item.runtime_role,
            )
            for item in topology.workstreams
        ),
        assignment_policy=topology.assignment_policy,
        provider_policy=topology.provider_policy,
        mutation_policy=topology.mutation_policy,
        default_worker_fanout=topology.default_worker_fanout,
        scaling=scaling_summary_from_contract(topology.scaling),
    )


def _select_next_slice(rows: tuple[PlanRow, ...]) -> DevelopmentNextSlice:
    selected = _first_row_with_status(rows, "in_progress")
    if selected is None:
        selected = _first_row_with_status(rows, "queued")
    if selected is None:
        return DevelopmentNextSlice(
            status="none",
            reason="No queued or in-progress typed plan rows found.",
        )
    return DevelopmentNextSlice(
        slice_id=selected.row_id,
        source=selected.source_doc_path or DEFAULT_MASTER_PLAN_STORE_REL,
        title=selected.title,
        target_ref=selected.target_ref,
        status=selected.status,
        reason="Selected from typed master-plan rows, preferring in-progress before queued.",
    )


def _first_row_with_status(rows: tuple[PlanRow, ...], status: str) -> PlanRow | None:
    for row in rows:
        if row.status == status:
            return row
    return None


def _discovery_snapshot() -> DevelopmentDiscoverySnapshot:
    catalog = build_system_catalog(repo_root=REPO_ROOT)
    return DevelopmentDiscoverySnapshot(
        commands=catalog.total_commands,
        guards=catalog.total_guards,
        probes=catalog.total_probes,
        surfaces=catalog.total_surfaces,
        coverage_targets=(
            "commands",
            "guards",
            "probes",
            "surfaces",
            "runtime-spine rows",
            "platform contracts",
        ),
    )


def _learning_snapshot(repo_root: Path) -> DevelopmentLearningSnapshot:
    finding_rows = _jsonl_rows(repo_root / "dev/reports/governance/finding_reviews.jsonl")
    promotion_rows = _jsonl_rows(
        repo_root / "dev/reports/governance/guard_promotion_candidates.jsonl"
    )
    queued_promotions = sum(
        1
        for row in promotion_rows
        if str(row.get("status") or row.get("candidate_status") or "queued") == "queued"
    )
    return DevelopmentLearningSnapshot(
        open_findings=len(finding_rows),
        promotion_candidates=len(promotion_rows),
        queued_promotion_candidates=queued_promotions,
        smartness_inputs=(
            "governance-quality-feedback",
            "probe-report",
            "GuardSmartnessReport",
            "red_team_fixture_result",
        ),
        learning_state="typed_inputs_available",
    )


def _jsonl_rows(path: Path) -> tuple[dict[str, Any], ...]:
    if not path.exists():
        return ()
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return tuple(rows)


def _action_findings(action: str, args: Any) -> tuple[tuple[str, ...], tuple[str, ...]]:
    blockers: list[str] = []
    warnings: list[str] = []
    fleet = str(getattr(args, "fleet", "default") or "default")
    max_cycles = int(getattr(args, "max_cycles", 1) or 1)
    max_workers = int(getattr(args, "max_workers", 0) or 0)

    if fleet != "default":
        blockers.append("Only the default DevelopmentModeTopology fleet is implemented.")
    if max_cycles < 1:
        blockers.append("--max-cycles must be at least 1.")
    if max_workers < 0:
        blockers.append("--max-workers cannot be negative.")
    if action == "launch":
        warnings.append(
            "launch is a read-only controller cycle preview; no worker process is spawned"
        )
        if max_cycles > 1:
            warnings.append(
                "multi-cycle launch is not active yet; this command renders one bounded report"
            )
    if action in {"pause", "resume"}:
        warnings.append(
            f"{action} is report-only until the typed controller-state writer lands"
        )
    return tuple(blockers), tuple(warnings)


def _summary_for_action(action: str, *, blockers: tuple[str, ...]) -> str:
    if blockers:
        return "Develop controller request failed closed before execution."
    if action == "next":
        return "Selected the next bounded typed development slice."
    if action == "audit-guards":
        return "Rendered guard/probe learning inputs for development mode."
    if action == "launch":
        return "Rendered one read-only develop controller cycle without mutation."
    if action in {"pause", "resume"}:
        return f"Rendered a read-only {action} request without mutating controller state."
    return "Rendered typed develop controller status."


def _required_checks(action: str) -> tuple[str, ...]:
    checks = [
        "python3 dev/scripts/checks/check_active_plan_sync.py",
        "python3 dev/scripts/checks/check_platform_contract_closure.py --format md",
        "python3 dev/scripts/checks/check_governance_closure.py --format md",
        "python3 dev/scripts/checks/check_multi_agent_sync.py",
    ]
    if action in {"audit-guards", "launch"}:
        checks.append("python3 dev/scripts/devctl.py probe-report --format md")
        checks.append("python3 dev/scripts/devctl.py governance-quality-feedback --format md")
    return tuple(checks)


def _next_commands(action: str) -> tuple[str, ...]:
    if action == "next":
        return ("python3 dev/scripts/devctl.py develop launch --dry-run --max-cycles 1",)
    if action == "audit-guards":
        return (
            "python3 dev/scripts/devctl.py governance-quality-feedback --format md",
            "python3 dev/scripts/devctl.py probe-report --format md",
        )
    if action == "launch":
        return (
            "python3 dev/scripts/devctl.py review-channel --action sync-status --terminal none --format md",
            "python3 dev/scripts/devctl.py develop next --format md",
        )
    return ("python3 dev/scripts/devctl.py develop next --format md",)


__all__ = ["build_report"]
