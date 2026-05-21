"""Build the review-channel ``agent_work_board`` projection (v1.1)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace

from ..commands.rollout_tail.constants import (
    CLAUDE_PROJECTS_ROOT,
    CODEX_SESSIONS_ROOT,
    PROVIDER_CLAUDE,
    PROVIDER_CODEX,
)
from ..commands.rollout_tail.discovery import (
    iter_claude_subagent_files,
    session_id_from_path,
)
from .agent_work_board_barriers import (
    build_lane_barriers,
    index_barriers_by_lane,
)
from .agent_work_board_models import (
    AgentWorkBoardProjection,
    AgentWorkBoardRow,
)
from .agent_work_board_packets import (
    _select_current_active_packet_id,
    _select_executing_packet_id,
)
from .agent_work_board_participants import (
    index_participants_by_role,
    resolve_participant,
)
from .agent_work_board_row_builder import build_session_row
from .agent_work_board_roles import build_runtime_role_index
from .agent_work_board_roles import RuntimeRoleResolution
from .agent_work_board_sessions import (
    recent_paths,
    recent_sessions,
    utc_iso_pair_for,
)


_CODEX_SESSION_AGE_CUTOFF_SECONDS = 1_800
_CLAUDE_SESSION_AGE_CUTOFF_SECONDS = 1_800
_CLAUDE_SUBAGENT_AGE_CUTOFF_SECONDS = 600
_MUTATION_CAPABILITIES = frozenset({"repo.stage", "repo.commit"})


def build_agent_work_board_projection(
    *,
    events: list[dict[str, object]],
    packet_rows: list[dict[str, object]],
    agent_sync_payload: dict[str, object] | None,
    collaboration: Mapping[str, object] | None = None,
    refresh_seq: int,
    refreshed_at_utc: str,
) -> AgentWorkBoardProjection:
    """Build the work-board projection from packet rows + sessions + agent_sync."""
    last_event_id = _latest_event_id(events)
    if not last_event_id and agent_sync_payload:
        last_event_id = str(agent_sync_payload.get("source_latest_event_id") or "")

    participants_by_role = index_participants_by_role(collaboration or {})
    role_index = build_runtime_role_index(collaboration or {})
    barriers = build_lane_barriers(agent_sync_payload=agent_sync_payload or {})
    barrier_index = index_barriers_by_lane(barriers)

    rows: list[AgentWorkBoardRow] = []
    rows.extend(
        _build_codex_session_rows(
            packet_rows=packet_rows,
            agent_sync_payload=agent_sync_payload or {},
            barrier_index=barrier_index,
            last_event_id=last_event_id,
            participants_by_role=participants_by_role,
            role_index=role_index,
        )
    )
    rows.extend(
        _build_claude_session_rows(
            packet_rows=packet_rows,
            agent_sync_payload=agent_sync_payload or {},
            barrier_index=barrier_index,
            last_event_id=last_event_id,
            participants_by_role=participants_by_role,
            role_index=role_index,
        )
    )

    return AgentWorkBoardProjection(
        schema_version=1,
        contract_id="AgentWorkBoardProjection",
        source_latest_event_id=last_event_id,
        event_index=last_event_id,
        projection_refresh_seq=refresh_seq,
        refreshed_at_utc=refreshed_at_utc,
        rows=rows,
        barriers=list(barriers),
    )


def _build_codex_session_rows(
    *,
    packet_rows: list[dict[str, object]],
    agent_sync_payload: dict[str, object],
    barrier_index: dict[str, list[str]],
    last_event_id: str,
    participants_by_role: dict[tuple[str, str], Mapping[str, object]],
    role_index: object,
) -> list[AgentWorkBoardRow]:
    sessions = recent_sessions(
        provider=PROVIDER_CODEX,
        root=CODEX_SESSIONS_ROOT,
        cutoff_seconds=_CODEX_SESSION_AGE_CUTOFF_SECONDS,
    )
    aggregate = _agent_sync_row_for(agent_sync_payload, "codex")
    rows: list[AgentWorkBoardRow] = []
    session_count = len(sessions)
    for index, (session_path, started_utc, last_active_utc) in enumerate(sessions, start=1):
        session_id = session_id_from_path(session_path, provider=PROVIDER_CODEX)
        participant = resolve_participant(
            participants_by_role,
            actor_id="codex",
            role="",
        )
        role_resolution = role_index.resolve(
            actor_id="codex",
            provider=PROVIDER_CODEX,
            declared_role=(participant or {}).get("role") if participant else "",
        )
        role_resolution = _session_safe_role_resolution(
            role_resolution,
            provider_session_count=session_count,
        )
        # v4.55.2 (rev_pkt_4767): when multiple recent codex session files
        # exist, only the most-recently-active one is the main conductor.
        # Older entries are read-only helper/explorer sidecars from spawn
        # audits and must not inherit provider-level reviewer authority;
        # demote them to `subagent` so develop next / launch dry-run do
        # not surface them as codex:reviewer controller blockers.
        role_resolution = _demote_helper_codex_session(
            role_resolution,
            session_index=index,
            session_count=session_count,
        )
        rows.append(
            build_session_row(
                actor_id="codex",
                provider=PROVIDER_CODEX,
                role=role_resolution.role,
                declared_role=role_resolution.declared_role,
                authority_role=role_resolution.authority_role,
                role_source=role_resolution.role_source,
                role_scope=role_resolution.role_scope,
                granted_capabilities=role_resolution.granted_capabilities,
                mutation_mode=role_resolution.mutation_mode,
                session_id=session_id,
                subagent_id="",
                lane_id=f"codex_session_{session_id[:12]}",
                instance_num=index,
                started_utc=started_utc,
                last_active_utc=last_active_utc,
                aggregate=aggregate,
                barrier_index=barrier_index,
                packet_rows=packet_rows,
                last_event_id=last_event_id,
                source_surface=str(session_path),
                participant=resolve_participant(
                    participants_by_role,
                    actor_id="codex",
                    role=role_resolution.role,
                ),
            )
        )
    return rows


def _build_claude_session_rows(
    *,
    packet_rows: list[dict[str, object]],
    agent_sync_payload: dict[str, object],
    barrier_index: dict[str, list[str]],
    last_event_id: str,
    participants_by_role: dict[tuple[str, str], Mapping[str, object]],
    role_index: object,
) -> list[AgentWorkBoardRow]:
    sessions = recent_sessions(
        provider=PROVIDER_CLAUDE,
        root=CLAUDE_PROJECTS_ROOT,
        cutoff_seconds=_CLAUDE_SESSION_AGE_CUTOFF_SECONDS,
    )
    aggregate = _agent_sync_row_for(agent_sync_payload, "claude")
    rows: list[AgentWorkBoardRow] = []
    session_count = len(sessions)
    for index, (session_path, started_utc, last_active_utc) in enumerate(sessions, start=1):
        session_id = session_id_from_path(session_path, provider=PROVIDER_CLAUDE)
        participant = resolve_participant(
            participants_by_role,
            actor_id="claude",
            role="",
        )
        role_resolution = role_index.resolve(
            actor_id="claude",
            provider=PROVIDER_CLAUDE,
            declared_role=(participant or {}).get("role") if participant else "",
        )
        role_resolution = _session_safe_role_resolution(
            role_resolution,
            provider_session_count=session_count,
        )
        rows.append(
            build_session_row(
                actor_id="claude",
                provider=PROVIDER_CLAUDE,
                role=role_resolution.role,
                declared_role=role_resolution.declared_role,
                authority_role=role_resolution.authority_role,
                role_source=role_resolution.role_source,
                role_scope=role_resolution.role_scope,
                granted_capabilities=role_resolution.granted_capabilities,
                mutation_mode=role_resolution.mutation_mode,
                session_id=session_id,
                subagent_id="",
                lane_id=f"claude_session_{session_id[:12]}",
                instance_num=index,
                started_utc=started_utc,
                last_active_utc=last_active_utc,
                aggregate=aggregate,
                barrier_index=barrier_index,
                packet_rows=packet_rows,
                last_event_id=last_event_id,
                source_surface=str(session_path),
                participant=resolve_participant(
                    participants_by_role,
                    actor_id="claude",
                    role=role_resolution.role,
                ),
            )
        )
    rows.extend(
        _build_claude_subagent_rows(
            barrier_index=barrier_index,
            packet_rows=packet_rows,
            last_event_id=last_event_id,
            participants_by_role=participants_by_role,
            role_index=role_index,
        )
    )
    return rows


def _build_claude_subagent_rows(
    *,
    barrier_index: dict[str, list[str]],
    packet_rows: list[dict[str, object]],
    last_event_id: str,
    participants_by_role: dict[tuple[str, str], Mapping[str, object]],
    role_index: object,
) -> list[AgentWorkBoardRow]:
    if CLAUDE_PROJECTS_ROOT is None or not CLAUDE_PROJECTS_ROOT.exists():
        return []
    subagents = list(iter_claude_subagent_files(CLAUDE_PROJECTS_ROOT))
    rows: list[AgentWorkBoardRow] = []
    for index, subagent_path in enumerate(
        recent_paths(subagents, cutoff_seconds=_CLAUDE_SUBAGENT_AGE_CUTOFF_SECONDS),
        start=1,
    ):
        started_utc, last_active_utc = utc_iso_pair_for(subagent_path)
        subagent_id = subagent_path.stem
        role_resolution = role_index.resolve(
            actor_id="claude",
            provider=PROVIDER_CLAUDE,
            declared_role="subagent",
        )
        rows.append(
            build_session_row(
                actor_id="claude",
                provider=PROVIDER_CLAUDE,
                role=role_resolution.role,
                declared_role=role_resolution.declared_role,
                authority_role=role_resolution.authority_role,
                role_source=role_resolution.role_source,
                role_scope=role_resolution.role_scope,
                granted_capabilities=role_resolution.granted_capabilities,
                mutation_mode=role_resolution.mutation_mode,
                session_id=subagent_path.parent.parent.name,
                subagent_id=subagent_id,
                lane_id=f"claude_subagent_{subagent_id[:12]}",
                instance_num=index,
                started_utc=started_utc,
                last_active_utc=last_active_utc,
                aggregate=None,
                barrier_index=barrier_index,
                packet_rows=packet_rows,
                last_event_id=last_event_id,
                source_surface=str(subagent_path),
                confidence_override="agent_mind_observation",
                parent_agent_id="claude",
                participant=resolve_participant(
                    participants_by_role,
                    actor_id="claude",
                    role="implementer",
                ),
            )
        )
    return rows


def _agent_sync_row_for(
    payload: dict[str, object],
    agent_id: str,
) -> dict[str, object] | None:
    agents = payload.get("agents") if isinstance(payload, dict) else None
    if not isinstance(agents, dict):
        return None
    row = agents.get(agent_id)
    return row if isinstance(row, dict) else None


def _demote_helper_codex_session(
    resolution: RuntimeRoleResolution,
    *,
    session_index: int,
    session_count: int,
) -> RuntimeRoleResolution:
    """v4.55.2 (rev_pkt_4767): demote non-conductor codex session rows.

    `recent_sessions` returns sessions sorted by mtime descending, so
    `session_index == 1` is the most-recently-active codex session
    (the main conductor / reviewer). Any later index is a read-only
    helper, explorer, or research sidecar left on disk by an earlier
    spawn audit. Those must not inherit provider-level reviewer
    authority from `RuntimeRoleIndex` just because actor_id=codex has
    reviewer authority — otherwise `develop next` and
    `develop launch` dry-run promote helper sidecars to controller
    rows. Demote to `subagent` with read_only mutation and no
    capabilities so the typed lanes see them as evidence-only.
    """
    if session_count <= 1 or session_index == 1:
        return resolution
    if resolution.role in {"subagent", "researcher"}:
        return resolution
    return replace(
        resolution,
        role="subagent",
        role_source="helper_session_demotion",
        role_scope="session",
        mutation_mode="read_only",
        granted_capabilities=(),
    )


def _session_safe_role_resolution(
    resolution: RuntimeRoleResolution,
    *,
    provider_session_count: int,
) -> RuntimeRoleResolution:
    """Keep actor-scoped mutation authority from becoming N session grants."""
    if (
        resolution.role_scope == "actor"
        and provider_session_count > 1
        and resolution.mutation_mode == "live_tree"
    ):
        return replace(
            resolution,
            role="dashboard",
            role_scope="actor_ambiguous",
            mutation_mode="read_only",
            granted_capabilities=tuple(
                capability
                for capability in resolution.granted_capabilities
                if capability not in _MUTATION_CAPABILITIES
            ),
        )
    return resolution


def _latest_event_id(events: Iterable[dict[str, object]]) -> str:
    best_rank = -1
    best_id = ""
    for event in events:
        eid = str(event.get("event_id") or "")
        if not eid.startswith("rev_evt_"):
            continue
        try:
            rank = int(eid[len("rev_evt_"):])
        except ValueError:
            continue
        if rank > best_rank:
            best_rank = rank
            best_id = eid
    return best_id
