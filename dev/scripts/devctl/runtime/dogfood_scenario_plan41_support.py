"""Support helpers for the Plan 4.1 dogfood scenario reducer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .dogfood_models import DogfoodReport
from .dogfood_scenario_models import DogfoodScenarioGate, DogfoodScenarioLane
from .dogfood_scenario_plan41_extract import list_value, mapping, text


def startup_gate(control_plane: Mapping[str, Any]) -> DogfoodScenarioGate:
    next_action = text(control_plane.get("next_action"))
    top_blocker = text(control_plane.get("top_blocker"))
    attention = text(control_plane.get("attention_status"))
    blocked = (
        "checkpoint" in next_action
        or "checkpoint" in top_blocker
        or attention == "checkpoint_required"
    )
    if blocked:
        return DogfoodScenarioGate(
            gate_id="startup_authority",
            status="blocked",
            blocking=True,
            summary=top_blocker or next_action or "checkpoint required",
            evidence_refs=(next_action, top_blocker, attention),
        )
    return DogfoodScenarioGate(
        gate_id="startup_authority",
        status="ready",
        blocking=False,
        summary="startup authority does not block this scenario",
        evidence_refs=(next_action, top_blocker, attention),
    )


def router_gate(router: Mapping[str, Any]) -> DogfoodScenarioGate:
    state = text(router.get("router_state"))
    selected = text(router.get("selected_route_id"))
    debt_count = len(list_value(router.get("governance_debt")))
    if not state:
        return DogfoodScenarioGate(
            gate_id="ai_router",
            status="missing",
            blocking=True,
            summary="AgentDispatchRouter is not projected into the live review state",
        )
    if state in {"ambiguous", "blocked"} or debt_count:
        return DogfoodScenarioGate(
            gate_id="ai_router",
            status=state,
            blocking=True,
            summary=(
                f"router_state={state}; governance_debt={debt_count}; "
                f"selected_route_id={selected}"
            ),
            evidence_refs=(selected,),
        )
    return DogfoodScenarioGate(
        gate_id="ai_router",
        status=state or "ready",
        blocking=False,
        summary=f"router can select typed work; selected_route_id={selected}",
        evidence_refs=(selected,),
    )


def packet_gate(pending_packets: int) -> DogfoodScenarioGate:
    if pending_packets:
        return DogfoodScenarioGate(
            gate_id="packet_queue",
            status="attention_required",
            blocking=False,
            summary=(
                f"{pending_packets} pending packet(s) should drive the next "
                "tandem cycle before new work is invented"
            ),
            evidence_refs=(str(pending_packets),),
        )
    return DogfoodScenarioGate(
        gate_id="packet_queue",
        status="clear",
        blocking=False,
        summary="no pending packets are visible to the scenario reducer",
    )


def tester_cadence_gate(dashboard: Mapping[str, Any]) -> DogfoodScenarioGate:
    minds = mapping(dashboard.get("agent_minds"))
    codex = mapping(minds.get("codex"))
    claude = mapping(minds.get("claude"))
    missing = [
        provider
        for provider, row in (("codex", codex), ("claude", claude))
        if not bool(row.get("available"))
    ]
    if missing:
        return DogfoodScenarioGate(
            gate_id="tester_cadence",
            status="degraded",
            blocking=False,
            summary="missing agent-mind projection for " + ", ".join(missing),
            evidence_refs=tuple(missing),
        )
    return DogfoodScenarioGate(
        gate_id="tester_cadence",
        status="ready",
        blocking=False,
        summary="Codex and Claude tester projections are available",
        evidence_refs=(
            text(codex.get("generated_at_utc")),
            text(claude.get("generated_at_utc")),
        ),
    )


def fanout_gate(
    coordination: Mapping[str, Any],
    fix_mode: str,
) -> DogfoodScenarioGate:
    safe_to_fanout = bool(coordination.get("safe_to_fanout"))
    resync_required = bool(coordination.get("resync_required"))
    fanout_mode = fix_mode in {"isolated-worker", "conflict-drill"}
    blocking = fanout_mode and (not safe_to_fanout or resync_required)
    if blocking:
        return DogfoodScenarioGate(
            gate_id="fanout_readiness",
            status="blocked",
            blocking=True,
            summary=(
                "mutating worker fanout requires safe_to_fanout=true and "
                "resync_required=false"
            ),
            evidence_refs=(str(safe_to_fanout), str(resync_required)),
        )
    status = "ready" if safe_to_fanout else "observe_only"
    return DogfoodScenarioGate(
        gate_id="fanout_readiness",
        status=status,
        blocking=False,
        summary=(
            "worker fanout is not required for this scenario mode"
            if not fanout_mode
            else "typed fanout readiness is green"
        ),
        evidence_refs=(str(safe_to_fanout), str(resync_required)),
    )


def dogfood_backlog_gate(report: DogfoodReport) -> DogfoodScenarioGate:
    open_findings = report.governance_summary.open_findings
    if open_findings:
        return DogfoodScenarioGate(
            gate_id="dogfood_backlog",
            status="active_findings",
            blocking=False,
            summary=(
                f"{open_findings} open dogfood finding(s) are available for "
                "router-driven repair"
            ),
            evidence_refs=(str(open_findings),),
        )
    return DogfoodScenarioGate(
        gate_id="dogfood_backlog",
        status="clear",
        blocking=False,
        summary="no open dogfood governance findings are visible",
    )


def scenario_lanes(
    *,
    dashboard: Mapping[str, Any],
    cadence_seconds: int,
    fix_mode: str,
) -> tuple[DogfoodScenarioLane, ...]:
    posture = mapping(mapping(dashboard.get("control_plane")).get("session_posture"))
    actors = [row for row in list_value(posture.get("actors")) if isinstance(row, Mapping)]
    mutation_owner = _first_actor_with_capability(actors, "repo.commit") or "codex"
    return (
        _lane("ai-router", "router", "coordinator", "system", "report_only", cadence_seconds),
        DogfoodScenarioLane(
            lane_id="claude-tester",
            actor_id="claude",
            role="tester",
            provider="claude",
            mode="observe_and_packet",
            cadence_seconds=cadence_seconds,
            required_actions=("poll codex agent-mind", "inspect typed status", "post scoped findings"),
        ),
        DogfoodScenarioLane(
            lane_id="codex-tester",
            actor_id="codex",
            role="tester",
            provider="codex",
            mode="observe_and_probe",
            cadence_seconds=cadence_seconds,
            required_actions=("run read-only probes", "verify router output", "record dogfood evidence"),
        ),
        DogfoodScenarioLane(
            lane_id="mutation-owner",
            actor_id=mutation_owner,
            role="implementer",
            provider=mutation_owner,
            mode=("single_writer" if fix_mode == "authorized" else fix_mode),
            cadence_seconds=0,
            required_actions=("fix bounded defects only when typed authority allows mutation",),
        ),
    )


def recommended_actions(
    *,
    gates: tuple[DogfoodScenarioGate, ...],
    pending_packets: int,
    router: Mapping[str, Any],
    fix_mode: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    gate_ids = {gate.gate_id for gate in gates}
    if "startup_authority" in gate_ids:
        actions.append("Satisfy startup/checkpoint authority before widening the loop.")
    if "ai_router" in gate_ids:
        actions.append(
            "Repair AgentDispatchRouter projection or route ambiguity before automated dispatch."
        )
    if pending_packets:
        actions.append(
            "Drain the live codex packet queue through review-channel inbox/ack/apply/dismiss."
        )
    if fix_mode in {"isolated-worker", "conflict-drill"}:
        actions.append(
            "Keep worker mutation blocked until SwarmReadinessReport/WorkerPacket and safe_to_fanout are green."
        )
    if text(router.get("router_state")) in {"ready", "partial"}:
        actions.append("Use selected router routes as the next typed assignment source.")
    if not actions:
        actions.append("Run the next tandem packet round and record dogfood evidence.")
    return tuple(actions)


def scenario_state(
    *,
    gates: tuple[DogfoodScenarioGate, ...],
    router_state: str,
    fix_mode: str,
) -> str:
    if gates:
        if any(gate.gate_id == "startup_authority" for gate in gates):
            return "blocked_by_startup_authority"
        if any(gate.gate_id == "ai_router" for gate in gates):
            return "blocked_by_router"
        if any(gate.gate_id == "fanout_readiness" for gate in gates):
            return "blocked_by_fanout"
        return "blocked"
    if fix_mode == "observe":
        return "ready_observe_only"
    return "ready_partial_routes" if router_state == "partial" else "ready"


def dogfood_status_for_state(state: str) -> str:
    return "blocked" if state.startswith("blocked") else "passed"


def scenario_summary(
    *,
    scenario_state: str,
    blocking_gates: tuple[DogfoodScenarioGate, ...],
    pending_packets: int,
    router: Mapping[str, Any],
) -> str:
    if blocking_gates:
        gate_list = ", ".join(gate.gate_id for gate in blocking_gates)
        return f"{scenario_state}; blocking gates: {gate_list}"
    return (
        f"{scenario_state}; pending_packets={pending_packets}; "
        f"router_state={text(router.get('router_state')) or 'missing'}"
    )


def _lane(
    lane_id: str,
    actor_id: str,
    role: str,
    provider: str,
    mode: str,
    cadence_seconds: int,
) -> DogfoodScenarioLane:
    return DogfoodScenarioLane(
        lane_id=lane_id,
        actor_id=actor_id,
        role=role,
        provider=provider,
        mode=mode,
        cadence_seconds=cadence_seconds,
        required_actions=("read typed state", "select next packet/finding", "emit typed route or governance debt"),
    )


def _first_actor_with_capability(
    actors: list[Mapping[str, Any]],
    capability: str,
) -> str:
    for actor in actors:
        if capability in list_value(actor.get("granted_capabilities")):
            return text(actor.get("actor_id"))
    return ""


__all__ = [
    "dogfood_backlog_gate",
    "dogfood_status_for_state",
    "fanout_gate",
    "packet_gate",
    "recommended_actions",
    "router_gate",
    "scenario_lanes",
    "scenario_state",
    "scenario_summary",
    "startup_gate",
    "tester_cadence_gate",
]
