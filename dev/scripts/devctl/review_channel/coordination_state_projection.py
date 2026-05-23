"""Build the typed CoordinationStateProjection (rev_pkt_2273/2278/2281/2298).

Per Codex rev_pkt_2298: ``single_agent`` is an authority/review-gate label,
NOT observed runtime topology. When typed session/subagent evidence proves
multiple active AI sessions, the operator-facing projection must say
``multi_agent_active`` while preserving ``single_agent`` only as a
compatibility authority/recovery-gate value.

This is a v1.1 minimum-viable split. The full v1.2 typed-coordination-graph
slice (rev_pkt_2278: actors / sessions / subagents / relationships /
authority / work_board / lane_barriers / stale_or_expired_items /
source_evidence) supersedes this once it lands.

Per rev_pkt_2298 fail-closed rule: when runtime evidence is unknown or
missing, do NOT default to ``single_agent`` — emit ``unknown`` instead.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, TypedDict


#: Role-based coordination topology is a free-form string of the shape
#: ``typed_role_topology[role:provider,provider;role:provider]`` (per
#: ``runtime/role_topology.py:typed_role_topology_label``) or
#: ``"unknown"`` when no live roles can be resolved. The previous
#: agent-count Literal ("multi_agent_active" / "single_agent_active" /
#: "no_active_agents") is retained in ``legacy_topology_label`` as
#: migration-debt evidence per the AntiDumbass amendment and the typed
#: inventory at ``dev/state/topology_hardcode_inventory.jsonl``.
CoordinationTopology = str

#: Deprecated agent-counting topology labels. Listed for downstream
#: consumers that need to recognize legacy values arriving via
#: ``legacy_topology_label`` for compatibility windows. NEVER emit one
#: of these as the canonical ``coordination_topology`` value.
DEPRECATED_AGENT_COUNTING_TOPOLOGY_LABELS = frozenset({
    "multi_agent_active",
    "single_agent_active",
    "no_active_agents",
})


AuthorityMode = Literal[
    "single_writer",
    "shared_writer",
    "review_gated",
    "unknown",
]


RecoveryEligibility = Literal[
    "local_takeover_allowed",
    "remote_only",
    "blocked",
    "unknown",
]


class ObservedRuntime(TypedDict):
    """Factual inventory of what's currently observable on the runtime."""

    active_actor_count: int
    active_runtime_providers: list[str]
    active_operator_channels: list[str]
    active_conductors: list[str]
    detached_runtime_providers: list[str]
    work_board_row_counts: dict[str, int]


class CoordinationStateProjection(TypedDict):
    """4-field topology/authority split per rev_pkt_2273/2281/2298.

    Sibling projection to ``agent_sync`` and ``agent_work_board``; lives at
    ``review_state["coordination_state"]``. Composes with the v1.2 typed
    coordination graph (rev_pkt_2278) which will fan out into the full
    9-row-type structure once landed.

    Schema v2 (2026-05-23): ``coordination_topology`` is now role-based
    vocabulary (``typed_role_topology[reviewer:claude;implementer:codex]``
    or ``"unknown"``). The previous agent-count Literal is retained in
    ``legacy_topology_label`` for migration audit only. Authority
    decisions MUST NOT branch on ``legacy_topology_label``; they MUST
    read role/session-typed state.
    """

    schema_version: int
    contract_id: str
    coordination_topology: CoordinationTopology
    legacy_topology_label: str
    authority_mode: AuthorityMode
    recovery_eligibility: RecoveryEligibility
    observed_runtime: ObservedRuntime
    legacy_reviewer_mode: str
    legacy_authority_label: str
    notes: list[str]


