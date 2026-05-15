"""Markdown rendering for ``devctl develop`` reports."""

from __future__ import annotations

from .models import DevelopmentLoopReport
from .render_campaign import campaign_lines
from .render_collaboration import (
    orchestration_lines,
    peer_mind_lines,
    runtime_lines,
)
from ..render_vocabulary import action_label, reason_label


def render_markdown(report: DevelopmentLoopReport) -> str:
    """Render a human-scannable controller report."""
    payload = report.to_dict()
    topology = payload["topology"]
    scaling = topology["scaling"]
    lines = ["# devctl develop", ""]
    lines.extend(_header_lines(payload, topology, scaling))
    lines.extend(_next_slice_lines(payload["next_slice"]))
    lines.extend(_packet_attention_lines(payload["packet_attention"]))
    lines.extend(_design_preflight_lines(payload.get("design_preflight")))
    lines.extend(_lifecycle_lines(payload.get("lifecycle")))
    lines.extend(campaign_lines(payload.get("campaign")))
    lines.extend(runtime_lines(payload.get("runtime")))
    lines.extend(peer_mind_lines(payload.get("peer_minds")))
    lines.extend(orchestration_lines(payload.get("orchestration")))
    lines.extend(_collaboration_mode_lines(payload.get("collaboration_mode")))
    lines.extend(_packet_pressure_lines(payload))
    lines.extend(_watcher_lease_lines(payload.get("watcher_lease")))
    lines.extend(_continuation_lines(payload.get("continuation")))
    lines.extend(_final_response_gate_lines(payload.get("final_response_gate")))
    lines.extend(
        _reviewer_response_shape_lines(payload.get("reviewer_response_shape"))
    )
    lines.extend(_workstream_lines(topology["workstreams"]))
    lines.extend(_scaling_lines(scaling))
    lines.extend(_learning_lines(payload["learning"]))
    lines.extend(_packet_debt_lines(payload.get("packet_debt_remediation")))
    lines.extend(_discovery_lines(payload["discovery"]))
    _append_list(lines, "Blockers", payload["blockers"])
    _append_list(lines, "Warnings", payload["warnings"])
    _append_list(lines, "Required Checks", payload["required_checks"])
    _append_list(lines, "Next Commands", payload["next_commands"])
    lines.extend(_operator_command_wrapper_lines(payload.get("operator_command_wrappers")))
    return "\n".join(lines)


def _header_lines(payload: dict[str, object], topology, scaling) -> list[str]:
    lines = [
        f"- ok: {payload['ok']}",
        f"- action: {payload['action']}",
        f"- status: {payload['status']}",
        f"- controller_state: {payload['controller_state']}",
        f"- summary: {payload['summary']}",
        f"- next_step_command: {payload.get('next_step_command') or '(none)'}",
        f"- topology_id: {topology['topology_id']}",
        f"- default_worker_fanout: {topology['default_worker_fanout']}",
        f"- scaling_modes: {', '.join(scaling['mode_ids'])}",
    ]
    continuation = payload.get("continuation")
    if isinstance(continuation, dict) and continuation.get("continuation_required"):
        lines.insert(5, f"- continuation_state: {continuation.get('user_continue_state') or 'must_continue'}")
        lines.insert(
            6,
            f"- user_action: {action_label(continuation.get('user_action')) or '(none)'}",
        )
        lines.insert(7, f"- continuation_goal: {continuation.get('continuation_goal') or '(none)'}")
        lines.insert(
            8,
            "- next_required_command: "
            f"{continuation.get('next_required_command') or '(none)'}",
        )
    return lines


def _next_slice_lines(next_slice) -> list[str]:
    return [
        "",
        "## Next Slice",
        "",
        f"- slice_id: {next_slice.get('slice_id') or '(none)'}",
        f"- title: {next_slice.get('title') or '(none)'}",
        f"- target_ref: {next_slice.get('target_ref') or '(none)'}",
        f"- status: {next_slice.get('status') or '(none)'}",
        f"- reason: {next_slice.get('reason') or '(none)'}",
    ]


