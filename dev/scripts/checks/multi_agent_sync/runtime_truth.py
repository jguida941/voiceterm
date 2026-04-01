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
    errors: list[str] = []

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
        "errors": errors,
    }


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
