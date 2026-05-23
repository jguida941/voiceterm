#!/usr/bin/env python3
"""Guard the CurrentPlanAuthority composition seam for `/develop`."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        utc_timestamp,
    )

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.commands.development.next_slice import select_next_slice
from dev.scripts.devctl.commands.development.packet_attention import review_state_payload
from dev.scripts.devctl.runtime.current_plan_authority import (
    CurrentPlanAuthority,
    resolve_current_plan_authority,
)
from dev.scripts.devctl.runtime.master_plan_contract import (
    DEFAULT_MASTER_PLAN_STORE_REL,
)
from dev.scripts.devctl.runtime.master_plan_store import read_plan_rows_jsonl

try:
    from .support import (
        CHECK_PATH,
        COMMAND,
        CURRENT_ROW_ID,
        SCENARIO_PATH,
        CurrentPlanAuthorityViolation,
        check_next_slice as _check_next_slice,
        check_source_wiring as _check_source_wiring,
        current_row_has_plan_ingestion_evidence as _current_row_has_plan_ingestion_evidence,
        is_active_pkt_bind_row as _is_active_pkt_bind_row,
        is_executable_plan_row as _is_executable_plan_row,
        packet_rows as _packet_rows,
        row_id as _row_id,
        source_contains as _source_contains,
        terminal_row_selected as _terminal_row_selected,
    )
except ImportError:
    from current_plan_authority.support import (
        CHECK_PATH,
        COMMAND,
        CURRENT_ROW_ID,
        SCENARIO_PATH,
        CurrentPlanAuthorityViolation,
        check_next_slice as _check_next_slice,
        check_source_wiring as _check_source_wiring,
        current_row_has_plan_ingestion_evidence as _current_row_has_plan_ingestion_evidence,
        is_active_pkt_bind_row as _is_active_pkt_bind_row,
        is_executable_plan_row as _is_executable_plan_row,
        packet_rows as _packet_rows,
        row_id as _row_id,
        source_contains as _source_contains,
        terminal_row_selected as _terminal_row_selected,
    )


@dataclass(frozen=True, slots=True)
class CurrentPlanAuthorityGuardReport:
    command: str
    ok: bool
    timestamp: str
    current_plan_row_id: str
    current_plan_row_status: str
    selected_next_slice_id: str
    selected_next_slice_source: str
    executable_plan_row_exists: bool
    executable_plan_row_count: int
    active_pkt_bind_row_count: int
    terminal_selector_violation_count: int
    bound_packet_count: int
    unbound_packet_count: int
    plan_ingestion_evidence_present: bool
    check_router_registered: bool
    bundle_registered: bool
    scenario_path_exists: bool
    checked_surfaces: tuple[str, ...]
    violation_count: int
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = ()
    contract_id: str = "CurrentPlanAuthorityGuard"
    schema_version: int = 1


def evaluate_current_plan_authority(
    *,
    repo_root: Path = REPO_ROOT,
) -> CurrentPlanAuthorityGuardReport:
    from dev.scripts.devctl.governance.script_catalog_registry import (
        CHECK_SCRIPT_RELATIVE_PATHS,
    )

    rows = read_plan_rows_jsonl(repo_root / DEFAULT_MASTER_PLAN_STORE_REL)
    packets = _packet_rows(review_state_payload(repo_root))
    authority = resolve_current_plan_authority(rows, pending_packets=packets)
    next_slice = select_next_slice(
        rows,
        current_plan_authority=authority,
    )
    violations: list[CurrentPlanAuthorityViolation] = []
    warnings: list[str] = []
    executable_rows = tuple(row for row in rows if _is_executable_plan_row(row))
    active_pkt_bind_rows = tuple(row for row in rows if _is_active_pkt_bind_row(row))
    terminal_selected_rows = tuple(row for row in rows if _terminal_row_selected(row))

    _check_authority_selection(
        authority=authority,
        executable_rows=executable_rows,
        violations=violations,
    )
    _check_next_slice(
        next_slice_id=str(getattr(next_slice, "slice_id", "") or ""),
        executable_rows=executable_rows,
        rows=rows,
        violations=violations,
    )
    _check_source_wiring(repo_root=repo_root, violations=violations)

    check_router_registered = (
        CHECK_SCRIPT_RELATIVE_PATHS.get("current_plan_authority")
        == "dev/scripts/checks/check_current_plan_authority.py"
    )
    bundle_registered = _source_contains(
        repo_root / "dev/scripts/devctl/bundles/registry.py",
        'check_script_shell_command("current_plan_authority")',
    )
    scenario_path_exists = (repo_root / SCENARIO_PATH).is_file()
    plan_ingestion_evidence_present = _current_row_has_plan_ingestion_evidence(rows)

    if not check_router_registered:
        violations.append(
            CurrentPlanAuthorityViolation(
                reason="check_router_catalog_missing_current_plan_authority",
                detail="script catalog does not register check_current_plan_authority.py",
                path="dev/scripts/devctl/governance/script_catalog_registry.py",
            )
        )
    if not bundle_registered:
        violations.append(
            CurrentPlanAuthorityViolation(
                reason="bundle_missing_current_plan_authority",
                detail="default guard bundle does not run current_plan_authority",
                path="dev/scripts/devctl/bundles/registry.py",
            )
        )
    if not scenario_path_exists:
        violations.append(
            CurrentPlanAuthorityViolation(
                reason="dogfood_scenario_missing",
                detail=f"required scenario file is missing: {SCENARIO_PATH}",
                path=SCENARIO_PATH,
            )
        )
    if not plan_ingestion_evidence_present:
        warnings.append(
            "current row does not expose plan_intent_receipt evidence in work_evidence_ids"
        )

    return CurrentPlanAuthorityGuardReport(
        command=COMMAND,
        ok=not violations,
        timestamp=utc_timestamp(),
        current_plan_row_id=authority.plan_row_id,
        current_plan_row_status=authority.plan_row_status,
        selected_next_slice_id=str(getattr(next_slice, "slice_id", "") or ""),
        selected_next_slice_source=str(getattr(next_slice, "source", "") or ""),
        executable_plan_row_exists=bool(executable_rows),
        executable_plan_row_count=len(executable_rows),
        active_pkt_bind_row_count=len(active_pkt_bind_rows),
        terminal_selector_violation_count=len(terminal_selected_rows),
        bound_packet_count=len(authority.plan_bound_packet_ids),
        unbound_packet_count=len(authority.unbound_packet_ids),
        plan_ingestion_evidence_present=plan_ingestion_evidence_present,
        check_router_registered=check_router_registered,
        bundle_registered=bundle_registered,
        scenario_path_exists=scenario_path_exists,
        checked_surfaces=(
            "dev/scripts/devctl/runtime/current_plan_authority.py",
            "dev/scripts/devctl/commands/development/next_slice.py",
            "dev/scripts/devctl/commands/development/models.py",
            "dev/scripts/devctl/commands/development/report_assembly.py",
            "dev/scripts/devctl/commands/development/report_assembly_final.py",
            "dev/scripts/devctl/commands/development/final_response_gate.py",
            "dev/scripts/devctl/commands/review_channel/event_queue_report.py",
            "dev/scripts/devctl/governance/script_catalog_registry.py",
            "dev/scripts/devctl/bundles/registry.py",
            SCENARIO_PATH,
        ),
        violation_count=len(violations),
        violations=tuple(violation.to_dict() for violation in violations),
        warnings=tuple(warnings),
    )


def _check_authority_selection(
    *,
    authority: CurrentPlanAuthority,
    executable_rows: tuple[object, ...],
    violations: list[CurrentPlanAuthorityViolation],
) -> None:
    if executable_rows and not authority.has_executable_plan_row:
        violations.append(
            CurrentPlanAuthorityViolation(
                reason="executable_rows_exist_but_authority_empty",
                detail=(
                    "plan_index has queued/in_progress executable rows, but "
                    "CurrentPlanAuthority did not select one"
                ),
                path="dev/state/plan_index.jsonl",
            )
        )
    if authority.plan_row_id.startswith("PKT-BIND-"):
        violations.append(
            CurrentPlanAuthorityViolation(
                reason="pkt_bind_selected_as_current_plan",
                detail=(
                    "CurrentPlanAuthority selected a packet-binding evidence row "
                    f"as executable work: {authority.plan_row_id}"
                ),
                path="dev/state/plan_index.jsonl",
            )
        )
    required_row = next(
        (row for row in executable_rows if _row_id(row) == CURRENT_ROW_ID),
        None,
    )
    if required_row is not None and authority.plan_row_id != CURRENT_ROW_ID:
        violations.append(
            CurrentPlanAuthorityViolation(
                reason="current_plan_authority_selected_wrong_active_row",
                detail=(
                    "The current row exists as executable typed state but "
                    "CurrentPlanAuthority selected "
                    f"{authority.plan_row_id or '(none)'} instead of {CURRENT_ROW_ID}."
                ),
                path="dev/state/plan_index.jsonl",
            )
        )


def _render_md(report: CurrentPlanAuthorityGuardReport) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- current_plan_row_id: `{report.current_plan_row_id}`")
    lines.append(f"- current_plan_row_status: `{report.current_plan_row_status}`")
    lines.append(f"- selected_next_slice_id: `{report.selected_next_slice_id}`")
    lines.append(f"- selected_next_slice_source: `{report.selected_next_slice_source}`")
    lines.append(f"- executable_plan_row_count: {report.executable_plan_row_count}")
    lines.append(f"- active_pkt_bind_row_count: {report.active_pkt_bind_row_count}")
    lines.append(f"- bound_packet_count: {report.bound_packet_count}")
    lines.append(f"- unbound_packet_count: {report.unbound_packet_count}")
    lines.append(f"- plan_ingestion_evidence_present: {report.plan_ingestion_evidence_present}")
    lines.append(f"- check_router_registered: {report.check_router_registered}")
    lines.append(f"- bundle_registered: {report.bundle_registered}")
    lines.append(f"- scenario_path_exists: {report.scenario_path_exists}")
    lines.append(f"- violation_count: {report.violation_count}")
    if report.warnings:
        lines.append("")
        lines.append("## Warnings")
        for warning in report.warnings:
            lines.append(f"- {warning}")
    if report.violations:
        lines.append("")
        lines.append("## Violations")
        for violation in report.violations:
            lines.append(
                "- "
                f"{violation.get('reason')}: {violation.get('detail')} "
                f"({violation.get('path')})"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    try:
        report = evaluate_current_plan_authority()
    # broad-except: allow reason=guard entrypoints must emit structured reports instead of tracebacks fallback=typed runtime error
    except Exception as exc:
        emit_runtime_error(COMMAND, exc)
        return 2
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print(_render_md(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
