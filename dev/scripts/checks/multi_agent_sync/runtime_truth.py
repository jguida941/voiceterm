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
from dev.scripts.devctl.review_channel.agent_loop_decision_projection import (  # pragma: no cover - import wiring
    agent_loop_decisions_for_work_board,
    apply_agent_sync_session_attention_disambiguation,
    apply_scoped_attention_to_ambiguous_packet_attention,
)
from dev.scripts.devctl.review_channel.agent_sync_readers import (  # pragma: no cover - import wiring
    agent_sync_pending_packet_ids_from_row,
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
    payload = _with_pending_agent_loop_projection(payload)

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


def _with_pending_agent_loop_projection(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    """Append missing loop rows for pending packets before validation.

    ``review-channel status`` is allowed to be read-only and may leave the
    persisted latest JSON one projection step behind. The sync guard should
    validate the canonical typed projection, while still preserving existing
    bad rows so drift tests keep failing closed.
    """
    agent_sync = _mapping(payload.get("agent_sync"))
    agents = _mapping(agent_sync.get("agents"))
    pending_agents = set(pending_packet_agents(agents, packet_rows=_packet_rows(payload)))
    if not pending_agents:
        return payload

    work_board = _mapping(payload.get("agent_work_board"))
    if not work_board:
        return payload

    existing = agent_loop_decision_rows(payload)
    projected = agent_loop_decisions_for_work_board(
        review_state=payload,
        work_board=work_board,
    )
    existing, refreshed_lifecycle = _refresh_superseded_lifecycle_decisions(
        existing,
        projected=projected,
        work_board=work_board,
    )
    existing, repaired_existing = _repair_existing_pending_decisions(
        existing,
        agents=agents,
        pending_agents=pending_agents,
        work_board=work_board,
    )
    seen = {_decision_key(row) for row in existing if _decision_key(row)}
    missing = [
        row
        for row in projected
        if str(row.get("actor_id") or "").strip() in pending_agents
        and _decision_key(row)
        and _decision_key(row) not in seen
    ]
    if not missing and not repaired_existing and not refreshed_lifecycle:
        return payload

    updated: dict[str, object] = dict(payload)
    updated["agent_loop_decisions"] = [*existing, *missing]
    updated = apply_agent_sync_session_attention_disambiguation(updated)
    updated = apply_scoped_attention_to_ambiguous_packet_attention(updated)
    return updated


def _refresh_superseded_lifecycle_decisions(
    existing: list[Mapping[str, object]],
    *,
    projected: list[Mapping[str, object]],
    work_board: Mapping[str, object],
) -> tuple[list[Mapping[str, object]], bool]:
    """Replace stale packet-lifecycle rows when active work has advanced.

    The persisted review-state projection can lag a code/read-model repair by
    one write. Preserve normal bad rows so drift still fails closed, but allow
    a stale body-open/semantic/absorption row to be refreshed when the
    recomputed canonical decision agrees with the typed work-board focus.
    """
    if not existing or not projected:
        return existing, False

    projected_by_key = {
        _decision_key(row): row
        for row in projected
        if _decision_key(row)
    }
    work_focus = _work_board_focus_by_key(work_board)
    refreshed: list[Mapping[str, object]] = []
    changed = False
    for row in existing:
        key = _decision_key(row)
        candidate = projected_by_key.get(key)
        if (
            key
            and candidate is not None
            and _packet_lifecycle_row(row)
            and _decision_focus_differs(row, work_focus.get(key, {}))
            and _decision_matches_focus(candidate, work_focus.get(key, {}))
        ):
            replacement = dict(candidate)
            replacement["projection_repaired_from_active_packet_focus"] = True
            refreshed.append(replacement)
            changed = True
            continue
        refreshed.append(row)
    return refreshed, changed


def _work_board_focus_by_key(
    work_board: Mapping[str, object],
) -> dict[tuple[str, str, str], dict[str, str]]:
    rows = work_board.get("rows")
    if not isinstance(rows, list):
        return {}
    focus: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        key = (
            str(row.get("actor_id") or "").strip(),
            str(row.get("role") or "").strip(),
            str(row.get("session_id") or "").strip(),
        )
        if not key[0]:
            continue
        focus[key] = {
            "active_packet_id": str(row.get("active_packet_id") or "").strip(),
            "attention_packet_id": str(row.get("attention_packet_id") or "").strip(),
        }
    return focus


def _packet_lifecycle_row(row: Mapping[str, object]) -> bool:
    return str(row.get("required_action") or "").strip() in {
        "open_packet_body",
        "ingest_packet_semantics",
        "absorb_packet",
    } or str(row.get("reason_code") or "").strip() in {
        "packet_body_open_required",
        "packet_semantic_ingestion_required",
        "packet_absorption_required",
    }


def _decision_focus_differs(
    row: Mapping[str, object],
    focus: Mapping[str, str],
) -> bool:
    return any(
        focus.get(field) and str(row.get(field) or "").strip() != focus[field]
        for field in ("active_packet_id", "attention_packet_id")
    )


def _decision_matches_focus(
    row: Mapping[str, object],
    focus: Mapping[str, str],
) -> bool:
    return all(
        not focus.get(field) or str(row.get(field) or "").strip() == focus[field]
        for field in ("active_packet_id", "attention_packet_id")
    )


def _repair_existing_pending_decisions(
    existing: list[Mapping[str, object]],
    *,
    agents: Mapping[str, object],
    pending_agents: set[str],
    work_board: Mapping[str, object],
) -> tuple[list[Mapping[str, object]], bool]:
    """Annotate stale startup-blocked rows with pending packet counts.

    Read-only runtime truth can lag by one projection step. If a startup-blocked
    row already occupies an actor/session key, queue-target projection cannot
    append the agent-sync pending row. Rows with actual packet focus stay
    untouched so active/attention drift remains blocking.
    """
    if not existing:
        return existing, False
    focused_actors = _work_board_packet_focus_actors(work_board)
    actors_with_pending_decision = {
        str(row.get("actor_id") or "").strip()
        for row in existing
        if _int(row.get("pending_packet_count")) > 0
    }
    if pending_agents <= actors_with_pending_decision:
        return existing, False

    repaired: list[Mapping[str, object]] = []
    changed = False
    for row in existing:
        actor = str(row.get("actor_id") or "").strip()
        if (
            actor in pending_agents
            and actor not in focused_actors
            and actor not in actors_with_pending_decision
            and _row_without_packet_focus(row)
        ):
            pending_count = _agent_sync_pending_packet_count(agents, actor)
            if pending_count > 0:
                updated = dict(row)
                updated["pending_packet_count"] = pending_count
                updated["wake_required"] = True
                updated["projection_repaired_from_agent_sync"] = True
                repaired.append(updated)
                changed = True
                continue
        repaired.append(row)
    return repaired, changed


def _work_board_packet_focus_actors(work_board: Mapping[str, object]) -> set[str]:
    rows = work_board.get("rows")
    if not isinstance(rows, list):
        return set()
    actors: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if not _row_without_packet_focus(row):
            actor = str(row.get("actor_id") or "").strip()
            if actor:
                actors.add(actor)
    return actors


def _row_without_packet_focus(row: Mapping[str, object]) -> bool:
    return not (
        str(row.get("active_packet_id") or "").strip()
        or str(row.get("attention_packet_id") or "").strip()
        or str(row.get("executing_packet_id") or "").strip()
    )


def _agent_sync_pending_packet_count(
    agents: Mapping[str, object],
    actor: str,
) -> int:
    row = agents.get(actor)
    if not isinstance(row, Mapping):
        return 0
    return len(agent_sync_pending_packet_ids_from_row(row))


def _decision_key(row: Mapping[str, object]) -> tuple[str, str, str]:
    actor = str(row.get("actor_id") or "").strip()
    role = str(row.get("actor_role") or "").strip()
    session = str(row.get("session_id") or "").strip()
    if not actor:
        return ("", "", "")
    return (actor, role, session)


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


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


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