def _packet_attention_lines(attention) -> list[str]:
    attention_reason = (
        attention.get("attention_reason")
        or attention.get("wake_reason")
        or "(none)"
    )
    return [
        "",
        "## Inbox Attention",
        "",
        f"- attention_required: {attention.get('attention_required')}",
        f"- attention_status: {reason_label(attention.get('attention_status'))}",
        f"- attention_reason: {reason_label(attention_reason)}",
        f"- latest_attention_packet_id: {attention.get('latest_attention_packet_id') or '(none)'}",
        f"- latest_finding_packet_id: {attention.get('latest_finding_packet_id') or '(none)'}",
        "- pending_delivery_packet_ids: "
        f"{_list_text(attention.get('pending_delivery_packet_ids'))}",
        "- pending_actionable_packet_ids: "
        f"{_list_text(attention.get('pending_actionable_packet_ids'))}",
        f"- durable_plan_row_id: {attention.get('durable_plan_row_id') or '(none)'}",
        f"- expired_unresolved_count: {attention.get('expired_unresolved_count')}",
        f"- required_command: {attention.get('required_command') or '(none)'}",
        f"- summary: {attention.get('summary') or '(none)'}",
    ]


def _design_preflight_lines(design_preflight) -> list[str]:
    if not isinstance(design_preflight, dict):
        return []
    lines = ["", "## Design Preflight", ""]
    lines.append(f"- topic: {design_preflight.get('topic') or '(none)'}")
    lines.append(
        f"- routing_decision: {design_preflight.get('routing_decision') or '(none)'}"
    )
    lines.append(f"- summary: {design_preflight.get('summary') or '(none)'}")
    lines.append(f"- receipt_verdict: {design_preflight.get('receipt_verdict')}")
    lines.append(f"- receipt_path: {design_preflight.get('receipt_path') or '(none)'}")
    lines.append(
        "- trigger_paths_digest: "
        f"{design_preflight.get('trigger_paths_digest') or '(none)'}"
    )
    lines.append(
        "- observed_probe_ids: "
        f"{_list_text(design_preflight.get('observed_probe_ids'))}"
    )
    lines.append(
        "- trigger_paths: "
        f"{_list_text(design_preflight.get('trigger_paths'))}"
    )
    probes = design_preflight.get("probes")
    if isinstance(probes, list):
        for probe in probes:
            if not isinstance(probe, dict):
                continue
            lines.append(
                f"- {probe.get('probe_id')}: {probe.get('status')} - "
                f"{probe.get('summary')}"
            )
    return lines


def _workstream_lines(workstreams) -> list[str]:
    lines = ["", "## Workstreams", ""]
    for item in workstreams:
        lines.append(
            f"- {item['display_name']} ({item['workstream_id']}): "
            f"{item['mutation_policy']}"
        )
    return lines


def _collaboration_mode_lines(collaboration) -> list[str]:
    if not isinstance(collaboration, dict):
        return []
    policy = collaboration.get("packet_pressure_policy")
    pressure = policy if isinstance(policy, dict) else {}
    selected_mode = collaboration.get("selected_mode")
    mode = selected_mode if isinstance(selected_mode, dict) else {}
    lines = [
        "",
        "## Collaboration Mode",
        "",
        f"- contract_id: {collaboration.get('contract_id') or '(none)'}",
        f"- selected_mode_id: {collaboration.get('selected_mode_id') or '(none)'}",
        f"- selected_role_preset_id: {collaboration.get('selected_role_preset_id') or '(none)'}",
        f"- mutable_fanout_status: {collaboration.get('mutable_fanout_status') or '(none)'}",
        f"- default_worker_fanout: {collaboration.get('default_worker_fanout')}",
        f"- coordination_surfaces: {_list_text(mode.get('coordination_surfaces'))}",
        f"- peer_polling_policy: {mode.get('peer_polling_policy') or '(none)'}",
        f"- role_count_policy: {mode.get('role_count_policy') or '(none)'}",
        f"- stop_anchor_policy: {mode.get('stop_anchor_policy') or '(none)'}",
        f"- stop_anchor_targets: {_list_text(mode.get('stop_anchor_targets'))}",
        f"- stop_anchor_packet_kinds: {_list_text(mode.get('stop_anchor_packet_kinds'))}",
        f"- audit_role: {mode.get('audit_role') or '(none)'}",
        f"- max_audit_agent_count: {mode.get('max_audit_agent_count')}",
        f"- soft_attention_budget: {pressure.get('soft_attention_budget')}",
        f"- hard_attention_budget: {pressure.get('hard_attention_budget')}",
        f"- near_ttl_minutes: {pressure.get('near_ttl_minutes')}",
        f"- authority_policy: {collaboration.get('authority_policy') or '(none)'}",
    ]
    lines.extend(_mode_chain_lines(collaboration.get("mode_chain")))
    lines.extend(_collaboration_profile_lines(collaboration.get("profile")))
    return lines


