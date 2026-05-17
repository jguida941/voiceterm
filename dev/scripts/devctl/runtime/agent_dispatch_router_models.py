"""Typed task-to-agent dispatch router contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True, slots=True)
class AgentDispatchSessionNode:
    """One addressable live or recent agent session in the dispatch graph."""

    node_id: str = ""
    actor_id: str = ""
    provider: str = ""
    actor_role: str = ""
    declared_role: str = ""
    authority_role: str = ""
    role_source: str = ""
    role_scope: str = ""
    session_id: str = ""
    subagent_id: str = ""
    lane_id: str = ""
    instance_num: int = 0
    worktree_identity: str = ""
    branch: str = ""
    workspace_root: str = ""
    path_scope: tuple[str, ...] = ()
    status: str = ""
    live: bool = False
    freshness_state: str = "unknown"
    last_active_utc: str = ""
    idle_seconds: int = 0
    stale_after_seconds: int = 0
    confidence_class: str = ""
    source_event_id: str = ""
    source_surface: str = ""
    current_command: str = ""
    current_check: str = ""
    current_file_or_module: str = ""
    active_packet_id: str = ""
    attention_packet_id: str = ""
    executing_packet_id: str = ""
    plan_row_id: str = ""
    parent_agent_id: str = ""
    conductor_id: str = ""
    integrator_id: str = ""
    mutation_mode: str = ""
    granted_capabilities: tuple[str, ...] = ()
    work_scope_lease_id: str = ""
    barrier_ids: tuple[str, ...] = ()
    metadata_path: str = ""
    log_path: str = ""
    communication_endpoint_ref: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["path_scope"] = list(self.path_scope)
        payload["granted_capabilities"] = list(self.granted_capabilities)
        payload["barrier_ids"] = list(self.barrier_ids)
        return payload


@dataclass(frozen=True, slots=True)
class AgentDispatchWorkFocus:
    """Current typed work focus for one session node."""

    focus_id: str = ""
    session_node_id: str = ""
    actor_id: str = ""
    actor_role: str = ""
    session_id: str = ""
    current_packet_id: str = ""
    attention_packet_id: str = ""
    executing_packet_id: str = ""
    plan_target_ref: str = ""
    target_kind: str = ""
    target_ref: str = ""
    target_revision: str = ""
    current_instruction_revision: str = ""
    lifecycle_state: str = ""
    latest_event_id: str = ""
    requested_action: str = ""
    policy_hint: str = ""
    requested_session_visibility: str = ""
    source_contracts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["source_contracts"] = list(self.source_contracts)
        return payload


@dataclass(frozen=True, slots=True)
class AgentDispatchPeerLink:
    """Typed communication or coordination edge between session graph nodes."""

    link_id: str = ""
    from_node_id: str = ""
    to_node_id: str = ""
    link_kind: str = ""
    packet_id: str = ""
    plan_target_ref: str = ""
    freshness_state: str = ""
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True, slots=True)
class AgentDispatchAmbiguousGroup:
    """One fail-closed dispatch ambiguity with competing session nodes."""

    group_id: str = ""
    group_kind: str = ""
    actor_id: str = ""
    actor_role: str = ""
    packet_id: str = ""
    plan_target_ref: str = ""
    session_node_ids: tuple[str, ...] = ()
    reason: str = ""
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["session_node_ids"] = list(self.session_node_ids)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True, slots=True)
class AgentDispatchGovernanceDebt:
    """Typed routing debt that must be remediated before autonomous dispatch."""

    debt_id: str = ""
    debt_kind: str = ""
    severity: str = "high"
    route_id: str = ""
    session_node_id: str = ""
    actor_id: str = ""
    actor_role: str = ""
    session_id: str = ""
    packet_id: str = ""
    plan_target_ref: str = ""
    reason: str = ""
    required_remediation: str = ""
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True, slots=True)
class AgentDispatchRoute:
    """One candidate route from typed work to one actor/session."""

    route_id: str = ""
    session_node_id: str = ""
    actor_id: str = ""
    provider: str = ""
    actor_role: str = ""
    session_id: str = ""
    lane_id: str = ""
    worktree_identity: str = ""
    branch: str = ""
    target_kind: str = ""
    target_ref: str = ""
    target_revision: str = ""
    packet_id: str = ""
    plan_target_ref: str = ""
    dispatch_kind: str = "observation"
    requested_session_visibility: str = ""
    required_capabilities: tuple[str, ...] = ()
    guard_bundle: str = ""
    preflight_command: str = ""
    path_scope: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    source_contracts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["required_capabilities"] = list(self.required_capabilities)
        payload["path_scope"] = list(self.path_scope)
        payload["evidence_refs"] = list(self.evidence_refs)
        payload["source_contracts"] = list(self.source_contracts)
        return payload


@dataclass(frozen=True, slots=True)
class AgentDispatchRejection:
    """A rejected route candidate with typed routing evidence."""

    route_id: str = ""
    actor_id: str = ""
    provider: str = ""
    actor_role: str = ""
    session_id: str = ""
    packet_id: str = ""
    reason: str = ""
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True, slots=True)
class AgentDispatchRouter:
    """Read-only top-level router that selects typed work ownership.

    This contract decides route ownership only. It deliberately does not set
    loop execution fields such as ``may_mutate`` or ``can_run_next_command``;
    those remain owned by AgentLoopDecision.
    """

    contract_id: str = "AgentDispatchRouter"
    schema_version: int = 1
    snapshot_id: str = ""
    source_identity: dict[str, str] = field(default_factory=dict)
    source_contract: str = "ReviewState"
    source_command: str = ""
    repo_id: str = ""
    input_refs: dict[str, str] = field(default_factory=dict)
    session_nodes: tuple[AgentDispatchSessionNode, ...] = ()
    work_focus: tuple[AgentDispatchWorkFocus, ...] = ()
    peer_links: tuple[AgentDispatchPeerLink, ...] = ()
    ambiguous_session_groups: tuple[AgentDispatchAmbiguousGroup, ...] = ()
    governance_debt: tuple[AgentDispatchGovernanceDebt, ...] = ()
    routes: tuple[AgentDispatchRoute, ...] = ()
    rejected_routes: tuple[AgentDispatchRejection, ...] = ()
    selected_route_id: str = ""
    selected_route_ids: tuple[str, ...] = ()
    selection_reason: str = ""
    router_state: str = "no_dispatchable_work"

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_id": self.contract_id,
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "source_identity": dict(self.source_identity),
            "source_contract": self.source_contract,
            "source_command": self.source_command,
            "repo_id": self.repo_id,
            "input_refs": dict(self.input_refs),
            "session_nodes": [node.to_dict() for node in self.session_nodes],
            "work_focus": [focus.to_dict() for focus in self.work_focus],
            "peer_links": [link.to_dict() for link in self.peer_links],
            "ambiguous_session_groups": [
                group.to_dict() for group in self.ambiguous_session_groups
            ],
            "governance_debt": [debt.to_dict() for debt in self.governance_debt],
            "routes": [route.to_dict() for route in self.routes],
            "rejected_routes": [
                rejection.to_dict() for rejection in self.rejected_routes
            ],
            "selected_route_id": self.selected_route_id,
            "selected_route_ids": list(self.selected_route_ids),
            "selection_reason": self.selection_reason,
            "router_state": self.router_state,
        }


__all__ = [
    "AgentDispatchAmbiguousGroup",
    "AgentDispatchGovernanceDebt",
    "AgentDispatchPeerLink",
    "AgentDispatchRejection",
    "AgentDispatchRoute",
    "AgentDispatchRouter",
    "AgentDispatchSessionNode",
    "AgentDispatchWorkFocus",
]
