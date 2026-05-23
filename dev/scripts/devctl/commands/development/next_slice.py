"""Next-slice selection for the typed develop controller."""

from __future__ import annotations

from collections.abc import Sequence

from ...runtime.current_plan_authority import CurrentPlanAuthority
from ...runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL, PlanRow
from ...triage.findings_priority_models import RankedFinding
from .models import (
    DevelopmentNextSlice,
    DevelopmentOrchestrationSnapshot,
    DevelopmentPacketAttention,
)
from .next_slice_blockers import blocker_categories, category_row_ids

_PREEMPTING_FINDING_SEVERITIES: frozenset[str] = frozenset({"critical", "high"})


def select_next_slice(
    rows: tuple[PlanRow, ...],
    *,
    packet_attention: DevelopmentPacketAttention | None = None,
    orchestration: DevelopmentOrchestrationSnapshot | None = None,
    ranked_findings: Sequence[RankedFinding] | None = None,
    current_plan_authority: CurrentPlanAuthority | None = None,
) -> DevelopmentNextSlice:
    """Select the next bounded development row from typed state."""
    packet_row = _packet_attention_row(rows, packet_attention)
    current_plan_row = _current_authority_row(rows, current_plan_authority)
    if current_plan_row is None:
        current_plan_row = _active_leaf_row(rows)
    selected = _orchestration_blocker_row(rows, orchestration)
    if _packet_attention_closes_orchestration_blocker(
        packet_attention,
        orchestration,
    ):
        return _packet_attention_slice(packet_attention, packet_row)
    if (
        selected is None
        and packet_attention is not None
        and packet_attention.attention_required
        and packet_attention.authority_affecting
        and _packet_attention_can_preempt_current_plan(
            packet_attention=packet_attention,
            packet_row=packet_row,
            current_plan_row=current_plan_row,
        )
    ):
        return _packet_attention_slice(packet_attention, packet_row)
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
    finding_slice = _critical_finding_preemption_slice(
        rows,
        ranked_findings,
        current_plan_row=current_plan_row,
    )
    if finding_slice is not None:
        return finding_slice
    if current_plan_row is not None:
        return _plan_row_slice(
            current_plan_row,
            reason=(
                "Selected from typed current-plan authority; packet backlog is "
                "evidence or communication unless it blocks the current row or "
                "routes through plan-intent ingestion."
            ),
        )
    if packet_attention is not None and packet_attention.attention_required:
        return _packet_attention_slice(packet_attention, packet_row)
    if current_plan_row is None:
        return DevelopmentNextSlice(
            status="none",
            reason="No queued or in-progress typed plan rows found.",
        )
    return _plan_row_slice(
        current_plan_row,
        reason=(
            "Selected from typed master-plan rows using active leaf rows; "
            "active parent rows delegate to concrete child rows before "
            "ordinary status ordering."
        ),
    )


def _plan_row_slice(row: PlanRow, *, reason: str) -> DevelopmentNextSlice:
    return DevelopmentNextSlice(
        slice_id=row.row_id,
        source=row.source_doc_path or DEFAULT_MASTER_PLAN_STORE_REL,
        title=row.title,
        target_ref=row.target_ref,
        status=row.status,
        reason=reason,
    )


def _current_authority_row(
    rows: tuple[PlanRow, ...],
    current_plan_authority: CurrentPlanAuthority | None,
) -> PlanRow | None:
    if current_plan_authority is None or not current_plan_authority.plan_row_id:
        return None
    for row in rows:
        if row.row_id == current_plan_authority.plan_row_id:
            return row
    return None


def _first_row_with_status(rows: tuple[PlanRow, ...], status: str) -> PlanRow | None:
    for row in rows:
        if row.status == status:
            return row
    return None