def _mode_chain_lines(mode_chain) -> list[str]:
    if not isinstance(mode_chain, dict):
        return []
    lines = ["", "## Mode Chain", ""]
    lines.append(f"- contract_id: {mode_chain.get('contract_id') or '(none)'}")
    lines.append(f"- ok: {mode_chain.get('ok')}")
    lines.append(f"- chain_id: {mode_chain.get('chain_id') or '(none)'}")
    lines.append(
        "- effective_reviewer_mode: "
        f"{mode_chain.get('effective_reviewer_mode') or '(none)'}"
    )
    policy = mode_chain.get("policy") if isinstance(mode_chain.get("policy"), dict) else {}
    phase_policy = (
        policy.get("phase_sequence")
        if isinstance(policy.get("phase_sequence"), dict)
        else {}
    )
    lane_policy = (
        policy.get("lane_cardinality")
        if isinstance(policy.get("lane_cardinality"), dict)
        else {}
    )
    receipt_policy = (
        policy.get("composite_receipt")
        if isinstance(policy.get("composite_receipt"), dict)
        else {}
    )
    lines.append(
        "- phase_sequence: "
        f"{phase_policy.get('default_ordering') or '(none)'} "
        f"interleaving={phase_policy.get('interleaving_policy') or '(none)'}"
    )
    lines.append(
        "- lane_cardinality: "
        f"max_chain_phases={lane_policy.get('max_chain_phases')} "
        f"max_live_tree_writers={lane_policy.get('max_live_tree_writers')} "
        f"next_derivers={lane_policy.get('max_independent_next_derivers')}"
    )
    lines.append(
        "- composite_receipt: "
        f"{receipt_policy.get('emit_stage') or '(none)'} "
        f"children={_list_text(receipt_policy.get('required_child_receipt_kinds'))}"
    )
    for phase in _dict_rows(mode_chain.get("phases")):
        lines.append(
            f"- phase {phase.get('order')}: "
            f"{phase.get('role_preset')}:{phase.get('collaboration_mode')} "
            f"kind={phase.get('phase_kind')} "
            f"scope={phase.get('scope_ref') or '(inherited/default)'} "
            f"parent={phase.get('scope_inherited_from') or '(none)'}"
        )
    _append_list(lines, "Mode Chain Errors", mode_chain.get("validation_errors") or [])
    _append_list(
        lines,
        "Mode Chain Warnings",
        mode_chain.get("validation_warnings") or [],
    )
    return lines


