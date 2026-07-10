"""Read-only Claude loop surface backed by DashboardSnapshot v3."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...review_channel.agent_packet_attention import packet_attention_for_agent
from ...runtime.instruction_authority import (
    DEFAULT_INSTRUCTION_TRANSITIONS_REL,
    instruction_transition_receipt_from_mapping,
)
from ...runtime.dashboard_snapshot_authority import build_dashboard_snapshot
from ...runtime.agent_loop_decision import build_agent_loop_decision
from ...runtime.agent_dispatch_router_models import (
    AgentDispatchAmbiguousGroup,
    AgentDispatchGovernanceDebt,
    AgentDispatchPeerLink,
    AgentDispatchRejection,
    AgentDispatchRoute,
    AgentDispatchRouter,
    AgentDispatchSessionNode,
    AgentDispatchWorkFocus,
)
from ...runtime.agent_loop_decision_sources import AgentLoopContext
from ...runtime.agent_loop_operator_override import AgentLoopOperatorOverride
from ...runtime.reviewer_runtime_models import InboxObservationState, WakeEvidence
from ...runtime.value_coercion import coerce_mapping
from .claude_loop_follow import run_follow
from .claude_loop_packets import scoped_packets
from .claude_loop_proof import (
    build_loop_proof_evidence,
    compact_master_plan_authority,
)
from .claude_loop_render import render
from .claude_loop_state import (
    extract_agent_runtime_clock,
    extract_coordination_state,
    extract_inbox_observation,
    extract_packet_attention,
    load_master_plan_authority,
    load_review_state,
    typed_freshness_evidence,
)

AGENT_LOOP_SURFACE_CONTRACTS = (
    AgentDispatchAmbiguousGroup,
    AgentDispatchGovernanceDebt,
    AgentDispatchPeerLink,
    AgentDispatchRejection,
    AgentDispatchRoute,
    AgentDispatchRouter,
    AgentDispatchSessionNode,
    AgentDispatchWorkFocus,
    AgentLoopContext,
    AgentLoopOperatorOverride,
    InboxObservationState,
    WakeEvidence,
)


def run(args) -> int:
    """Render one or more typed agent-loop snapshots from dashboard state."""
    if bool(getattr(args, "execute", False)):
        print("agent-loop --execute is not enabled until typed dispatch lands.")
        return 2
    if bool(getattr(args, "follow", False)):
        return run_follow(
            args,
            build_snapshot=build_claude_loop_snapshot,
            render_snapshot=render,
        )
    payload = build_claude_loop_snapshot(args)
    print(render(args, payload))
    return 0


def build_claude_loop_snapshot(args) -> dict[str, Any]:
    """Return the bounded agent-loop view over the shared dashboard contract."""
    repo_root = Path(getattr(args, "repo_root", None) or REPO_ROOT).resolve()
    actor_id = str(getattr(args, "actor", "claude") or "claude").strip()
    actor_role = str(getattr(args, "role", "dashboard") or "dashboard").strip()
    session_id = str(getattr(args, "session_id", "") or "").strip()
    loop_intent, plan_ref, packet_id = _loop_request(args)
    dashboard = build_dashboard_snapshot(
        repo_root=repo_root,
        view="overview",
        role=actor_role,
        include_review_state=True,
    )
    # Per Codex rev_pkt_2376: claude-loop must read ONE frozen ReviewState
    # snapshot per render. Earlier code re-loaded review_state.json across
    # _load_coordination_state and _load_canonical_active_packet, so a
    # concurrent writer could downgrade the cached projection between
    # reads, which is exactly the 0/0 regression Codex observed.
    review_state = dict(coerce_mapping(dashboard.get("_review_state")))
    if not review_state:
        review_state = load_review_state(repo_root)
    master_plan = load_master_plan_authority(repo_root)
    typed_freshness = typed_freshness_evidence(review_state)
    loop_decision = _build_loop_decision(
        args=args,
        review_state=review_state,
        dashboard=dashboard,
        actor_id=actor_id,
        actor_role=actor_role,
        session_id=session_id,
        loop_intent=loop_intent,
        plan_ref=plan_ref,
        packet_id=packet_id,
        master_plan=master_plan,
    )
    loop_decision_payload = loop_decision.to_dict()
    loop_packet_attention = _loop_packet_attention(
        review_state=review_state,
        actor_id=actor_id,
        actor_role=actor_role,
        session_id=session_id,
    )
    master_plan_authority = compact_master_plan_authority(
        master_plan,
        target_ref=loop_decision.target_ref or plan_ref,
    )
    proof_evidence = build_loop_proof_evidence(
        loop_decision=loop_decision_payload,
        master_plan_authority=master_plan_authority,
        review_state=review_state,
    )
    now = _loop_now(dashboard=dashboard, review_state=review_state)
    command_name = str(getattr(args, "command", "") or "claude-loop")
    payload: dict[str, Any] = {"schema_version": 1, "command": command_name}
    payload.update(
        (
            ("dashboard_contract_id", dashboard.get("contract_id")),
            ("dashboard_schema_version", dashboard.get("schema_version")),
            ("timestamp", dashboard.get("timestamp")),
            ("repo", dashboard.get("repo", {})),
            ("now", now),
        )
    )
    payload.update(
        (
            ("control_plane", dashboard.get("control_plane", {})),
            ("ack_freshness", dashboard.get("ack_freshness", {})),
            ("session_outcomes", dashboard.get("session_outcomes", {})),
            ("instruction_transitions", _recent_instruction_transitions(repo_root)),
            (
                "pending_packets",
                scoped_packets(
                    dashboard.get("pending_packets"),
                    actor_id=actor_id,
                    actor_role=actor_role,
                    session_id=session_id,
                ),
            ),
            (
                "control_packets",
                scoped_packets(
                    dashboard.get("control_packets"),
                    actor_id=actor_id,
                    actor_role=actor_role,
                    session_id=session_id,
                ),
            ),
        )
    )
    payload.update(
        (
            ("active_codex_sessions", dashboard.get("active_codex_sessions", {})),
            ("agent_mind", dashboard.get("agent_mind", {})),
            ("agent_minds", dashboard.get("agent_minds", {})),
            ("session_posture", dashboard.get("session_posture", {})),
            ("system_topology", dashboard.get("system_topology", {})),
            ("master_plan_authority", master_plan_authority),
            (
                "packet_continuity_index",
                dashboard.get("packet_continuity_index", {}),
            ),
            ("continuity_attention", dashboard.get("continuity_attention", {})),
            # Per rev_pkt_2298/2301/2376: typed coordination_state read
            # from the SAME frozen review_state snapshot as canonical_active
            # so the two cannot disagree mid-render.
            ("coordination_state", extract_coordination_state(review_state)),
            (
                "canonical_active_packet_for_actor",
                loop_decision.active_packet_id,
            ),
            (
                "legacy_unscoped_packet_for_actor",
                loop_decision.legacy_unscoped_packet_id,
            ),
            (
                "canonical_active_packet_for_claude",
                loop_decision.active_packet_id if actor_id == "claude" else "",
            ),
            (
                "legacy_unscoped_packet_for_claude",
                loop_decision.legacy_unscoped_packet_id if actor_id == "claude" else "",
            ),
            ("agent_loop_decision", loop_decision_payload),
            ("proof_evidence", proof_evidence),
            # Per rev_pkt_2376: freshness evidence for the typed snapshot
            # that backs coordination_state / agent_work_board / canonical.
            # Consumers MUST check this before trusting typed counts; if
            # missing, the renderer will mark counts as unavailable/stale.
            ("typed_snapshot_freshness", typed_freshness),
            # Per rev_pkt_2486 Scope 3: machine-readable pivot signal.
            # Renderers MUST surface pivot_required + pivot_reasons so agents
            # can detect packet-arrival / superseded-active / pending-inbox
            # state without voluntary polling. Read from reviewer_runtime
            # contract typed projection.
            ("inbox_observation", extract_inbox_observation(review_state)),
            # Per rev_pkt_2498 (6): expose the durable typed wake/attention
            # runtime alongside the legacy inbox_observation so consumers can
            # migrate to the richer per-actor_session contract. The shared
            # AgentRuntimeClock binds all agents to one source_latest_event_id.
            ("packet_attention", loop_packet_attention),
            ("agent_runtime_clock", extract_agent_runtime_clock(review_state)),
            (
                "loop_request",
                {
                    "mode": loop_intent,
                    "plan_ref": plan_ref,
                    "packet_id": packet_id,
                    "execute_requested": bool(getattr(args, "execute", False)),
                },
            ),
        )
    )
    return payload


def _loop_request(args) -> tuple[str, str, str]:
    mode = str(getattr(args, "mode", "auto") or "auto").strip()
    plan_ref = str(getattr(args, "plan", "") or "").strip()
    packet_id = str(getattr(args, "packet", "") or "").strip()
    if bool(getattr(args, "plan377", False)):
        mode = "plan"
        plan_ref = plan_ref or "MP-377"
    if packet_id and mode == "auto":
        mode = "packet"
    if plan_ref and mode == "auto":
        mode = "plan"
    return mode, plan_ref, packet_id


def _loop_now(
    *,
    dashboard: dict[str, Any],
    review_state: dict[str, Any],
) -> dict[str, Any]:
    now = dict(dashboard.get("now", {}))
    now["instruction_provenance"] = _current_instruction_provenance(
        dashboard=dashboard,
        review_state=review_state,
    )
    now["priority_decision"] = dict(
        coerce_mapping(now.get("priority_decision"))
        or _current_priority_decision(review_state)
    )
    return now


def _build_loop_decision(
    *,
    args,
    review_state: dict[str, Any],
    dashboard: dict[str, Any],
    actor_id: str,
    actor_role: str,
    session_id: str,
    loop_intent: str,
    plan_ref: str,
    packet_id: str,
    master_plan: dict[str, Any],
):
    return build_agent_loop_decision(
        review_state=review_state,
        dashboard=dashboard,
        actor_id=actor_id,
        actor_role=actor_role,
        session_id=session_id,
        loop_intent=loop_intent,
        requested_plan_ref=plan_ref,
        requested_packet_id=packet_id,
        master_plan=master_plan,
        operator_override_requested=getattr(args, "operator_override", False),
        operator_override_reason=getattr(args, "override_reason", ""),
        operator_override_scope=getattr(args, "override_scope", "edit-only"),
        operator_override_by=getattr(args, "override_by", "operator"),
    )


def _loop_packet_attention(
    *,
    review_state: dict[str, Any],
    actor_id: str,
    actor_role: str,
    session_id: str,
) -> dict[str, Any]:
    return asdict(
        packet_attention_for_agent(
            review_state,
            actor=actor_id,
            role=actor_role,
            session=session_id,
            fallback_attention=extract_packet_attention(review_state),
        )
    )


def _current_priority_decision(review_state: dict[str, Any]) -> dict[str, Any]:
    queue = coerce_mapping(review_state.get("queue"))
    decision = coerce_mapping(queue.get("instruction_priority_decision"))
    if decision:
        return dict(decision)
    source = coerce_mapping(queue.get("derived_next_instruction_source"))
    return dict(coerce_mapping(source.get("priority_decision")))


def _current_instruction_provenance(
    *,
    dashboard: dict[str, Any],
    review_state: dict[str, Any],
) -> dict[str, Any]:
    dashboard_now = coerce_mapping(dashboard.get("now"))
    dashboard_provenance = coerce_mapping(
        dashboard_now.get("instruction_provenance")
    )
    if dashboard_provenance:
        return dict(dashboard_provenance)

    queue = coerce_mapping(review_state.get("queue"))
    source = coerce_mapping(queue.get("derived_next_instruction_source"))
    provenance = coerce_mapping(source.get("provenance"))
    if provenance:
        return dict(provenance)

    control_plane = coerce_mapping(dashboard.get("control_plane"))
    coordination = coerce_mapping(control_plane.get("coordination"))
    active_target = coerce_mapping(coordination.get("active_target"))
    if active_target:
        return _active_target_provenance(active_target, control_plane)
    return {}


def _active_target_provenance(
    active_target: dict[str, Any],
    control_plane: dict[str, Any],
) -> dict[str, Any]:
    return dict(
        (
            ("schema_version", 1),
            ("contract_id", "IngestionProvenance"),
            ("source_file", str(active_target.get("plan_path") or "")),
            ("source_line", 0),
            ("source_kind", "CoordinationSnapshot"),
            ("source_hash", str(active_target.get("expected_revision") or "")),
            ("observed_at_utc", str(control_plane.get("timestamp") or "")),
            ("section_authority", "owner_doc"),
        )
    )


def _recent_instruction_transitions(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / DEFAULT_INSTRUCTION_TRANSITIONS_REL
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    receipts: list[dict[str, Any]] = []
    for line in lines[-5:]:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            receipts.append(instruction_transition_receipt_from_mapping(payload).to_dict())
    return receipts


__all__ = ["build_claude_loop_snapshot", "run"]
