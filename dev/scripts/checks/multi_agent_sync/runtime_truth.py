"""Runtime-truth checks for planned multi-agent markdown surfaces."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.runtime.review_state_locator import (  # pragma: no cover - import wiring
    load_review_state_payload,
    resolved_review_state_relative_path,
)
from dev.scripts.devctl.runtime.agent_dispatch_router import (  # pragma: no cover - import wiring
    build_agent_dispatch_router,
)

if __package__:
    from .runtime_truth_agent_loop import (
        agent_loop_decision_errors,
        agent_loop_decision_rows,
        pending_packet_agents,
    )
else:  # pragma: no cover - standalone package fallback
    from runtime_truth_agent_loop import (
        agent_loop_decision_errors,
        agent_loop_decision_rows,
        pending_packet_agents,
    )


def evaluate_runtime_truth(
    *,
    repo_root: Path,
    planned_agent_ids: Sequence[str],
) -> dict[str, object]:
    """Validate that static AGENT rows do not leak into typed runtime truth."""
    payload = load_review_state_payload(repo_root)
    if not isinstance(payload, Mapping):
        return {
            "checked": False,
            "review_state_path": "",
            "errors": [],
        }
    collaboration = _mapping(payload.get("collaboration"))
    registry = _mapping(payload.get("registry"))
    if not collaboration or not registry:
        return {
            "checked": False,
            "review_state_path": resolved_review_state_relative_path(repo_root),
            "errors": [],
        }

    planned_ids = {
        str(agent).strip().upper()
        for agent in planned_agent_ids
        if str(agent).strip()
    }
    participant_ids = _agent_id_rows(collaboration.get("participants"))
    registry_ids = _agent_id_rows(registry.get("agents"))
    planned_receipts = _agent_id_rows(collaboration.get("delegated_work"))
    live_receipts = _live_receipt_ids(collaboration.get("delegated_work"))
    runtime = _runtime_summary(payload)
    errors: list[str] = []
    warnings = _runtime_warnings(runtime)
    errors.extend(agent_loop_decision_errors(payload))
    errors.extend(_router_governance_debt_errors(payload))

    leaked_participants = _planned_overlap(participant_ids, planned_ids)
    if leaked_participants:
        errors.append(
            "Planned AGENT rows leaked into live collaboration participants: "
            + ", ".join(leaked_participants)
        )

    leaked_registry = _planned_overlap(registry_ids - live_receipts, planned_ids)
    if leaked_registry:
        errors.append(
            "Planned AGENT rows leaked into runtime registry without live worker receipts: "
            + ", ".join(leaked_registry)
        )

    planned_receipts_in_registry = sorted((planned_receipts - live_receipts) & registry_ids)
    if planned_receipts_in_registry:
        errors.append(
            "Delegated planned-work receipts appeared in the runtime registry before they were live: "
            + ", ".join(planned_receipts_in_registry)
        )

    if _ready_gate_status(collaboration, "delegated_work") == "not_requested" and live_receipts:
        errors.append(
            "Delegated workers were marked live even though the collaboration ready gate says fanout was not requested."
        )

    return {
        "checked": True,
        "review_state_path": resolved_review_state_relative_path(repo_root),
        **runtime,
        "errors": errors,
        "warnings": warnings,
    }


def _runtime_summary(payload: Mapping[str, object]) -> dict[str, object]:
    coordination = _mapping(payload.get("coordination_state"))
    observed = _mapping(coordination.get("observed_runtime"))
    agent_sync = _mapping(payload.get("agent_sync"))
    agents = _mapping(agent_sync.get("agents"))
    work_board = _mapping(payload.get("agent_work_board"))
    rows = work_board.get("rows")
    work_rows = rows if isinstance(rows, list) else []
    decision_rows = agent_loop_decision_rows(payload)
    return {
        "coordination_topology": str(
            coordination.get("coordination_topology") or ""
        ).strip(),
        "legacy_reviewer_mode": str(
            coordination.get("legacy_reviewer_mode") or ""
        ).strip(),
        "active_runtime_providers": _string_items(
            observed.get("active_runtime_providers")
        ),
        "agent_work_board_row_count": len(work_rows),
        "agent_loop_decision_row_count": len(decision_rows),
        "pending_packet_agents": pending_packet_agents(
            agents,
            packet_rows=_packet_rows(payload),
        ),
    }


def _runtime_warnings(runtime: Mapping[str, object]) -> list[str]:
    topology = str(runtime.get("coordination_topology") or "").strip()
    legacy_mode = str(runtime.get("legacy_reviewer_mode") or "").strip()
    if not topology or not legacy_mode or topology == legacy_mode:
        return []
    return [
        "Typed coordination topology differs from legacy reviewer mode: "
        f"coordination_topology={topology}; legacy_reviewer_mode={legacy_mode}. "
        "Use coordination_topology for runtime topology."
    ]


def _router_governance_debt_errors(
    payload: Mapping[str, object],
) -> list[str]:
    router = payload.get("agent_dispatch_router")
    if not isinstance(router, Mapping):
        router = build_agent_dispatch_router(review_state=payload).to_dict()
    debts = router.get("governance_debt")
    if not isinstance(debts, list):
        return []
    errors: list[str] = []
    for debt in debts:
        if not isinstance(debt, Mapping):
            continue
        severity = str(debt.get("severity") or "").strip()
        debt_kind = str(debt.get("debt_kind") or "").strip()
        if severity != "critical":
            continue
        errors.append(
            "Agent dispatch router critical governance debt: "
            f"{debt_kind}; actor={debt.get('actor_id') or ''}; "
            f"role={debt.get('actor_role') or ''}; "
            f"session={debt.get('session_id') or ''}; "
            f"packet={debt.get('packet_id') or ''}; "
            f"plan={debt.get('plan_target_ref') or ''}; "
            f"reason={debt.get('reason') or ''}."
        )
    return errors


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _packet_rows(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    rows = payload.get("packets")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _agent_id_rows(rows: object) -> set[str]:
    if not isinstance(rows, list):
        return set()
    return {
        text
        for row in rows
        if isinstance(row, Mapping)
        for text in [str(row.get("agent_id") or "").strip()]
        if text
    }


def _live_receipt_ids(rows: object) -> set[str]:
    if not isinstance(rows, list):
        return set()
    return {
        str(row.get("agent_id") or "").strip()
        for row in rows
        if isinstance(row, Mapping)
        and str(row.get("agent_id") or "").strip()
        and bool(row.get("live"))
    }


def _planned_overlap(agent_ids: set[str], planned_agent_ids: set[str]) -> list[str]:
    return sorted(
        agent_id
        for agent_id in agent_ids
        if agent_id.upper() in planned_agent_ids
    )


def _ready_gate_status(
    collaboration: Mapping[str, object],
    gate_id: str,
) -> str:
    gates = collaboration.get("ready_gates")
    if not isinstance(gates, list):
        return ""
    for gate in gates:
        if not isinstance(gate, Mapping):
            continue
        if str(gate.get("gate_id") or "").strip() == gate_id:
            return str(gate.get("status") or "").strip()
    return ""


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
