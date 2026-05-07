"""Next-slice selection for the typed develop controller."""

from __future__ import annotations

from ...runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL, PlanRow
from .models import (
    DevelopmentNextSlice,
    DevelopmentOrchestrationSnapshot,
    DevelopmentPacketAttention,
)


def select_next_slice(
    rows: tuple[PlanRow, ...],
    *,
    packet_attention: DevelopmentPacketAttention | None = None,
    orchestration: DevelopmentOrchestrationSnapshot | None = None,
) -> DevelopmentNextSlice:
    """Select the next bounded development row from typed state."""
    packet_row = _packet_attention_row(rows, packet_attention)
    if packet_row is not None:
        return DevelopmentNextSlice(
            slice_id=packet_row.row_id,
            source=packet_row.source_doc_path or DEFAULT_MASTER_PLAN_STORE_REL,
            title=packet_row.title,
            target_ref=packet_row.target_ref,
            status=packet_row.status,
            reason=(
                "Selected because packet attention requires this durable packet-owned "
                "plan row before ordinary /develop work can continue."
            ),
        )
    if packet_attention is not None and packet_attention.attention_required:
        packet_id = (
            packet_attention.latest_attention_packet_id
            or packet_attention.latest_finding_packet_id
        )
        if packet_id:
            slice_id = f"packet:{packet_id}"
        elif packet_attention.wake_reason == "expired_unresolved_packet":
            slice_id = "packet-debt-audit"
        elif packet_attention.wake_reason == "review_loop_relaunch_required":
            slice_id = "review-loop-relaunch-required"
        elif packet_attention.attention_status == "checkpoint_required":
            slice_id = "checkpoint-required"
        elif packet_attention.attention_status == "blocked":
            slice_id = "runtime-attention-blocked"
        else:
            slice_id = "packet-attention"
        return DevelopmentNextSlice(
            slice_id=slice_id,
            source="ReviewState.packet_inbox",
            title=packet_attention.summary,
            target_ref=packet_attention.required_command,
            status="attention_required",
            reason="Packet attention preempts ordinary typed plan-row selection.",
        )
    selected = _orchestration_blocker_row(rows, orchestration)
    if selected is not None:
        return DevelopmentNextSlice(
            slice_id=selected.row_id,
            source=selected.source_doc_path or DEFAULT_MASTER_PLAN_STORE_REL,
            title=selected.title,
            target_ref=selected.target_ref,
            status=selected.status,
            reason=(
                "Selected from typed orchestration blockers mapped to active "
                "plan rows; compatibility topology labels remain projection "
                "vocabulary, not scheduling authority."
            ),
        )
    selected = _active_leaf_row(rows)
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
        reason=(
            "Selected from typed master-plan rows using active leaf rows; "
            "active parent rows delegate to concrete child rows before "
            "ordinary status ordering."
        ),
    )


def _first_row_with_status(rows: tuple[PlanRow, ...], status: str) -> PlanRow | None:
    for row in rows:
        if row.status == status:
            return row
    return None


def _active_leaf_row(rows: tuple[PlanRow, ...]) -> PlanRow | None:
    active_rows = tuple(
        row for row in rows if row.status in {"in_progress", "queued"}
    )
    leaf_rows = tuple(
        row for row in active_rows if not _has_active_child(row, active_rows)
    )
    selected = _first_row_with_status(leaf_rows, "in_progress")
    if selected is not None:
        return selected
    selected = _first_row_with_status(leaf_rows, "queued")
    if selected is not None:
        return selected
    selected = _first_row_with_status(rows, "in_progress")
    if selected is not None:
        return selected
    return _first_row_with_status(rows, "queued")


def _has_active_child(row: PlanRow, rows: tuple[PlanRow, ...]) -> bool:
    row_refs = {row.row_id, f"plan:{row.row_id}"}
    for candidate in rows:
        if candidate.row_id == row.row_id:
            continue
        if _packet_binding_row(candidate):
            continue
        if row_refs.intersection(candidate.anchor_refs):
            return True
        if candidate.target_ref in row_refs:
            return True
    return False


def _packet_binding_row(row: PlanRow) -> bool:
    return row.row_id.startswith("PKT-BIND-")


