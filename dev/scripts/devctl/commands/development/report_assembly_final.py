"""Final report phase for develop report assembly."""

from __future__ import annotations

from typing import Any

from ...config import REPO_ROOT
from . import report as development_report
from .campaign import campaign_report
from .continuation import continuation_signal
from .design_preflight import build_design_preflight
from .final_response_gate import enforce_final_response_gate
from .lifecycle import LIFECYCLE_ACTIONS
from .report import (
    _proposed_response_text_for_shape,
    _runtime_role_for_actor,
    _session_activity_log_ref_for_actor,
)
from .status_summary import status_for_report, summary_for_action


def build_final_parts(
    args: Any,
    *,
    core: Any,
    blockers: tuple[str, ...],
    final_parts_type: Any,
) -> Any:
    design_preflight = build_design_preflight(
        args=args,
        repo_root=REPO_ROOT,
        review_state=core.review_state,
    )
    watcher_lease = development_report.watcher_lease_status(
        REPO_ROOT,
        core.review_state,
        actor=core.actor,
    )
    campaign = campaign_report(
        core.review_state,
        packet_attention=core.packet_attention,
    )
    current_plan_row_id = _current_plan_goal_id(core)
    continuation = continuation_signal(
        packet_attention=core.packet_attention,
        orchestration=core.orchestration,
        watcher_lease=watcher_lease,
        packet_pressure=core.packet_pressure,
        review_state=core.review_state,
        actor=core.actor,
        current_action=core.action,
        fallback_commands=core.next_commands,
        current_plan_row_id=current_plan_row_id,
    )
    final_response_gate = enforce_final_response_gate(
        continuation,
        packet_attention=core.packet_attention,
        orchestration=core.orchestration,
        next_slice_id=core.next_slice.slice_id,
        current_plan_authority=core.current_plan_authority,
        current_plan_row_id=current_plan_row_id,
        repo_root=REPO_ROOT,
    )
    status = status_for_report(blockers=blockers, continuation=continuation)
    summary = summary_for_action(
        core.action,
        blockers=blockers,
        continuation=continuation,
        lifecycle_actions=LIFECYCLE_ACTIONS,
        drain_packets=bool(getattr(args, "drain_packets", False)),
        dry_run=bool(getattr(args, "dry_run", False)),
    )
    response_text, response_text_source = _proposed_response_text_for_shape(
        args,
        summary=summary,
    )
    reviewer_shape = development_report.reviewer_response_shape_for_gate(
        final_response_gate,
        actor_id=core.actor,
        role=_runtime_role_for_actor(core.runtime, core.actor),
        session_activity_log_ref=_session_activity_log_ref_for_actor(
            core.runtime,
            core.actor,
        ),
        proposed_response_text=response_text,
        proposed_response_text_source=response_text_source,
    )
    return final_parts_type(
        design_preflight=design_preflight,
        watcher_lease=watcher_lease,
        campaign=campaign,
        continuation=continuation,
        final_response_gate=final_response_gate,
        status=status,
        summary=summary,
        reviewer_response_shape=reviewer_shape,
    )


def _current_plan_goal_id(core: Any) -> str:
    next_slice_id = str(getattr(core.next_slice, "slice_id", "") or "")
    if next_slice_id and not next_slice_id.startswith("PKT-BIND-"):
        for row in core.rows:
            if str(getattr(row, "row_id", "") or "") == next_slice_id:
                return next_slice_id
    return str(getattr(core.current_plan_authority, "plan_row_id", "") or "")