def _collaboration_profile_lines(profile) -> list[str]:
    if not isinstance(profile, dict):
        return []
    lines = ["", "## Collaboration Profile", ""]
    lines.append(f"- contract_id: {profile.get('contract_id') or '(none)'}")
    lines.append(f"- profile_id: {profile.get('profile_id') or '(none)'}")
    lines.append(f"- ok: {profile.get('ok')}")
    lines.append(f"- providers: {_list_text(profile.get('providers'))}")
    lines.append(
        "- agent_mind_providers: "
        f"{_list_text(profile.get('agent_mind_providers'))}"
    )
    lines.append(f"- remote_provider: {profile.get('remote_provider') or '(none)'}")
    lines.append(
        "- architecture_agent_count: "
        f"{profile.get('architecture_agent_count')} "
        f"(max {profile.get('max_architecture_agent_count')})"
    )
    lines.append(f"- review_agent_count: {profile.get('review_agent_count')}")
    lines.append(
        f"- source_packet_id: {profile.get('source_packet_id') or '(none)'}"
    )
    lines.append(
        f"- target_packet_id: {profile.get('target_packet_id') or '(none)'}"
    )
    lines.append(
        f"- stop_at_packet_id: {profile.get('stop_at_packet_id') or '(none)'}"
    )
    lines.append(
        f"- stop_at_mp_row_id: {profile.get('stop_at_mp_row_id') or '(none)'}"
    )
    lines.append(f"- source_ref: {profile.get('source_ref') or '(none)'}")
    lines.append(f"- target_ref: {profile.get('target_ref') or '(none)'}")
    lines.append(f"- authority_policy: {profile.get('authority_policy') or '(none)'}")
    session = profile.get("collaboration_session")
    if isinstance(session, dict):
        lines.extend(_collaboration_session_lines(session))
    for wake in _dict_rows(profile.get("advisory_wake_evidence")):
        lines.append(
            "- advisory_attention "
            f"{wake.get('role') or '(role)'}:{wake.get('provider') or '(provider)'} "
            f"arrival={wake.get('arrival_kind') or 'none'} "
            f"packet={wake.get('latest_relevant_packet_id') or '(none)'} "
            f"attention={reason_label(wake.get('attention_status')) or 'none'}"
        )
    stop_anchor = profile.get("stop_anchor_request")
    if isinstance(stop_anchor, dict):
        lines.append(
            f"- stop_anchor_status: {stop_anchor.get('status') or '(none)'}"
        )
        lines.append(
            "- stop_anchor_packet_kinds: "
            f"{stop_anchor.get('continuation_packet_kind')}/"
            f"{stop_anchor.get('stop_packet_kind')}"
        )
        lines.append(
            "- stop_anchor_authority_policy: "
            f"{stop_anchor.get('authority_policy') or '(none)'}"
        )
        for reason in stop_anchor.get("reasons") or []:
            lines.append(f"- stop_anchor_reason: {reason}")
    for binding in _dict_rows(profile.get("role_bindings")):
        session = f":{binding.get('session_id')}" if binding.get("session_id") else ""
        lines.append(
            f"- bind {binding.get('role')}: "
            f"{binding.get('provider')}{session}"
        )
    for request in _dict_rows(profile.get("role_count_requests")):
        lines.append(
            f"- count {request.get('role')}: "
            f"{request.get('requested_count')} source={request.get('source')}"
        )
    for budget in _dict_rows(profile.get("resolved_role_budgets")):
        lines.append(
            f"- budget {budget.get('role')}: "
            f"{budget.get('resolved_count')}/{budget.get('max_count')} "
            f"{budget.get('status')} {budget.get('budget_kind')}"
        )
    _append_list(lines, "Collaboration Profile Errors", profile.get("validation_errors") or [])
    _append_list(
        lines,
        "Collaboration Profile Warnings",
        profile.get("validation_warnings") or [],
    )
    _append_list(lines, "Collaboration Profile Commands", profile.get("command_plan") or [])
    if isinstance(profile.get("template"), dict):
        lines.append("- template: embedded")
    return lines


def _collaboration_session_lines(session: dict[str, object]) -> list[str]:
    owners = session.get("owners") if isinstance(session.get("owners"), dict) else {}
    peer = (
        session.get("peer_review")
        if isinstance(session.get("peer_review"), dict)
        else {}
    )
    arbitration = (
        session.get("arbitration")
        if isinstance(session.get("arbitration"), dict)
        else {}
    )
    lines = [
        "- collaboration_session: "
        f"{session.get('contract_id') or '(none)'} "
        f"session={session.get('session_id') or '(none)'} "
        f"status={session.get('status') or '(none)'} "
        f"topology={session.get('topology_mode') or '(none)'}",
        "- collaboration_session_owner: "
        f"mutation={owners.get('mutation_owner') or '(none)'} "
        f"verification={owners.get('verification_owner') or '(none)'} "
        f"watcher={owners.get('watcher_owner') or '(none)'}",
        "- collaboration_session_peer_review: "
        f"revision={peer.get('current_instruction_revision') or '(none)'} "
        f"ack={peer.get('implementer_ack_state') or '(none)'} "
        f"open_findings={peer.get('open_findings') or '(none)'}",
        "- collaboration_session_arbitration: "
        f"{arbitration.get('status') or '(none)'} "
        f"owner={arbitration.get('owner') or '(none)'}",
    ]
    for authority in _dict_rows(session.get("actor_authorities"))[:8]:
        capabilities = _list_text(authority.get("capabilities"))
        lines.append(
            "- collaboration_session_authority "
            f"{authority.get('actor_id') or '(none)'}: "
            f"{authority.get('role') or '(none)'} "
            f"provider={authority.get('provider') or '(none)'} "
            f"live={authority.get('live')} capabilities={capabilities}"
        )
    for gate in _dict_rows(session.get("ready_gates")):
        lines.append(
            f"- collaboration_session_gate {gate.get('gate_id')}: "
            f"{reason_label(gate.get('status'))} - "
            f"{reason_label(gate.get('summary')) or '(none)'}"
        )
    return lines