def _orchestration_blocker_row(
    rows: tuple[PlanRow, ...],
    orchestration: DevelopmentOrchestrationSnapshot | None,
) -> PlanRow | None:
    if orchestration is None or not orchestration.action_required_count:
        return None
    text = _orchestration_blocker_text(orchestration)
    if not text:
        return None
    categories = _blocker_categories(text)
    for category in categories:
        selected = _first_active_row_by_id(rows, _CATEGORY_ROW_IDS[category])
        if selected is not None:
            return selected
    return None


def _orchestration_blocker_text(
    orchestration: DevelopmentOrchestrationSnapshot,
) -> str:
    values: list[str] = []
    for row in orchestration.agent_loop_decisions:
        if row.safe_to_continue and not row.top_blocker:
            continue
        values.extend(
            (
                row.top_blocker,
                row.required_action,
                row.lifecycle_state,
            )
        )
    for signal in orchestration.signals:
        if signal.status not in {"action_required", "blocked", "stale"}:
            continue
        values.extend(
            (
                signal.summary,
                signal.recommended_action,
                signal.signal_id,
            )
        )
    return " ".join(value for value in values if value).lower()


def _blocker_categories(text: str) -> tuple[str, ...]:
    categories: list[str] = []
    if _has_any(
        text,
        (
            "active_dual_agent",
            "single_agent",
            "tools_only",
            "topology",
            "no_live_agents",
            "reviewer mode",
            "live loop",
            "coordination_resync",
            "resync",
            "inactive",
        ),
    ):
        categories.append("topology")
    if _has_any(
        text,
        (
            "next selector",
            "activeworkenvelope",
            "active work envelope",
            "develop next",
        ),
    ):
        categories.append("selector")
    if _has_any(
        text,
        (
            "checkpoint",
            "index.lock",
            "git_index_write_blocked",
            "import_index_atomicity",
            "dirty_path_budget_exceeded",
            "dirty_after_local_checkpoint",
            "startup authority",
            "startup_authority",
            "managed projection",
            "vcs.stage",
        ),
    ):
        categories.append("checkpoint")
    if _has_any(text, ("code-shape", "code shape", "pytest", "test execution")):
        categories.append("test_policy")
    return tuple(dict.fromkeys(categories))


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


_CATEGORY_ROW_IDS = {
    "topology": (
        "MP377-P0-TOPOLOGY-NEUTRAL-NEXT-S1",
        "MP377-P0-ROLE-MATRIX-ROSTER-S1",
        "MP377-P0-LIFECYCLE-ROLE-SIGNOFF-S1",
        "MP377-P0-T22AN-L",
    ),
    "selector": (
        "MP377-P0-TOPOLOGY-NEUTRAL-NEXT-S1",
        "MP377-P0-ACTIVE-WORK-ENVELOPE-S1",
        "MP377-P0-PACKET-INTAKE-SCHEDULER-S1",
    ),
    "checkpoint": (
        "MP377-P0-CHECKPOINT-AUTOMATION-S1",
        "MP377-P0-T22AN-AB",
    ),
    "test_policy": (
        "MP377-P0-T22AN-AB",
    ),
}


def _first_active_row_by_id(
    rows: tuple[PlanRow, ...],
    row_ids: tuple[str, ...],
) -> PlanRow | None:
    active_by_id = {
        row.row_id: row
        for row in rows
        if row.status in {"in_progress", "queued"} and not _packet_binding_row(row)
    }
    for row_id in row_ids:
        row = active_by_id.get(row_id)
        if row is not None:
            return row
    return None


def _packet_attention_row(
    rows: tuple[PlanRow, ...],
    packet_attention: DevelopmentPacketAttention | None,
) -> PlanRow | None:
    if packet_attention is None or not packet_attention.attention_required:
        return None
    row_id = packet_attention.durable_plan_row_id
    for row in rows:
        if row_id and row.row_id == row_id:
            return row
    packet_id = (
        packet_attention.latest_attention_packet_id
        or packet_attention.latest_finding_packet_id
    )
    if not packet_id:
        return None
    for row in rows:
        if packet_id in row.sourced_from_packets:
            return row
    return None


__all__ = ["select_next_slice"]
