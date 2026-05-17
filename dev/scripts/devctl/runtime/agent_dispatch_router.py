"""Build the typed task-to-agent dispatch router projection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from .agent_dispatch_router_models import (
    AgentDispatchAmbiguousGroup,
    AgentDispatchGovernanceDebt,
    AgentDispatchPeerLink,
    AgentDispatchRejection,
    AgentDispatchRoute,
    AgentDispatchRouter,
    AgentDispatchSessionNode,
    AgentDispatchWorkFocus,
)
from .value_coercion import coerce_mapping as _mapping
from .value_coercion import coerce_text as _text

_EVENT_ID_RE = re.compile(r"rev_evt_(\d+)$")
_ROLE_ALIASES = {
    "coder": "implementer",
    "coding": "implementer",
    "implementation": "implementer",
    "implementer": "implementer",
    "review": "reviewer",
    "reviewer": "reviewer",
    "dashboard": "dashboard",
    "observer": "dashboard",
    "watcher": "dashboard",
    "operator": "operator",
    "remote_operator": "operator",
    "subagent": "subagent",
}


def build_agent_dispatch_router(
    *,
    review_state: Mapping[str, object],
    work_intake: Mapping[str, object] | None = None,
    project_governance: Mapping[str, object] | None = None,
    guard_dispatch: Mapping[str, object] | None = None,
) -> AgentDispatchRouter:
    """Resolve one read-only dispatch router state from typed runtime inputs."""
    session_nodes = _session_nodes(review_state)
    routes = _candidate_routes(
        review_state=review_state,
        work_intake=work_intake or {},
        guard_dispatch=guard_dispatch or {},
        session_nodes=session_nodes,
    )
    rejections = _scope_rejections(
        review_state=review_state,
        routes=routes,
    )
    rejections.extend(
        _actor_session_rejections(
            routes=routes,
            session_nodes=session_nodes,
        )
    )
    rejections.extend(
        _stale_session_rejections(
            routes=routes,
            session_nodes=session_nodes,
        )
    )
    rejections.extend(
        _capability_rejections(
            routes=routes,
            session_nodes=session_nodes,
        )
    )
    scope_rejected_route_ids = {rejection.route_id for rejection in rejections}
    ambiguity_rejections = _ambiguity_rejections(
        tuple(route for route in routes if route.route_id not in scope_rejected_route_ids)
    )
    all_rejections = tuple([*rejections, *ambiguity_rejections])
    selected_route_ids, reason, state = _select_routes(routes, all_rejections)
    work_focus = _work_focus(review_state=review_state, session_nodes=session_nodes)
    peer_links = _peer_links(
        review_state=review_state,
        session_nodes=session_nodes,
        work_focus=work_focus,
    )
    ambiguous_groups = _ambiguous_session_groups(
        routes=routes,
        rejections=all_rejections,
        session_nodes=session_nodes,
    )
    governance_debt = _governance_debt(
        review_state=review_state,
        session_nodes=session_nodes,
        work_focus=work_focus,
        routes=routes,
        ambiguous_groups=ambiguous_groups,
    )
    return AgentDispatchRouter(
        snapshot_id=_text(review_state.get("snapshot_id")),
        source_identity=_source_identity(review_state),
        source_contract=_text(review_state.get("source_contract")) or "ReviewState",
        source_command=_text(review_state.get("source_command")),
        repo_id=_repo_id(project_governance or {}, review_state),
        input_refs=_input_refs(review_state=review_state, work_intake=work_intake or {}),
        session_nodes=session_nodes,
        work_focus=work_focus,
        peer_links=peer_links,
        ambiguous_session_groups=ambiguous_groups,
        governance_debt=governance_debt,
        routes=routes,
        rejected_routes=all_rejections,
        selected_route_id=selected_route_ids[0] if selected_route_ids else "",
        selected_route_ids=selected_route_ids,
        selection_reason=reason,
        router_state=state,
    )


def _candidate_routes(
    *,
    review_state: Mapping[str, object],
    work_intake: Mapping[str, object],
    guard_dispatch: Mapping[str, object],
    session_nodes: tuple[AgentDispatchSessionNode, ...],
) -> tuple[AgentDispatchRoute, ...]:
    routes: list[AgentDispatchRoute] = []
    packet_rows = _packet_rows(review_state)
    work_rows = _work_board_rows(review_state)
    decisions = _decision_rows(review_state)
    guard_bundle = _guard_bundle(guard_dispatch)
    preflight = _preflight_command(guard_dispatch)
    route_keys: set[str] = set()
    for decision in decisions:
        actor = _text(decision.get("actor_id"))
        packet_id = _text(decision.get("active_packet_id")) or _text(
            decision.get("attention_packet_id")
        )
        if not actor or not packet_id:
            continue
        work_row = _matching_work_row(
            work_rows,
            actor=actor,
            role=decision.get("actor_role"),
            session=decision.get("session_id"),
        )
        packet = _packet_by_id(packet_rows, packet_id)
        route = _route_from_sources(
            decision=decision,
            work_row=work_row,
            packet=packet,
            packet_id=packet_id,
            guard_bundle=guard_bundle,
            preflight_command=preflight,
            session_nodes=session_nodes,
        )
        if route.route_id in route_keys:
            continue
        routes.append(route)
        route_keys.add(route.route_id)

    queue_route = _queue_route(
        review_state=review_state,
        work_rows=work_rows,
        guard_bundle=guard_bundle,
        preflight_command=preflight,
        session_nodes=session_nodes,
    )
    if queue_route and queue_route.route_id not in route_keys:
        routes.append(queue_route)

    plan_route = _work_intake_plan_route(
        work_intake=work_intake,
        guard_bundle=guard_bundle,
        preflight_command=preflight,
    )
    if plan_route and plan_route.route_id not in route_keys:
        routes.append(plan_route)
    return tuple(routes)


def _route_from_sources(
    *,
    decision: Mapping[str, object],
    work_row: Mapping[str, object],
    packet: Mapping[str, object],
    packet_id: str,
    guard_bundle: str,
    preflight_command: str,
    session_nodes: tuple[AgentDispatchSessionNode, ...],
) -> AgentDispatchRoute:
    actor = _text(decision.get("actor_id"))
    role = _normalize_route_role(decision.get("actor_role"))
    session = _text(decision.get("session_id"))
    route_key = "|".join((actor, role, session, packet_id))
    target_ref = _text(packet.get("target_ref")) or _text(decision.get("plan_target_ref"))
    plan_ref = _text(decision.get("plan_target_ref")) or _plan_ref_for_packet(packet)
    dispatch_kind = "packet" if packet_id else "observation"
    return AgentDispatchRoute(
        route_id=f"route:{route_key}",
        session_node_id=_session_node_id_for(
            session_nodes,
            actor=actor,
            role=role,
            session=session,
        ),
        actor_id=actor,
        provider=_text(work_row.get("provider")) or actor,
        actor_role=role,
        session_id=session,
        lane_id=_text(work_row.get("lane_id")),
        worktree_identity=_text(work_row.get("worktree_identity")),
        branch=_text(work_row.get("branch")),
        target_kind=_text(packet.get("target_kind")),
        target_ref=target_ref,
        target_revision=_text(packet.get("target_revision")),
        packet_id=packet_id,
        plan_target_ref=plan_ref,
        dispatch_kind=dispatch_kind,
        required_capabilities=_required_capabilities(decision, packet),
        guard_bundle=guard_bundle,
        preflight_command=preflight_command,
        path_scope=_string_tuple(work_row.get("path_scope")),
        evidence_refs=(
            _text(packet.get("latest_event_id")),
            _text(decision.get("source_latest_event_id")),
            _text(work_row.get("source_event_id")),
        ),
        source_contracts=(
            "ReviewPacketState",
            "AgentLoopDecision",
            "AgentWorkBoardProjection",
        ),
    )


def _queue_route(
    *,
    review_state: Mapping[str, object],
    work_rows: tuple[Mapping[str, object], ...],
    guard_bundle: str,
    preflight_command: str,
    session_nodes: tuple[AgentDispatchSessionNode, ...],
) -> AgentDispatchRoute | None:
    queue = _mapping(review_state.get("queue"))
    source = _mapping(queue.get("derived_next_instruction_source"))
    packet_id = _text(source.get("packet_id"))
    actor = _text(source.get("to_agent"))
    if not packet_id or not actor:
        return None
    role = _normalize_route_role(source.get("target_role"))
    session = _text(source.get("target_session_id"))
    if not session:
        fresh_matches = _fresh_nodes_for_actor(
            session_nodes,
            actor=actor,
            role=role,
        )
        if len(fresh_matches) == 1:
            resolved = fresh_matches[0]
            role = role or resolved.actor_role
            session = resolved.session_id
    work_row = _matching_work_row(work_rows, actor=actor, role=role, session=session)
    route_id = "|".join((actor, role, session, packet_id))
    plan_ref = _text(source.get("plan_target_ref"))
    if not plan_ref and _text(source.get("target_kind")) == "plan":
        plan_ref = _text(source.get("target_ref"))
    return AgentDispatchRoute(
        route_id=f"route:{route_id}",
        session_node_id=_session_node_id_for(
            session_nodes,
            actor=actor,
            role=role,
            session=session,
        ),
        actor_id=actor,
        provider=_text(work_row.get("provider")) or actor,
        actor_role=role,
        session_id=session,
        lane_id=_text(work_row.get("lane_id")),
        worktree_identity=_text(work_row.get("worktree_identity")),
        branch=_text(work_row.get("branch")),
        target_kind=_text(source.get("target_kind")),
        target_ref=_text(source.get("target_ref")),
        target_revision=_text(source.get("target_revision")),
        packet_id=packet_id,
        plan_target_ref=plan_ref,
        dispatch_kind="packet",
        required_capabilities=_required_capabilities({}, source),
        guard_bundle=guard_bundle,
        preflight_command=preflight_command,
        path_scope=_string_tuple(work_row.get("path_scope")),
        evidence_refs=(_text(source.get("source_event_id")), packet_id),
        source_contracts=("ReviewQueueState", "InstructionPriorityDecision"),
    )


def _work_intake_plan_route(
    *,
    work_intake: Mapping[str, object],
    guard_bundle: str,
    preflight_command: str,
) -> AgentDispatchRoute | None:
    active_target = _mapping(work_intake.get("active_target"))
    if not active_target:
        return None
    target_id = _text(active_target.get("target_id")) or _text(
        active_target.get("anchor_ref")
    )
    if not target_id:
        return None
    routing = _mapping(work_intake.get("routing"))
    ownership = _mapping(work_intake.get("ownership"))
    return AgentDispatchRoute(
        route_id=f"route:plan||{target_id}",
        target_kind=_text(active_target.get("target_kind")) or "plan",
        target_ref=target_id,
        target_revision=_text(active_target.get("expected_revision")),
        plan_target_ref=target_id,
        dispatch_kind="plan_target",
        guard_bundle=guard_bundle or _text(routing.get("post_push_bundle")),
        preflight_command=preflight_command or _text(routing.get("preflight_command")),
        path_scope=_string_tuple(ownership.get("scope_paths")),
        evidence_refs=(_text(active_target.get("plan_path")), target_id),
        source_contracts=("WorkIntakePacket", "PlanTargetRef"),
    )


def _session_nodes(
    review_state: Mapping[str, object],
) -> tuple[AgentDispatchSessionNode, ...]:
    participants = _participant_rows(review_state)
    nodes: list[AgentDispatchSessionNode] = []
    seen: set[str] = set()
    for row in _work_board_rows(review_state):
        actor = _text(row.get("actor_id"))
        role = _normalize_route_role(row.get("role"))
        session = _text(row.get("session_id"))
        subagent = _text(row.get("subagent_id"))
        if not actor:
            continue
        participant = _participant_for_row(participants, row)
        path_scope = _string_tuple(row.get("path_scope"))
        source_surface = _text(row.get("source_surface"))
        workspace_root = _text(participant.get("workspace_root")) if participant else ""
        node_id = _node_id(
            actor=actor,
            role=role,
            session=session,
            subagent=subagent,
        )
        if node_id in seen:
            continue
        seen.add(node_id)
        freshness = _freshness_state(row)
        row_worktree = _text(row.get("worktree_identity"))
        participant_worktree = _text(participant.get("worktree")) if participant else ""
        row_branch = _text(row.get("branch"))
        participant_branch = _text(participant.get("branch")) if participant else ""
        nodes.append(
            AgentDispatchSessionNode(
                node_id=node_id,
                actor_id=actor,
                provider=_text(row.get("provider")) or actor,
                actor_role=role,
                declared_role=_normalize_route_role(row.get("declared_role")),
                authority_role=_normalize_route_role(row.get("authority_role")),
                role_source=_text(row.get("role_source")),
                role_scope=_text(row.get("role_scope")),
                session_id=session,
                subagent_id=subagent,
                lane_id=_text(row.get("lane_id")),
                instance_num=_int(row.get("instance_num")),
                worktree_identity=row_worktree or participant_worktree,
                branch=row_branch or participant_branch,
                workspace_root=workspace_root or (path_scope[0] if path_scope else ""),
                path_scope=path_scope,
                status=_text(row.get("status")),
                live=freshness == "fresh",
                freshness_state=freshness,
                last_active_utc=_text(row.get("last_active_utc")),
                idle_seconds=_int(row.get("idle_seconds")),
                stale_after_seconds=_int(row.get("stale_after_seconds")),
                confidence_class=_text(row.get("confidence_class")),
                source_event_id=_text(row.get("source_event_id")),
                source_surface=source_surface,
                current_command=_text(row.get("current_command")),
                current_check=_text(row.get("current_check")),
                current_file_or_module=_text(row.get("current_file_or_module")),
                active_packet_id=_text(row.get("active_packet_id")),
                attention_packet_id=_text(row.get("attention_packet_id")),
                executing_packet_id=_text(row.get("executing_packet_id")),
                plan_row_id=_text(row.get("plan_row_id")),
                parent_agent_id=_text(row.get("parent_agent_id")),
                conductor_id=_text(row.get("conductor_id")),
                integrator_id=_text(row.get("integrator_id")),
                mutation_mode=_text(row.get("mutation_mode")),
                granted_capabilities=_string_tuple(row.get("granted_capabilities")),
                work_scope_lease_id=_text(row.get("work_scope_lease_id")),
                barrier_ids=_string_tuple(row.get("barrier_ids")),
                metadata_path=_text(participant.get("metadata_path")) if participant else "",
                log_path=_text(participant.get("log_path")) if participant else "",
                communication_endpoint_ref=source_surface,
            )
        )
    return tuple(nodes)


def _work_focus(
    *,
    review_state: Mapping[str, object],
    session_nodes: tuple[AgentDispatchSessionNode, ...],
) -> tuple[AgentDispatchWorkFocus, ...]:
    decisions = _decision_rows(review_state)
    packets = _packet_rows(review_state)
    rows: list[AgentDispatchWorkFocus] = []
    for node in session_nodes:
        decision = _matching_decision(
            decisions,
            actor=node.actor_id,
            role=node.actor_role,
            session=node.session_id,
        )
        current_packet_id = (
            _text(decision.get("executing_packet_id"))
            or _text(decision.get("attention_packet_id"))
            or _text(decision.get("active_packet_id"))
            or node.executing_packet_id
            or node.attention_packet_id
            or node.active_packet_id
        )
        packet = _packet_by_id(packets, current_packet_id)
        target_kind = _text(packet.get("target_kind")) or _text(
            decision.get("target_kind")
        )
        target_ref = _text(packet.get("target_ref")) or _text(decision.get("target_ref"))
        plan_target = _text(decision.get("plan_target_ref")) or _plan_ref_for_packet(
            packet
        )
        rows.append(
            AgentDispatchWorkFocus(
                focus_id=f"focus:{node.node_id}",
                session_node_id=node.node_id,
                actor_id=node.actor_id,
                actor_role=node.actor_role,
                session_id=node.session_id,
                current_packet_id=current_packet_id,
                attention_packet_id=_text(decision.get("attention_packet_id"))
                or node.attention_packet_id,
                executing_packet_id=_text(decision.get("executing_packet_id"))
                or node.executing_packet_id,
                plan_target_ref=plan_target or node.plan_row_id,
                target_kind=target_kind,
                target_ref=target_ref,
                target_revision=_text(packet.get("target_revision")),
                current_instruction_revision=_text(
                    decision.get("current_instruction_revision")
                ),
                lifecycle_state=_text(decision.get("lifecycle_state"))
                or _text(packet.get("lifecycle_current_state"))
                or _text(packet.get("status")),
                latest_event_id=_text(packet.get("latest_event_id"))
                or _text(decision.get("source_latest_event_id")),
                requested_action=_text(packet.get("requested_action")),
                policy_hint=_text(packet.get("policy_hint")),
                source_contracts=(
                    "AgentDispatchSessionNode",
                    "AgentLoopDecision",
                    "ReviewPacketState",
                ),
            )
        )
    return tuple(rows)


def _peer_links(
    *,
    review_state: Mapping[str, object],
    session_nodes: tuple[AgentDispatchSessionNode, ...],
    work_focus: tuple[AgentDispatchWorkFocus, ...],
) -> tuple[AgentDispatchPeerLink, ...]:
    links: list[AgentDispatchPeerLink] = []
    seen: set[str] = set()
    nodes_by_id = {node.node_id: node for node in session_nodes}
    for focus in work_focus:
        packet = _packet_by_id(_packet_rows(review_state), focus.current_packet_id)
        if not packet:
            continue
        for node in _nodes_for_packet(session_nodes, packet):
            link = AgentDispatchPeerLink(
                link_id=f"link:packet:{focus.current_packet_id}:{node.node_id}",
                from_node_id=_unique_actor_node_id(
                    session_nodes,
                    actor=_text(packet.get("from_agent")),
                ),
                to_node_id=node.node_id,
                link_kind="packet_addressed_to",
                packet_id=focus.current_packet_id,
                plan_target_ref=focus.plan_target_ref,
                freshness_state=node.freshness_state,
                evidence_refs=(
                    _text(packet.get("latest_event_id")),
                    node.source_event_id,
                ),
            )
            _append_link(links, seen, link)

    live_nodes = [node for node in session_nodes if node.live]
    for index, left in enumerate(live_nodes):
        if not left.worktree_identity:
            continue
        for right in live_nodes[index + 1:]:
            if right.worktree_identity != left.worktree_identity:
                continue
            if left.branch and right.branch and left.branch != right.branch:
                continue
            link = AgentDispatchPeerLink(
                link_id=f"link:same_worktree:{left.node_id}:{right.node_id}",
                from_node_id=left.node_id,
                to_node_id=right.node_id,
                link_kind="same_worktree_peer",
                freshness_state="fresh",
                evidence_refs=(left.source_event_id, right.source_event_id),
            )
            _append_link(links, seen, link)

    for node in live_nodes:
        if node.actor_role != "subagent" or not node.parent_agent_id:
            continue
        parent_id = _unique_actor_node_id(
            session_nodes,
            actor=node.parent_agent_id,
            session=node.session_id,
        )
        if not parent_id or parent_id not in nodes_by_id:
            continue
        link = AgentDispatchPeerLink(
            link_id=f"link:subagent:{node.node_id}:{parent_id}",
            from_node_id=node.node_id,
            to_node_id=parent_id,
            link_kind="subagent_of",
            freshness_state=node.freshness_state,
            evidence_refs=(node.source_event_id, nodes_by_id[parent_id].source_event_id),
        )
        _append_link(links, seen, link)
    return tuple(links)


def _ambiguous_session_groups(
    *,
    routes: tuple[AgentDispatchRoute, ...],
    rejections: tuple[AgentDispatchRejection, ...],
    session_nodes: tuple[AgentDispatchSessionNode, ...],
) -> tuple[AgentDispatchAmbiguousGroup, ...]:
    groups: dict[str, AgentDispatchAmbiguousGroup] = {}
    for rejection in rejections:
        if rejection.reason == "multiple_sessions_claim_same_packet":
            node_ids = _node_ids_for_sessions(
                session_nodes,
                actor=rejection.actor_id,
                role=rejection.actor_role,
                sessions=rejection.evidence_refs,
            )
            group_id = f"group:packet:{rejection.actor_id}:{rejection.packet_id}"
            groups[group_id] = AgentDispatchAmbiguousGroup(
                group_id=group_id,
                group_kind="packet_claim",
                actor_id=rejection.actor_id,
                actor_role=rejection.actor_role,
                packet_id=rejection.packet_id,
                session_node_ids=node_ids,
                reason=rejection.reason,
                evidence_refs=rejection.evidence_refs,
            )
        elif rejection.reason == "actor_session_unresolved":
            route = _route_by_id(routes, rejection.route_id)
            node_ids = _node_ids_for_sessions(
                session_nodes,
                actor=rejection.actor_id,
                role=rejection.actor_role,
                sessions=rejection.evidence_refs,
            )
            group_id = f"group:actor:{rejection.actor_id}:{rejection.packet_id}"
            groups[group_id] = AgentDispatchAmbiguousGroup(
                group_id=group_id,
                group_kind="actor_session",
                actor_id=rejection.actor_id,
                actor_role=rejection.actor_role,
                packet_id=rejection.packet_id,
                plan_target_ref=route.plan_target_ref if route else "",
                session_node_ids=node_ids,
                reason=rejection.reason,
                evidence_refs=rejection.evidence_refs,
            )
    return tuple(groups[key] for key in sorted(groups))


def _governance_debt(
    *,
    review_state: Mapping[str, object],
    session_nodes: tuple[AgentDispatchSessionNode, ...],
    work_focus: tuple[AgentDispatchWorkFocus, ...],
    routes: tuple[AgentDispatchRoute, ...],
    ambiguous_groups: tuple[AgentDispatchAmbiguousGroup, ...],
) -> tuple[AgentDispatchGovernanceDebt, ...]:
    debts: list[AgentDispatchGovernanceDebt] = []
    packets = _packet_rows(review_state)
    focus_by_node = {focus.session_node_id: focus for focus in work_focus}
    for node in session_nodes:
        if node.freshness_state != "fresh":
            continue
        focus = focus_by_node.get(node.node_id)
        plan_ref = focus.plan_target_ref if focus else node.plan_row_id
        packet_id = focus.current_packet_id if focus else ""
        if node.role_scope == "actor_ambiguous" and node.authority_role == "implementer":
            debts.append(
                AgentDispatchGovernanceDebt(
                    debt_id=f"debt:session_authority_binding:{node.node_id}",
                    debt_kind="session_bound_mutation_authority_required",
                    session_node_id=node.node_id,
                    actor_id=node.actor_id,
                    actor_role=node.actor_role,
                    session_id=node.session_id,
                    packet_id=packet_id,
                    plan_target_ref=plan_ref,
                    reason="actor_scoped_mutation_authority_cannot_select_session",
                    required_remediation=(
                        "bind repo mutation authority to an explicit session, "
                        "WorkerPacket, WorkScopeLease, or isolated worktree before "
                        "dispatching executable work"
                    ),
                    evidence_refs=(
                        node.source_event_id,
                        node.source_surface,
                        node.authority_role,
                        node.role_source,
                    ),
                )
            )
        if plan_ref:
            continue
        debts.append(
            AgentDispatchGovernanceDebt(
                debt_id=f"debt:session_plan_binding:{node.node_id}",
                debt_kind="session_without_plan_binding",
                session_node_id=node.node_id,
                actor_id=node.actor_id,
                actor_role=node.actor_role,
                session_id=node.session_id,
                packet_id=packet_id,
                reason="fresh_session_has_no_plan_target_or_packet_plan_binding",
                required_remediation=(
                    "bind session startup to WorkIntakePacket/PlanRow or "
                    "scope its active packet to a plan target"
                ),
                evidence_refs=(node.source_event_id, node.source_surface),
            )
        )

    for group in ambiguous_groups:
        packet = _packet_by_id(packets, group.packet_id)
        plan_ref = _plan_ref_for_packet(packet)
        debts.append(
            AgentDispatchGovernanceDebt(
                debt_id=f"debt:session_scope:{group.group_id}",
                debt_kind="packet_without_unique_session_scope",
                severity="critical",
                actor_id=group.actor_id,
                actor_role=group.actor_role,
                packet_id=group.packet_id,
                plan_target_ref=plan_ref,
                reason=group.reason,
                required_remediation=(
                    "repost or transition the work through a typed packet with "
                    "target_role plus target_session_id, or acquire a "
                    "WorkScopeLease for exactly one session"
                ),
                evidence_refs=group.evidence_refs,
            )
        )

    for route in routes:
        if route.plan_target_ref:
            continue
        debts.append(
            AgentDispatchGovernanceDebt(
                debt_id=f"debt:route_plan_binding:{route.route_id}",
                debt_kind="route_without_plan_binding",
                route_id=route.route_id,
                session_node_id=route.session_node_id,
                actor_id=route.actor_id,
                actor_role=route.actor_role,
                session_id=route.session_id,
                packet_id=route.packet_id,
                reason="dispatch_route_has_no_plan_target_ref",
                required_remediation=(
                    "ingest packet/chat intent into MasterPlan/PlanRow before "
                    "dispatching executable work"
                ),
                evidence_refs=route.evidence_refs,
            )
        )

    debts.extend(_write_scope_collision_debts(session_nodes, focus_by_node))
    return tuple(_dedupe_debt(debts))


def _write_scope_collision_debts(
    session_nodes: tuple[AgentDispatchSessionNode, ...],
    focus_by_node: Mapping[str, AgentDispatchWorkFocus],
) -> list[AgentDispatchGovernanceDebt]:
    writable_nodes = [
        node
        for node in session_nodes
        if node.freshness_state == "fresh"
        and node.mutation_mode in {"live_tree", "isolated_worktree"}
    ]
    debts: list[AgentDispatchGovernanceDebt] = []
    for index, left in enumerate(writable_nodes):
        for right in writable_nodes[index + 1:]:
            overlap_basis = _write_scope_overlap_basis(left, right)
            if not overlap_basis:
                continue
            left_plan = _node_plan_ref(left, focus_by_node)
            right_plan = _node_plan_ref(right, focus_by_node)
            if _write_scope_overlap_allowed(
                left=left,
                right=right,
                left_plan=left_plan,
                right_plan=right_plan,
            ):
                continue
            debts.append(
                AgentDispatchGovernanceDebt(
                    debt_id=(
                        "debt:write_scope_collision:"
                        f"{left.node_id}:{right.node_id}"
                    ),
                    debt_kind="overlapping_write_scope_without_lease_or_plan",
                    severity="critical",
                    session_node_id=left.node_id,
                    actor_id=left.actor_id,
                    actor_role=left.actor_role,
                    session_id=left.session_id,
                    plan_target_ref=left_plan or right_plan,
                    reason=(
                        "fresh_live_sessions_overlap_write_scope_without_"
                        "work_scope_lease_or_plan_binding"
                    ),
                    required_remediation=(
                        "route one session away from the overlapping file/path "
                        "or bind both sessions to an explicit WorkScopeLease/"
                        "shared PlanRow before either mutates"
                    ),
                    evidence_refs=(
                        left.node_id,
                        right.node_id,
                        overlap_basis,
                        left.source_event_id,
                        right.source_event_id,
                    ),
                )
            )
    return debts


def _write_scope_overlap_allowed(
    *,
    left: AgentDispatchSessionNode,
    right: AgentDispatchSessionNode,
    left_plan: str,
    right_plan: str,
) -> bool:
    if (
        left.work_scope_lease_id
        and right.work_scope_lease_id
        and left.work_scope_lease_id == right.work_scope_lease_id
    ):
        return True
    return bool(left_plan and left_plan == right_plan)


def _node_plan_ref(
    node: AgentDispatchSessionNode,
    focus_by_node: Mapping[str, AgentDispatchWorkFocus],
) -> str:
    focus = focus_by_node.get(node.node_id)
    return (focus.plan_target_ref if focus else "") or node.plan_row_id


def _write_scope_overlap_basis(
    left: AgentDispatchSessionNode,
    right: AgentDispatchSessionNode,
) -> str:
    left_file = _normalize_scope_path(left.current_file_or_module)
    right_file = _normalize_scope_path(right.current_file_or_module)
    if left_file and right_file and _paths_overlap(left_file, right_file):
        return f"current_file:{left_file}<->{right_file}"

    for left_scope in _node_scope_paths(left):
        for right_scope in _node_scope_paths(right):
            if _paths_overlap(left_scope, right_scope):
                return f"path_scope:{left_scope}<->{right_scope}"

    if left.worktree_identity and left.worktree_identity == right.worktree_identity:
        return f"worktree:{left.worktree_identity}"
    return ""


def _node_scope_paths(node: AgentDispatchSessionNode) -> tuple[str, ...]:
    values = [_normalize_scope_path(value) for value in node.path_scope]
    if node.current_file_or_module:
        values.append(_normalize_scope_path(node.current_file_or_module))
    return tuple(value for value in values if value)


def _normalize_scope_path(value: object) -> str:
    text = _text(value).strip()
    if not text:
        return ""
    return text.rstrip("/")


def _paths_overlap(left: str, right: str) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    return left.startswith(f"{right}/") or right.startswith(f"{left}/")


def _scope_rejections(
    *,
    review_state: Mapping[str, object],
    routes: tuple[AgentDispatchRoute, ...],
) -> list[AgentDispatchRejection]:
    rejections: list[AgentDispatchRejection] = []
    packets = _packet_rows(review_state)
    for route in routes:
        if not route.packet_id:
            continue
        packet = _packet_by_id(packets, route.packet_id)
        packet_to_agent = _text(packet.get("to_agent"))
        if (
            packet
            and (not packet_to_agent or packet_to_agent == route.actor_id)
            and _packet_route_matches_scope(
                packet,
                target_role=route.actor_role,
                target_session_id=route.session_id,
            )
        ):
            continue
        rejections.append(
            AgentDispatchRejection(
                route_id=route.route_id,
                actor_id=route.actor_id,
                provider=route.provider,
                actor_role=route.actor_role,
                session_id=route.session_id,
                packet_id=route.packet_id,
                reason="packet_route_scope_mismatch",
                evidence_refs=(route.route_id, route.packet_id),
            )
        )
    return rejections


def _actor_session_rejections(
    *,
    routes: tuple[AgentDispatchRoute, ...],
    session_nodes: tuple[AgentDispatchSessionNode, ...],
) -> list[AgentDispatchRejection]:
    rejections: list[AgentDispatchRejection] = []
    for route in routes:
        if not route.actor_id or route.session_id:
            continue
        sessions = tuple(
            node.session_id
            for node in _fresh_nodes_for_actor(
                session_nodes,
                actor=route.actor_id,
                role=route.actor_role,
            )
        )
        if len(sessions) <= 1:
            continue
        rejections.append(
            AgentDispatchRejection(
                route_id=route.route_id,
                actor_id=route.actor_id,
                provider=route.provider,
                actor_role=route.actor_role,
                session_id=route.session_id,
                packet_id=route.packet_id,
                reason="actor_session_unresolved",
                evidence_refs=sessions,
            )
        )
    return rejections


def _stale_session_rejections(
    *,
    routes: tuple[AgentDispatchRoute, ...],
    session_nodes: tuple[AgentDispatchSessionNode, ...],
) -> list[AgentDispatchRejection]:
    node_by_id = {node.node_id: node for node in session_nodes}
    rejections: list[AgentDispatchRejection] = []
    for route in routes:
        if not route.session_node_id:
            continue
        node = node_by_id.get(route.session_node_id)
        if node is None or node.freshness_state == "fresh":
            continue
        rejections.append(
            AgentDispatchRejection(
                route_id=route.route_id,
                actor_id=route.actor_id,
                provider=route.provider,
                actor_role=route.actor_role,
                session_id=route.session_id,
                packet_id=route.packet_id,
                reason="session_not_fresh",
                evidence_refs=(
                    route.session_node_id,
                    node.freshness_state,
                    node.source_event_id,
                ),
            )
        )
    return rejections


def _capability_rejections(
    *,
    routes: tuple[AgentDispatchRoute, ...],
    session_nodes: tuple[AgentDispatchSessionNode, ...],
) -> list[AgentDispatchRejection]:
    nodes_by_id = {node.node_id: node for node in session_nodes}
    rejections: list[AgentDispatchRejection] = []
    for route in routes:
        if not route.required_capabilities or not route.session_node_id:
            continue
        node = nodes_by_id.get(route.session_node_id)
        if node is None:
            continue
        required = set(route.required_capabilities)
        granted = set(node.granted_capabilities)
        missing = sorted(required - granted)
        if missing:
            rejections.append(
                AgentDispatchRejection(
                    route_id=route.route_id,
                    actor_id=route.actor_id,
                    provider=route.provider,
                    actor_role=route.actor_role,
                    session_id=route.session_id,
                    packet_id=route.packet_id,
                    reason="missing_required_capability",
                    evidence_refs=(
                        route.session_node_id,
                        ",".join(sorted(required)),
                        ",".join(sorted(granted)),
                    ),
                )
            )
            continue
        if required & {"repo.stage", "repo.commit"} and node.mutation_mode not in {
            "live_tree",
            "isolated_worktree",
        }:
            rejections.append(
                AgentDispatchRejection(
                    route_id=route.route_id,
                    actor_id=route.actor_id,
                    provider=route.provider,
                    actor_role=route.actor_role,
                    session_id=route.session_id,
                    packet_id=route.packet_id,
                    reason="mutation_mode_not_writable",
                    evidence_refs=(
                        route.session_node_id,
                        node.mutation_mode or "unknown",
                        ",".join(sorted(required)),
                    ),
                )
            )
    return rejections


def _ambiguity_rejections(
    routes: tuple[AgentDispatchRoute, ...],
) -> tuple[AgentDispatchRejection, ...]:
    grouped: dict[tuple[str, str], list[AgentDispatchRoute]] = {}
    for route in routes:
        if not route.actor_id or not route.packet_id:
            continue
        grouped.setdefault((route.actor_id, route.packet_id), []).append(route)

    rejections: list[AgentDispatchRejection] = []
    for (_actor, _packet), candidates in grouped.items():
        sessions = {route.session_id for route in candidates if route.session_id}
        if len(sessions) <= 1:
            continue
        for route in candidates:
            rejections.append(
                AgentDispatchRejection(
                    route_id=route.route_id,
                    actor_id=route.actor_id,
                    provider=route.provider,
                    actor_role=route.actor_role,
                    session_id=route.session_id,
                    packet_id=route.packet_id,
                    reason="multiple_sessions_claim_same_packet",
                    evidence_refs=tuple(sorted(sessions)),
                )
            )
    return tuple(rejections)


def _select_routes(
    routes: tuple[AgentDispatchRoute, ...],
    rejections: tuple[AgentDispatchRejection, ...],
) -> tuple[tuple[str, ...], str, str]:
    if not routes:
        return (), "no_dispatchable_work", "no_dispatchable_work"
    ambiguity_present = any(
        rejection.reason == "multiple_sessions_claim_same_packet"
        for rejection in rejections
    )
    rejected_route_ids = {rejection.route_id for rejection in rejections}
    valid_routes = tuple(
        route for route in routes if route.route_id not in rejected_route_ids
    )
    if not valid_routes:
        if ambiguity_present:
            return (), "ambiguous_actor_session_route", "ambiguous"
        return (), "no_valid_route_after_rejections", "blocked"

    selected_routes = tuple(
        sorted(
            (
                _ranked_route_group(routes_for_group)[0]
                for routes_for_group in _route_groups(valid_routes).values()
            ),
            key=_route_rank_key,
            reverse=True,
        )
    )
    selected_route_ids = tuple(route.route_id for route in selected_routes)
    if ambiguity_present:
        return (
            selected_route_ids,
            "selected_valid_routes_with_ambiguous_groups",
            "partial",
        )
    if rejections:
        return (
            selected_route_ids,
            "selected_valid_routes_with_rejections",
            "partial",
        )
    return selected_route_ids, "highest_ranked_typed_route_per_work_group", "ready"


def _route_groups(
    routes: tuple[AgentDispatchRoute, ...],
) -> dict[str, tuple[AgentDispatchRoute, ...]]:
    grouped: dict[str, list[AgentDispatchRoute]] = {}
    for route in routes:
        grouped.setdefault(_route_group_key(route), []).append(route)
    return {key: tuple(value) for key, value in grouped.items()}


def _route_group_key(route: AgentDispatchRoute) -> str:
    if route.packet_id:
        return f"packet:{route.actor_id}:{route.packet_id}"
    if route.plan_target_ref:
        return f"plan:{route.plan_target_ref}"
    if route.target_ref:
        return f"target:{route.target_kind}:{route.target_ref}"
    return route.route_id


def _ranked_route_group(
    routes: tuple[AgentDispatchRoute, ...],
) -> tuple[AgentDispatchRoute, ...]:
    return tuple(sorted(routes, key=_route_rank_key, reverse=True))


def _route_rank_key(route: AgentDispatchRoute) -> tuple[int, bool, str]:
    return (
        _best_event_rank(route.evidence_refs),
        route.dispatch_kind == "packet",
        route.route_id,
    )


def _required_capabilities(
    decision: Mapping[str, object],
    packet: Mapping[str, object],
) -> tuple[str, ...]:
    caps = []
    for value in decision.get("granted_capabilities") or ():
        text = _text(value)
        if text:
            caps.append(text)
    requested = _text(packet.get("requested_action"))
    if requested.startswith("stage_") and "repo.stage" not in caps:
        caps.append("repo.stage")
    return tuple(caps)


def _input_refs(
    *,
    review_state: Mapping[str, object],
    work_intake: Mapping[str, object],
) -> dict[str, str]:
    queue = _mapping(review_state.get("queue"))
    source = _mapping(queue.get("derived_next_instruction_source"))
    active_target = _mapping(work_intake.get("active_target"))
    refs: dict[str, str] = {}
    for key, value in (
        ("packet_id", source.get("packet_id")),
        ("plan_target_ref", active_target.get("target_id") or source.get("target_ref")),
        (
            "current_instruction_revision",
            _mapping(review_state.get("current_session")).get(
                "current_instruction_revision"
            ),
        ),
        ("work_intake_goal", work_intake.get("goal")),
    ):
        text = _text(value)
        if text:
            refs[key] = text
    return refs


def _repo_id(
    project_governance: Mapping[str, object],
    review_state: Mapping[str, object],
) -> str:
    repo = _mapping(project_governance.get("repo"))
    return (
        _text(repo.get("repo_id"))
        or _text(repo.get("slug"))
        or _text(_mapping(review_state.get("source_identity")).get("repo_id"))
    )


def _source_identity(review_state: Mapping[str, object]) -> dict[str, str]:
    source = _mapping(review_state.get("source_identity"))
    return {str(key): _text(value) for key, value in source.items() if _text(value)}


def _guard_bundle(guard_dispatch: Mapping[str, object]) -> str:
    return _text(guard_dispatch.get("recommended_bundle")) or _text(
        guard_dispatch.get("bundle_name")
    )


def _preflight_command(guard_dispatch: Mapping[str, object]) -> str:
    command = _text(guard_dispatch.get("preflight_command"))
    if command:
        return command
    commands = guard_dispatch.get("preflight_commands")
    if isinstance(commands, Sequence) and not isinstance(commands, (str, bytes)):
        return " && ".join(_text(item) for item in commands if _text(item))
    return ""


def _packet_rows(review_state: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows = review_state.get("packets")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _work_board_rows(
    review_state: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows = _mapping(review_state.get("agent_work_board")).get("rows")
    if not rows:
        rows = _mapping(review_state.get("work_board")).get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _decision_rows(review_state: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows = review_state.get("agent_loop_decisions")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _matching_work_row(
    rows: tuple[Mapping[str, object], ...],
    *,
    actor: object,
    role: object,
    session: object,
) -> Mapping[str, object]:
    actor_id = _text(actor)
    role_id = _normalize_route_role(role)
    session_id = _text(session)
    matches: list[Mapping[str, object]] = []
    for row in rows:
        if _text(row.get("actor_id")) != actor_id:
            continue
        if role_id and _normalize_route_role(row.get("role")) != role_id:
            continue
        if session_id and _text(row.get("session_id")) != session_id:
            continue
        matches.append(row)
    if len(matches) == 1:
        return matches[0]
    return {}


def _matching_decision(
    rows: tuple[Mapping[str, object], ...],
    *,
    actor: object,
    role: object,
    session: object,
) -> Mapping[str, object]:
    actor_id = _text(actor)
    role_id = _normalize_route_role(role)
    session_id = _text(session)
    for row in rows:
        if _text(row.get("actor_id")) != actor_id:
            continue
        if role_id and _normalize_route_role(row.get("actor_role")) != role_id:
            continue
        if session_id and _text(row.get("session_id")) != session_id:
            continue
        return row
    return {}


def _matching_sessions(
    rows: tuple[Mapping[str, object], ...],
    *,
    actor: object,
    role: object,
) -> tuple[str, ...]:
    actor_id = _text(actor)
    role_id = _normalize_route_role(role)
    sessions = {
        _text(row.get("session_id"))
        for row in rows
        if _text(row.get("actor_id")) == actor_id
        and (not role_id or _normalize_route_role(row.get("role")) == role_id)
        and _text(row.get("session_id"))
    }
    return tuple(sorted(sessions))


def _session_node_id_for(
    nodes: tuple[AgentDispatchSessionNode, ...],
    *,
    actor: object,
    role: object,
    session: object,
) -> str:
    actor_id = _text(actor)
    role_id = _normalize_route_role(role)
    session_id = _text(session)
    if not actor_id or not session_id:
        return ""
    matches = [
        node.node_id
        for node in nodes
        if node.actor_id == actor_id
        and node.session_id == session_id
        and (not role_id or node.actor_role == role_id)
    ]
    return matches[0] if len(matches) == 1 else ""


def _node_id(
    *,
    actor: object,
    role: object,
    session: object,
    subagent: object = "",
) -> str:
    actor_id = _text(actor)
    role_id = _normalize_route_role(role)
    session_id = _text(session) or "aggregate"
    subagent_id = _text(subagent)
    suffix = f":{subagent_id}" if subagent_id else ""
    return f"node:{actor_id}:{role_id}:{session_id}{suffix}"


def _unique_actor_node_id(
    nodes: tuple[AgentDispatchSessionNode, ...],
    *,
    actor: object,
    session: object = "",
) -> str:
    actor_id = _text(actor)
    session_id = _text(session)
    if not actor_id:
        return ""
    matches = [
        node.node_id
        for node in nodes
        if node.actor_id == actor_id
        and (not session_id or node.session_id == session_id)
        and node.live
    ]
    return matches[0] if len(matches) == 1 else ""


def _fresh_nodes_for_actor(
    nodes: tuple[AgentDispatchSessionNode, ...],
    *,
    actor: object,
    role: object,
) -> tuple[AgentDispatchSessionNode, ...]:
    actor_id = _text(actor)
    role_id = _normalize_route_role(role)
    if not actor_id:
        return ()
    return tuple(
        node
        for node in nodes
        if node.actor_id == actor_id
        and node.freshness_state == "fresh"
        and (not role_id or node.actor_role == role_id)
    )


def _nodes_for_packet(
    nodes: tuple[AgentDispatchSessionNode, ...],
    packet: Mapping[str, object],
) -> tuple[AgentDispatchSessionNode, ...]:
    to_agent = _text(packet.get("to_agent"))
    if not to_agent:
        return ()
    matches = [
        node
        for node in nodes
        if node.actor_id == to_agent
        and _packet_route_matches_scope(
            packet,
            target_role=node.actor_role,
            target_session_id=node.session_id,
        )
    ]
    return tuple(matches)


def _node_ids_for_sessions(
    nodes: tuple[AgentDispatchSessionNode, ...],
    *,
    actor: object,
    role: object,
    sessions: tuple[str, ...],
) -> tuple[str, ...]:
    actor_id = _text(actor)
    role_id = _normalize_route_role(role)
    wanted = {_text(session) for session in sessions if _text(session)}
    node_ids = [
        node.node_id
        for node in nodes
        if node.actor_id == actor_id
        and node.session_id in wanted
        and (not role_id or node.actor_role == role_id)
    ]
    return tuple(sorted(node_ids))


def _route_by_id(
    routes: tuple[AgentDispatchRoute, ...],
    route_id: str,
) -> AgentDispatchRoute | None:
    for route in routes:
        if route.route_id == route_id:
            return route
    return None


def _dedupe_debt(
    debts: list[AgentDispatchGovernanceDebt],
) -> tuple[AgentDispatchGovernanceDebt, ...]:
    seen: set[str] = set()
    rows: list[AgentDispatchGovernanceDebt] = []
    for debt in debts:
        if debt.debt_id in seen:
            continue
        seen.add(debt.debt_id)
        rows.append(debt)
    return tuple(rows)


def _append_link(
    links: list[AgentDispatchPeerLink],
    seen: set[str],
    link: AgentDispatchPeerLink,
) -> None:
    if link.link_id in seen:
        return
    seen.add(link.link_id)
    links.append(link)


def _participant_rows(
    review_state: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows = _mapping(review_state.get("collaboration")).get("participants")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _participant_for_row(
    participants: tuple[Mapping[str, object], ...],
    row: Mapping[str, object],
) -> Mapping[str, object]:
    actor = _text(row.get("actor_id"))
    role = _normalize_route_role(row.get("role"))
    worktree = _text(row.get("worktree_identity"))
    branch = _text(row.get("branch"))
    matches: list[Mapping[str, object]] = []
    for participant in participants:
        if _text(participant.get("agent_id")) != actor:
            continue
        if role and _normalize_route_role(participant.get("role")) != role:
            continue
        participant_worktree = _text(participant.get("worktree"))
        participant_branch = _text(participant.get("branch"))
        if worktree and participant_worktree and participant_worktree != worktree:
            continue
        if branch and participant_branch and participant_branch != branch:
            continue
        matches.append(participant)
    return matches[0] if len(matches) == 1 else {}


def _freshness_state(row: Mapping[str, object]) -> str:
    confidence = _text(row.get("confidence_class"))
    status = _text(row.get("status"))
    idle_seconds = _int(row.get("idle_seconds"))
    stale_after = _int(row.get("stale_after_seconds"))
    if confidence == "stale" or (stale_after > 0 and idle_seconds > stale_after):
        return "stale"
    if status in {"working", "polling", "blocked", "checkpointed"}:
        return "fresh"
    if status == "idle":
        return "idle"
    return "unknown"


def _packet_by_id(
    packet_rows: tuple[Mapping[str, object], ...],
    packet_id: str,
) -> Mapping[str, object]:
    for row in packet_rows:
        if _text(row.get("packet_id")) == packet_id:
            return row
    return {}


def _plan_ref_for_packet(packet: Mapping[str, object]) -> str:
    target_kind = _text(packet.get("target_kind"))
    target_ref = _text(packet.get("target_ref"))
    if target_kind == "plan" and target_ref:
        return target_ref
    plan_id = _text(packet.get("plan_id"))
    if plan_id:
        return plan_id
    intake_ref = _text(packet.get("intake_ref"))
    if intake_ref:
        return intake_ref
    anchor_refs = packet.get("anchor_refs")
    if isinstance(anchor_refs, Sequence) and not isinstance(anchor_refs, (str, bytes)):
        for anchor in anchor_refs:
            text = _text(anchor)
            if text:
                return text
    return target_ref if target_kind in {"policy", "runtime", "code"} else ""


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(_text(item) for item in value if _text(item))


def _int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = _text(value)
    if not text:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def _best_event_rank(values: tuple[str, ...]) -> int:
    return max((_event_id_rank(value) for value in values if value), default=-1)


def _event_id_rank(value: str) -> int:
    match = _EVENT_ID_RE.search(value)
    if not match:
        return -1
    return int(match.group(1))


def _normalize_route_role(value: object) -> str:
    role = _text(value)
    if not role:
        return ""
    key = role.lower().replace("-", "_").replace(" ", "_")
    return _ROLE_ALIASES.get(key, key)


def _packet_route_matches_scope(
    packet: Mapping[str, object],
    *,
    target_role: object = "",
    target_session_id: object = "",
) -> bool:
    packet_role = _normalize_route_role(packet.get("target_role"))
    scope_role = _normalize_route_role(target_role)
    if packet_role and packet_role != scope_role:
        return False

    packet_session = _text(packet.get("target_session_id"))
    scope_session = _text(target_session_id)
    if packet_session and packet_session != scope_session:
        return False

    return True


__all__ = [
    "AgentDispatchAmbiguousGroup",
    "AgentDispatchPeerLink",
    "AgentDispatchRejection",
    "AgentDispatchRoute",
    "AgentDispatchRouter",
    "AgentDispatchSessionNode",
    "AgentDispatchWorkFocus",
    "build_agent_dispatch_router",
]