def _packet_pressure_lines(payload) -> list[str]:
    pressure = payload.get("packet_pressure")
    decision = payload.get("packet_ingestion_decision")
    if not isinstance(pressure, dict) or not isinstance(decision, dict):
        return []
    classifications = payload.get("selected_packet_classifications")
    selected = classifications if isinstance(classifications, list) else []
    ingest_decisions = payload.get("packet_ingest_decisions")
    per_packet_decisions = ingest_decisions if isinstance(ingest_decisions, list) else []
    lines = ["", "## Packet Pressure", ""]
    lines.append(f"- pressure_state: {reason_label(pressure.get('pressure_state')) or '(none)'}")
    lines.append(f"- live_total: {pressure.get('live_total')}")
    lines.append(f"- actionable_total: {pressure.get('actionable_total')}")
    lines.append(f"- near_ttl_total: {pressure.get('near_ttl_total')}")
    lines.append(f"- expired_unresolved_total: {pressure.get('expired_unresolved_total')}")
    lines.append(f"- carry_forward_total: {pressure.get('carry_forward_total')}")
    lines.append(f"- durable_owner_gap_total: {pressure.get('durable_owner_gap_total')}")
    lines.append(f"- decision: {reason_label(decision.get('decision')) or '(none)'}")
    lines.append(f"- required_action: {action_label(decision.get('required_action')) or '(none)'}")
    lines.append(f"- next_command: {decision.get('next_command') or '(none)'}")
    for item in selected[:10]:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- {item.get('packet_id')}: {reason_label(item.get('classification'))} "
            f"owner={item.get('durable_owner') or '(none)'} "
            f"terminal={item.get('terminal_receipt') or '(none)'}"
        )
    for item in per_packet_decisions[:10]:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- decision {item.get('packet_id')}: {reason_label(item.get('decision'))} "
            f"action={action_label(item.get('required_action')) or '(none)'}"
        )
    return lines


def _lifecycle_lines(lifecycle) -> list[str]:
    if not isinstance(lifecycle, dict):
        return []
    lines = ["", "## Lifecycle", ""]
    lines.append(f"- action: {lifecycle.get('action')}")
    lines.append(f"- actor: {lifecycle.get('actor')}")
    lines.append(f"- slice_id: {lifecycle.get('slice_id') or '(none)'}")
    lines.append(f"- packet_id: {lifecycle.get('packet_id') or '(none)'}")
    lines.append(f"- state: {lifecycle.get('state')}")
    lines.append(f"- summary: {lifecycle.get('summary')}")
    steps = lifecycle.get("steps") if isinstance(lifecycle.get("steps"), list) else []
    for step in steps:
        if not isinstance(step, dict):
            continue
        command = f" | `{step.get('command')}`" if step.get("command") else ""
        lines.append(
            f"- {step.get('step_id')}: {step.get('state')} - "
            f"{step.get('purpose')}{command}"
        )
    return lines


def _scaling_lines(scaling) -> list[str]:
    lines = ["", "## Scaling", ""]
    lines.append(f"- pressure_inputs: {', '.join(scaling['pressure_inputs'])}")
    lines.append(f"- route_outputs: {', '.join(scaling['route_outputs'])}")
    for gate in scaling["safety_gates"]:
        lines.append(f"- safety_gate: {gate}")
    return lines


def _watcher_lease_lines(watcher) -> list[str]:
    if not isinstance(watcher, dict):
        return []
    return [
        "",
        "## Watcher Lease",
        "",
        f"- lease_id: {watcher.get('lease_id') or '(none)'}",
        f"- watcher_id: {watcher.get('watcher_id') or '(none)'}",
        f"- watched_actor: {watcher.get('watched_actor') or '(none)'}",
        f"- watched_surfaces: {_list_text(watcher.get('watched_surfaces'))}",
        f"- status: {watcher.get('status') or '(none)'}",
        f"- last_seen_event_id: {watcher.get('last_seen_event_id') or '(none)'}",
        f"- stale_after_seconds: {watcher.get('stale_after_seconds')}",
        f"- stale_seconds: {watcher.get('stale_seconds')}",
        f"- next_report_command: {watcher.get('next_report_command') or '(none)'}",
        f"- summary: {watcher.get('summary') or '(none)'}",
    ]