def build_coordination_state_projection(
    *,
    agent_work_board_payload: Mapping[str, object] | None,
    agent_sync_payload: Mapping[str, object] | None,
    collaboration: Mapping[str, object] | None,
    reviewer_runtime: Mapping[str, object] | None = None,
) -> CoordinationStateProjection:
    """Build the 4-field topology/authority split.

    Reads exclusively from typed sources already on ``review_state``:
    work_board rows for observed runtime, agent_sync agents for actor
    inventory, collaboration for legacy authority labels, reviewer_runtime
    for recovery posture. Fails closed to ``unknown`` when evidence is
    missing per rev_pkt_2298.
    """
    work_board = agent_work_board_payload or {}
    rows = work_board.get("rows") or []
    if not isinstance(rows, list):
        rows = []

    active_runtime_providers = _active_runtime_providers(rows)
    active_operator_channels = _active_operator_channels(collaboration)
    active_conductors = _active_conductors(rows)
    detached = _detached_runtime_providers(rows, active_runtime_providers)

    # Per operator directive 2026-04-30: 3 actors = dashboard + claude
    # implementer + codex reviewer. Dashboard counts toward active_actor_count
    # whenever an operator_channel is registered (typed evidence that the
    # operator has a dashboard surface attached). Without this, the typed
    # multi-agent count understates by 1 whenever dashboard is the only
    # operator-side actor.
    active_actor_count = len(active_runtime_providers) + len(active_operator_channels)
    work_board_counts = _row_counts(rows)

    legacy_topology_label = _derive_legacy_topology_label(
        active_actor_count=active_actor_count,
        rows=rows,
    )
    coordination_topology = _derive_role_based_coordination_topology(
        rows=rows,
    )
    authority_mode = _derive_authority_mode(
        collaboration=collaboration or {},
    )
    recovery_eligibility = _derive_recovery_eligibility(
        reviewer_runtime=reviewer_runtime or {},
        active_actor_count=active_actor_count,
    )

    observed_runtime: ObservedRuntime = {
        "active_actor_count": active_actor_count,
        "active_runtime_providers": list(active_runtime_providers),
        "active_operator_channels": list(active_operator_channels),
        "active_conductors": list(active_conductors),
        "detached_runtime_providers": list(detached),
        "work_board_row_counts": work_board_counts,
    }

    legacy_reviewer_mode = str((collaboration or {}).get("reviewer_mode") or "")
    legacy_authority_label = legacy_reviewer_mode or "unknown"

    notes: list[str] = []
    if legacy_topology_label == "multi_agent_active" and legacy_reviewer_mode == "single_agent":
        notes.append(
            "legacy_reviewer_mode='single_agent' is authority/review-gate "
            "vocabulary; observed runtime is multi_agent_active per "
            "agent_work_board.rows. Do NOT use single_agent as topology."
        )
    if legacy_topology_label in DEPRECATED_AGENT_COUNTING_TOPOLOGY_LABELS:
        notes.append(
            f"migration_debt: legacy_topology_label={legacy_topology_label!r} is "
            "an agent-counting label retained for migration audit only. "
            "Read coordination_topology (role-based) for authority decisions."
        )

    return CoordinationStateProjection(
        schema_version=2,
        contract_id="CoordinationStateProjection",
        coordination_topology=coordination_topology,
        legacy_topology_label=legacy_topology_label,
        authority_mode=authority_mode,
        recovery_eligibility=recovery_eligibility,
        observed_runtime=observed_runtime,
        legacy_reviewer_mode=legacy_reviewer_mode,
        legacy_authority_label=legacy_authority_label,
        notes=notes,
    )


def _active_runtime_providers(rows: list) -> list[str]:
    """Distinct providers with ≥1 non-stale active row."""
    providers: dict[str, None] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("status") or "") in {"working", "polling", "blocked"}:
            provider = str(row.get("provider") or "").strip()
            if provider:
                providers.setdefault(provider, None)
    return list(providers.keys())


def _active_operator_channels(
    collaboration: Mapping[str, object] | None,
) -> list[str]:
    """Operator-side channels: dashboard, remote-control surfaces."""
    if not collaboration:
        return []
    channels: list[str] = []
    operator_mode = str(collaboration.get("operator_mode") or "").strip()
    if operator_mode and operator_mode != "unknown":
        channels.append(operator_mode)
    return channels


def _active_conductors(rows: list) -> list[str]:
    """Distinct conductor_id values from non-stale active rows."""
    conductors: dict[str, None] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("status") or "") in {"working", "polling", "blocked"}:
            conductor = str(row.get("conductor_id") or "").strip()
            if conductor:
                conductors.setdefault(conductor, None)
    return list(conductors.keys())


def _detached_runtime_providers(
    rows: list,
    active_providers: list[str],
) -> list[str]:
    """Providers with rows but ZERO active (all idle/stale)."""
    seen: dict[str, None] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider") or "").strip()
        if provider:
            seen.setdefault(provider, None)
    return [p for p in seen if p not in active_providers]


