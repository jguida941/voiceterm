"""Build individual typed agent work-board rows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from .agent_work_board_models import (
    DEFAULT_STALE_AFTER_SECONDS_BY_ROLE,
    AgentWorkBoardRow,
)
from .agent_work_board_packets import (
    _select_current_active_packet_id,
    _select_executing_packet_id,
    plan_row_for,
)
from .agent_work_board_sessions import now_utc_iso, seconds_between


def build_session_row(
    *,
    actor_id: str,
    provider: str,
    role: str,
    declared_role: str,
    authority_role: str,
    role_source: str,
    role_scope: str,
    granted_capabilities: tuple[str, ...],
    mutation_mode: str,
    session_id: str,
    subagent_id: str,
    lane_id: str,
    instance_num: int,
    started_utc: str,
    last_active_utc: str,
    aggregate: dict[str, object] | None,
    barrier_index: dict[str, list[str]],
    packet_rows: list[dict[str, object]],
    last_event_id: str,
    source_surface: str,
    confidence_override: str = "",
    parent_agent_id: str = "",
    participant: Mapping[str, object] | None = None,
) -> AgentWorkBoardRow:
    barrier_ids = barrier_index.get(lane_id, [])
    attention_packet_id = _select_current_active_packet_id(
        actor_id=actor_id,
        packet_rows=packet_rows,
        target_role=role,
        target_session_id=session_id,
    )
    executing_packet_id = _select_executing_packet_id(
        actor_id=actor_id,
        packet_rows=packet_rows,
        target_role=role,
        target_session_id=session_id,
    )
    elapsed = seconds_between(started_utc, last_active_utc)
    idle = seconds_between(last_active_utc, now_utc_iso())
    stale_after = DEFAULT_STALE_AFTER_SECONDS_BY_ROLE.get(role, 600)
    status = _status_for_row(
        aggregate=aggregate,
        barrier_ids=barrier_ids,
        idle_seconds=idle,
        stale_after_seconds=stale_after,
    )
    parent, conductor, integrator = _agent_relationships(
        actor_id=actor_id,
        role=role,
        parent_agent_id=parent_agent_id,
    )
    worktree, branch, path_scope = _participant_scope(participant)
    confidence = _confidence_class(
        confidence_override=confidence_override,
        idle_seconds=idle,
        stale_after_seconds=stale_after,
        active_packet_id=attention_packet_id,
        participant=participant,
    )

    return AgentWorkBoardRow(
        actor_id=actor_id,
        provider=provider,
        role=role,
        declared_role=declared_role,
        authority_role=authority_role,
        role_source=role_source,
        role_scope=role_scope,
        session_id=session_id,
        subagent_id=subagent_id,
        lane_id=lane_id,
        instance_num=instance_num,
        terminal_label="",
        started_utc=started_utc,
        last_active_utc=last_active_utc,
        idle_seconds=idle,
        parent_agent_id=parent,
        conductor_id=conductor,
        integrator_id=integrator,
        active_packet_id=attention_packet_id,
        attention_packet_id=attention_packet_id,
        executing_packet_id=executing_packet_id,
        plan_row_id=plan_row_for(packet_id=attention_packet_id, packet_rows=packet_rows),
        path_scope=path_scope,
        worktree_identity=worktree,
        branch=branch,
        current_command="",
        current_check="",
        current_file_or_module="",
        status=cast("str", status),  # type: ignore[arg-type]
        elapsed_seconds=elapsed,
        stale_after_seconds=stale_after,
        blocker_or_wait_reason=_blocker_summary(barrier_ids),
        barrier_ids=list(barrier_ids),
        mutation_mode=(
            mutation_mode
            or ("read_only" if role in {"reviewer", "subagent", "dashboard"} else "live_tree")
        ),
        granted_capabilities=list(granted_capabilities),
        expected_output="",
        source_event_id=last_event_id,
        source_surface=source_surface,
        confidence_class=cast("str", confidence),  # type: ignore[arg-type]
    )


def _status_for_row(
    *,
    aggregate: dict[str, object] | None,
    barrier_ids: list[str],
    idle_seconds: int,
    stale_after_seconds: int,
) -> str:
    aggregate_status = str((aggregate or {}).get("derived_status") or "idle")
    status = (
        aggregate_status
        if aggregate_status in {"working", "polling", "blocked", "idle", "checkpointed"}
        else "idle"
    )
    if idle_seconds > stale_after_seconds and not barrier_ids and status != "checkpointed":
        status = "idle"
    if barrier_ids and status not in {"blocked", "checkpointed"}:
        status = "blocked"
    return status


def _confidence_class(
    *,
    confidence_override: str,
    idle_seconds: int,
    stale_after_seconds: int,
    active_packet_id: str,
    participant: Mapping[str, object] | None,
) -> str:
    if confidence_override:
        return confidence_override
    if idle_seconds > stale_after_seconds:
        return "stale"
    if active_packet_id:
        return "direct_typed_event"
    if participant is not None:
        return "derived_typed_event"
    return "inferred"


def _agent_relationships(
    *,
    actor_id: str,
    role: str,
    parent_agent_id: str,
) -> tuple[str, str, str]:
    parent = parent_agent_id or ("operator" if role != "subagent" else "")
    if role == "subagent":
        return parent, parent_agent_id, parent_agent_id
    return parent, actor_id, actor_id


def _participant_scope(
    participant: Mapping[str, object] | None,
) -> tuple[str, str, list[str]]:
    worktree = str((participant or {}).get("worktree") or "")
    branch = str((participant or {}).get("branch") or "")
    workspace_root = str((participant or {}).get("workspace_root") or "")
    return worktree, branch, [workspace_root] if workspace_root else []


def _blocker_summary(barrier_ids: list[str]) -> str:
    if not barrier_ids:
        return ""
    return f"see barrier_ids[0]={barrier_ids[0]}"