def _continuation_lines(continuation) -> list[str]:
    if not isinstance(continuation, dict):
        return []
    return [
        "",
        "## Continuation",
        "",
        f"- continuation_state: {continuation.get('user_continue_state') or '(none)'}",
        f"- user_action: {action_label(continuation.get('user_action')) or '(none)'}",
        f"- continuation_goal: {continuation.get('continuation_goal') or '(none)'}",
        "- continuation_anchor_packet_id: "
        f"{continuation.get('continuation_anchor_packet_id') or '(none)'}",
        f"- goal_progress_packet_id: {continuation.get('goal_progress_packet_id') or '(none)'}",
        "- progress_percentage_toward_goal: "
        f"{continuation.get('progress_percentage_toward_goal')}",
        f"- goal_progress_status: {continuation.get('goal_progress_status') or '(none)'}",
        f"- why_not_done: {reason_label(continuation.get('why_not_done')) or '(none)'}",
        f"- continuation_required: {continuation.get('continuation_required')}",
        f"- status: {continuation.get('status') or '(none)'}",
        f"- final_response_allowed: {continuation.get('final_response_allowed')}",
        "- final_response_gate_allowed: "
        f"{continuation.get('final_response_gate_allowed')}",
        "- required_final_response_action: "
        f"{action_label(continuation.get('required_final_response_action')) or '(none)'}",
        f"- do_not_stop_here: {not bool(continuation.get('final_response_allowed'))}",
        f"- required_packet_kind: {continuation.get('required_packet_kind') or '(none)'}",
        "- required_packet_command: "
        f"{continuation.get('required_packet_command') or '(none)'}",
        f"- reasons: {_list_label_text(continuation.get('reasons'))}",
        f"- next_required_command: {continuation.get('next_required_command') or '(none)'}",
        f"- stop_policy: {continuation.get('stop_policy') or '(none)'}",
        f"- summary: {reason_label(continuation.get('summary')) or '(none)'}",
    ]


def _final_response_gate_lines(gate) -> list[str]:
    if not isinstance(gate, dict):
        return []
    lines = [
        "",
        "## Stop Gate",
        "",
        f"- continuation_state: {gate.get('continuation_state') or ('may_stop' if gate.get('allow_final_response') else 'must_continue')}",
        f"- user_action: {action_label(gate.get('user_action') or gate.get('action')) or '(none)'}",
        f"- continuation_goal: {gate.get('continuation_goal') or gate.get('blocking_packet_id') or '(none)'}",
        f"- why_not_done: {reason_label(gate.get('why_not_done')) or '(none)'}",
        f"- allow_final_response: {gate.get('allow_final_response')}",
        f"- action: {action_label(gate.get('action')) or '(none)'}",
        f"- reason: {reason_label(gate.get('reason')) or '(none)'}",
        f"- source: {gate.get('source') or '(none)'}",
        f"- blocking_packet_id: {gate.get('blocking_packet_id') or '(none)'}",
        f"- next_required_command: {gate.get('next_required_command') or '(none)'}",
        f"- required_packet_kind: {gate.get('required_packet_kind') or '(none)'}",
        "- required_packet_command: "
        f"{gate.get('required_packet_command') or '(none)'}",
        f"- stop_policy: {gate.get('stop_policy') or '(none)'}",
    ]
    gate_failure = gate.get("gate_failure")
    if isinstance(gate_failure, dict) and gate_failure:
        lines.extend(
            [
                "- typed_gate_failure: "
                f"{gate_failure.get('gate_id') or '(none)'}",
                "- violation_reason: "
                f"{reason_label(gate_failure.get('violation_reason')) or '(none)'}",
                "- bypass_invocation: "
                f"{gate_failure.get('bypass_invocation') or '(none)'}",
                "- bypass_receipt_kind: "
                f"{gate_failure.get('bypass_receipt_kind') or '(none)'}",
                "- contract_definition_path: "
                f"{gate_failure.get('contract_definition_path') or '(none)'}",
                "- exception_lifecycle_class: "
                f"{gate_failure.get('exception_lifecycle_class') or '(none)'}",
            ]
        )
    return lines