def _row_counts(rows: list) -> dict[str, int]:
    """Count rows by status, role, and confidence_class."""
    by_status: dict[str, int] = {}
    by_role: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status") or "?")
        role = str(row.get("role") or "?")
        confidence = str(row.get("confidence_class") or "?")
        by_status[status] = by_status.get(status, 0) + 1
        by_role[role] = by_role.get(role, 0) + 1
        by_confidence[confidence] = by_confidence.get(confidence, 0) + 1
    return {
        "total": len(rows),
        **{f"status_{k}": v for k, v in by_status.items()},
        **{f"role_{k}": v for k, v in by_role.items()},
        **{f"confidence_{k}": v for k, v in by_confidence.items()},
    }


_LIVE_ROW_STATUSES = frozenset({"working", "polling", "blocked"})


def _derive_role_based_coordination_topology(*, rows: list) -> str:
    """Build a role-based coordination topology label from work_board rows.

    Format: ``typed_role_topology[role1:providerA,providerB;role2:providerC]``.
    Roles and providers are sorted for determinism. Returns ``"unknown"``
    when no live (role, provider) pairs can be resolved, per the
    fail-closed rule in rev_pkt_2298.

    Role membership is NOT gated by a hardcoded whitelist. The repo
    defines 25+ typed role ids in ``runtime/role_profile.py`` (implementer,
    reviewer, architect, researcher, tester, dogfood_test, tdd_first_role,
    tdd_discovery, plan_steward, orchestrator, observer, dashboard,
    watcher, duplicate_scope_guard, operator, ...). Any role that appears
    in a live work_board row counts; the projection does not invent its
    own membership rule. If a role appears in the work_board, it is by
    definition a coordination participant for that emission.

    This is the role-based replacement for the deprecated agent-counting
    ``CoordinationTopology`` Literal. Authority decisions MUST read this
    field; the agent-counting label is now exposed only via
    ``legacy_topology_label`` for migration audit.
    """
    role_to_providers: dict[str, set[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("status") or "") not in _LIVE_ROW_STATUSES:
            continue
        role = str(row.get("role") or "").strip().lower()
        if not role:
            continue
        provider = str(row.get("provider") or "").strip()
        if not provider:
            continue
        role_to_providers.setdefault(role, set()).add(provider)
    if not role_to_providers:
        return "unknown"
    chunks = [
        f"{role}:{','.join(sorted(role_to_providers[role]))}"
        for role in sorted(role_to_providers)
    ]
    return "typed_role_topology[" + ";".join(chunks) + "]"


def _derive_legacy_topology_label(
    *,
    active_actor_count: int,
    rows: list,
) -> str:
    """Per rev_pkt_2298: fail-closed to 'unknown' when no rows."""
    if not rows:
        return "unknown"
    if active_actor_count >= 2:
        return "multi_agent_active"
    if active_actor_count == 1:
        return "single_agent_active"
    return "no_active_agents"


def _derive_authority_mode(
    collaboration: Mapping[str, object],
) -> AuthorityMode:
    """Map legacy reviewer_mode to typed authority_mode per rev_pkt_2298."""
    legacy = str(collaboration.get("reviewer_mode") or "").strip()
    # Per rev_pkt_2298: single_agent legacy is authority/review-gate label.
    if legacy in {"single_agent"}:
        return "single_writer"
    if legacy in {"dual_agent", "active_dual_agent"}:
        return "review_gated"
    if legacy in {"tools_only", "paused", "offline"}:
        return "review_gated"
    return "unknown"


def _derive_recovery_eligibility(
    *,
    reviewer_runtime: Mapping[str, object],
    active_actor_count: int,
) -> RecoveryEligibility:
    """Per rev_pkt_2273: distinguish whether local takeover is allowed."""
    eligibility = str(
        reviewer_runtime.get("recovery_eligibility") or ""
    ).strip()
    if eligibility:
        if eligibility in {
            "local_takeover_allowed",
            "remote_only",
            "blocked",
        }:
            return cast_recovery(eligibility)
    if active_actor_count == 0:
        return "blocked"
    if active_actor_count >= 2:
        return "remote_only"
    return "local_takeover_allowed"


def cast_recovery(value: str) -> RecoveryEligibility:
    """Type-narrow a known string to RecoveryEligibility Literal."""
    return value  # type: ignore[return-value]
