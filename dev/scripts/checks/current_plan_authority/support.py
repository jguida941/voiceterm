"""Support helpers for the CurrentPlanAuthority guard."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

COMMAND = "check_current_plan_authority"
CURRENT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
EXECUTABLE_STATUSES = frozenset({"queued", "in_progress"})
NON_EXECUTABLE_TERMINAL_STATUSES = frozenset(
    {"applied", "completed", "closed", "archived", "tombstone"}
)
CHECK_PATH = "dev/scripts/checks/check_current_plan_authority.py"
SCENARIO_PATH = (
    "dev/scripts/devctl/tests/scenarios/"
    "test_current_plan_authority_dogfood.py"
)


@dataclass(frozen=True, slots=True)
class CurrentPlanAuthorityViolation:
    reason: str
    detail: str
    path: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def check_next_slice(
    *,
    next_slice_id: str,
    executable_rows: tuple[object, ...],
    rows: tuple[object, ...],
    violations: list[CurrentPlanAuthorityViolation],
) -> None:
    if next_slice_id.startswith("PKT-BIND-"):
        violations.append(
            CurrentPlanAuthorityViolation(
                reason="pkt_bind_selected_as_next_slice",
                detail=f"develop next selected packet-binding row {next_slice_id}",
                path="dev/state/plan_index.jsonl",
            )
        )
    if executable_rows and looks_like_packet_id(next_slice_id):
        violations.append(
            CurrentPlanAuthorityViolation(
                reason="packet_selected_while_executable_plan_exists",
                detail=(
                    "develop next selected a packet id while executable PlanRows "
                    f"exist: {next_slice_id}"
                ),
                path="dev/reports/review_channel/projections/latest/review_state.json",
            )
        )
    row_by_id = {row_id(row): row for row in rows}
    selected_row = row_by_id.get(next_slice_id)
    if (
        selected_row is not None
        and row_status(selected_row) in NON_EXECUTABLE_TERMINAL_STATUSES
    ):
        violations.append(
            CurrentPlanAuthorityViolation(
                reason="terminal_row_selected_as_next_slice",
                detail=(
                    "develop next selected a terminal row as executable current "
                    f"work: {next_slice_id}"
                ),
                path="dev/state/plan_index.jsonl",
            )
        )


def check_source_wiring(
    *,
    repo_root: Path,
    violations: list[CurrentPlanAuthorityViolation],
) -> None:
    required_terms = {
        "dev/scripts/devctl/commands/development/models.py": "current_plan_authority: Any",
        "dev/scripts/devctl/commands/development/report_assembly.py": (
            "current_plan_authority=core.current_plan_authority"
        ),
        "dev/scripts/devctl/commands/development/report_assembly_final.py": (
            "current_plan_authority=core.current_plan_authority"
        ),
        "dev/scripts/devctl/commands/development/final_response_gate.py": (
            "current_plan_authority: CurrentPlanAuthority | None"
        ),
        "dev/scripts/devctl/commands/review_channel/event_queue_report.py": (
            "plan_rows=_read_plan_rows(repo_root)"
        ),
    }
    for rel_path, term in required_terms.items():
        path = repo_root / rel_path
        if source_contains(path, term):
            continue
        violations.append(
            CurrentPlanAuthorityViolation(
                reason="current_plan_authority_wiring_missing",
                detail=f"expected source term not found: {term}",
                path=rel_path,
            )
        )


def packet_rows(review_state: object) -> tuple[dict[str, object], ...]:
    if not isinstance(review_state, dict):
        return ()
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, dict))


def is_executable_plan_row(row: object) -> bool:
    return (
        row_status(row) in EXECUTABLE_STATUSES
        and not row_id(row).startswith("PKT-BIND-")
        and row_kind(row) != "packet_binding"
    )


def is_active_pkt_bind_row(row: object) -> bool:
    return row_status(row) in EXECUTABLE_STATUSES and row_id(row).startswith(
        "PKT-BIND-"
    )


def terminal_row_selected(row: object) -> bool:
    return row_status(row) in NON_EXECUTABLE_TERMINAL_STATUSES and False


def current_row_has_plan_ingestion_evidence(rows: tuple[object, ...]) -> bool:
    for row in rows:
        if row_id(row) != CURRENT_ROW_ID:
            continue
        evidence_ids = getattr(row, "work_evidence_ids", ())
        return any(str(item).startswith("plan_intent_receipt:") for item in evidence_ids)
    return False


def source_contains(path: Path, term: str) -> bool:
    try:
        return term in path.read_text(encoding="utf-8")
    except OSError:
        return False


def row_id(row: object) -> str:
    return str(getattr(row, "row_id", "") or "").strip()


def row_status(row: object) -> str:
    return str(getattr(row, "status", "") or "").strip()


def row_kind(row: object) -> str:
    return str(getattr(row, "row_kind", "") or "").strip()


def looks_like_packet_id(value: str) -> bool:
    return value.startswith(("rev_pkt_", "pkt_", "packet:"))