def _active_leaf_row(rows: tuple[PlanRow, ...]) -> PlanRow | None:
    active_rows = tuple(
        row
        for row in rows
        if row.status in {"in_progress", "queued"} and not _packet_binding_row(row)
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


def _packet_attention_can_preempt_current_plan(
    *,
    packet_attention: DevelopmentPacketAttention,
    packet_row: PlanRow | None,
    current_plan_row: PlanRow | None,
) -> bool:
    if current_plan_row is None:
        return True
    if not packet_attention.authority_affecting:
        return False
    row_ids = {
        current_plan_row.row_id,
        f"plan:{current_plan_row.row_id}",
    }
    durable_row_id = str(packet_attention.durable_plan_row_id or "").strip()
    if durable_row_id in row_ids:
        return True
    return packet_row is not None and packet_row.row_id == current_plan_row.row_id


def _orchestration_blocker_row(
    rows: tuple[PlanRow, ...],
    orchestration: DevelopmentOrchestrationSnapshot | None,
) -> PlanRow | None:
    if orchestration is None or not orchestration.action_required_count:
        return None
    text = _orchestration_blocker_text(orchestration)
    if not text:
        return None
    for category in blocker_categories(text):
        selected = _first_active_row_by_id(rows, category_row_ids(category))
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
                row.why_not_done,
                row.continuation_goal,
                row.user_action,
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


def _packet_attention_slice(
    packet_attention: DevelopmentPacketAttention,
    packet_row: PlanRow | None,
) -> DevelopmentNextSlice:
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
    packet_id = (
        packet_attention.latest_attention_packet_id
        or packet_attention.latest_finding_packet_id
    )
    if packet_attention.wake_reason == "expired_unresolved_packet":
        slice_id = "packet-debt-audit"
    elif packet_attention.wake_reason == "review_loop_relaunch_required":
        slice_id = "review-loop-relaunch-required"
    elif packet_attention.attention_status == "checkpoint_required":
        slice_id = "checkpoint-required"
    elif packet_attention.attention_status == "blocked":
        slice_id = "runtime-attention-blocked"
    elif packet_id:
        slice_id = "communication-packet-attention"
    else:
        slice_id = "packet-attention"
    return DevelopmentNextSlice(
        slice_id=slice_id,
        source="ReviewState.packet_inbox",
        title=packet_attention.summary,
        target_ref=packet_attention.required_command,
        status="attention_required",
        reason=(
            "Communication-only packet attention has no durable plan row; "
            "the packet remains visible in Packet Attention without becoming "
            "an active slice id."
        ),
    )


def _critical_finding_preemption_slice(
    rows: tuple[PlanRow, ...],
    ranked_findings: Sequence[RankedFinding] | None,
    *,
    current_plan_row: PlanRow | None = None,
) -> DevelopmentNextSlice | None:
    """Preempt ordinary plan work with an open critical/high finding.

    Role-flip SLICE-X (codex rev_pkt_4494/4506): unresolved critical/high
    confirmed_issue findings outrank ordinary leaf-row selection in the
    develop-next decision path. The finding is bound to a plan row when its
    primary_file matches an active row's target_ref. Unlinked findings remain
    visible in the finding backlog, but do not become a competing scheduler lane
    while the current plan graph has an executable row.
    """
    if not ranked_findings:
        return None
    active_by_target: dict[str, PlanRow] = {
        row.target_ref: row
        for row in rows
        if (
            row.target_ref
            and row.status in {"in_progress", "queued"}
            and not _packet_binding_row(row)
        )
    }
    for finding in ranked_findings:
        if finding.resolution_state != "open":
            continue
        if finding.severity not in _PREEMPTING_FINDING_SEVERITIES:
            continue
        linked_row = active_by_target.get(finding.primary_file)
        if linked_row is not None:
            if (
                current_plan_row is not None
                and linked_row.row_id != current_plan_row.row_id
            ):
                # A critical finding linked to some other active row remains
                # backlog evidence. It cannot pivot away from the current
                # executable PlanRow without a typed graph-valid pivot receipt.
                continue
            return DevelopmentNextSlice(
                slice_id=linked_row.row_id,
                source=linked_row.source_doc_path or DEFAULT_MASTER_PLAN_STORE_REL,
                title=linked_row.title,
                target_ref=linked_row.target_ref,
                status=linked_row.status,
                reason=(
                    f"Critical/{finding.severity} open finding {finding.qid} at "
                    f"{finding.primary_file} preempts ordinary plan work via "
                    "active plan-row linkage on target_ref."
                ),
            )
        if current_plan_row is not None:
            continue
        return DevelopmentNextSlice(
            slice_id="bug-priority-preemption",
            source="FindingBacklog.ranked_findings",
            title=(
                f"Open {finding.severity} finding {finding.qid} preempts plan work"
            ),
            target_ref=finding.primary_file,
            status="attention_required",
            reason=(
                f"Critical/{finding.severity} open finding {finding.qid} at "
                f"{finding.primary_file} preempts ordinary /develop selection. "
                "No active plan-row linkage on target_ref; surfaced as "
                "finding-priority slice for codex review."
            ),
        )
    return None


def _packet_attention_closes_orchestration_blocker(
    packet_attention: DevelopmentPacketAttention | None,
    orchestration: DevelopmentOrchestrationSnapshot | None,
) -> bool:
    if packet_attention is None or not packet_attention.attention_required:
        return False
    if packet_attention.packet_kind != "action_request":
        return False
    if packet_attention.requested_action != "stage_commit_pipeline":
        return False
    text = _orchestration_blocker_text(orchestration) if orchestration else ""
    return "checkpoint" in blocker_categories(text)


__all__ = ["select_next_slice"]