def _reviewer_response_shape_lines(shape) -> list[str]:
    if not isinstance(shape, dict):
        return []
    return [
        "",
        "## Response Shape",
        "",
        f"- status: {shape.get('status') or '(none)'}",
        f"- response_mode: {shape.get('response_mode') or '(none)'}",
        f"- continuation_state: {shape.get('continuation_state') or '(none)'}",
        f"- status_prose_allowed: {shape.get('status_prose_allowed')}",
        f"- completion_prose_allowed: {shape.get('completion_prose_allowed')}",
        f"- required_next_action: {action_label(shape.get('required_next_action')) or '(none)'}",
        f"- next_required_command: {shape.get('next_required_command') or '(none)'}",
        f"- continuation_goal: {shape.get('continuation_goal') or '(none)'}",
        f"- operator_status_source: {shape.get('operator_status_source') or '(none)'}",
        "- proposed_response_text_observed: "
        f"{shape.get('proposed_response_text_observed')}",
        "- proposed_response_text_source: "
        f"{shape.get('proposed_response_text_source') or '(none)'}",
        f"- allowed_response_kinds: {_list_label_text(shape.get('allowed_response_kinds'))}",
        f"- violations: {_list_label_text(shape.get('violations'))}",
    ]


def _operator_command_wrapper_lines(wrappers) -> list[str]:
    if not isinstance(wrappers, list) or not wrappers:
        return []
    lines = ["", "## Operator Command Wrappers", ""]
    for wrapper in wrappers:
        if not isinstance(wrapper, dict):
            continue
        lines.append(
            "- "
            f"{wrapper.get('wrapper_id') or '(unknown)'}: "
            f"{wrapper.get('source') or '(unknown)'} "
            f"({wrapper.get('command_length')} chars)"
        )
        lines.append("```sh")
        lines.append(str(wrapper.get("wrapped_command") or ""))
        lines.append("```")
    return lines


def _learning_lines(learning) -> list[str]:
    return [
        "",
        "## Learning",
        "",
        f"- open_findings: {learning['open_findings']}",
        f"- promotion_candidates: {learning['promotion_candidates']}",
        f"- queued_promotion_candidates: {learning['queued_promotion_candidates']}",
        f"- smartness_inputs: {', '.join(learning['smartness_inputs'])}",
    ]


def _packet_debt_lines(report) -> list[str]:
    if not isinstance(report, dict):
        return []
    rows = report.get("rows") if isinstance(report.get("rows"), list) else []
    lines = ["", "## Packet Debt Remediation", ""]
    lines.append(f"- debt_count: {report.get('debt_count', 0)}")
    if report.get("total_debt_count") is not None:
        lines.append(f"- total_debt_count: {report.get('total_debt_count', 0)}")
    if report.get("omitted_debt_count") is not None:
        lines.append(f"- omitted_debt_count: {report.get('omitted_debt_count', 0)}")
    lines.append(f"- write_enabled: {report.get('write_enabled', False)}")
    lines.append(f"- action_counts: {_counts_text(report.get('action_counts'))}")
    for row in rows[:10]:
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- {row.get('packet_id')}: {row.get('recommended_action')} "
            f"({row.get('reason')}; target {row.get('target_ref') or '(none)'})"
        )
    return lines


def _discovery_lines(discovery) -> list[str]:
    return [
        "",
        "## Discovery",
        "",
        f"- commands: {discovery['commands']}",
        f"- guards: {discovery['guards']}",
        f"- probes: {discovery['probes']}",
        f"- surfaces: {discovery['surfaces']}",
        f"- coverage_targets: {', '.join(discovery['coverage_targets'])}",
    ]


def _append_list(lines: list[str], title: str, values: list[str]) -> None:
    if not values:
        return
    lines.extend(("", f"## {title}", ""))
    for value in values:
        lines.append(f"- {value}")


def _counts_text(value) -> str:
    if not isinstance(value, dict) or not value:
        return "(none)"
    return ", ".join(f"{key}={count}" for key, count in value.items())


def _list_text(value) -> str:
    if not isinstance(value, list) or not value:
        return "(none)"
    return ", ".join(str(item) for item in value)


def _list_label_text(value) -> str:
    if not isinstance(value, list) or not value:
        return "(none)"
    return ", ".join(reason_label(item) for item in value)


def _dict_rows(value) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


__all__ = ["render_markdown"]
