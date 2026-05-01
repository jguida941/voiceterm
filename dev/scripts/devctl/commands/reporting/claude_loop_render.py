"""Renderers for the Claude loop surface."""

from __future__ import annotations

import json
from typing import Any

from ...runtime.session_posture_simple_render import render_simple_posture_snapshot
from .claude_loop_compact import compact_agent_loop_output


def render(args, payload: dict[str, Any]) -> str:
    fmt = str(getattr(args, "format", "md") or "md")
    if fmt == "json":
        if str(payload.get("command") or "") == "agent-loop":
            return json.dumps(compact_agent_loop_output(payload), indent=2)
        return json.dumps(payload, indent=2)
    if fmt == "simple":
        now = payload.get("now", {})
        return render_simple_posture_snapshot(
            title=_surface_title(payload),
            next_action=now.get("next_action") if isinstance(now, dict) else "",
            top_blocker=now.get("top_blocker") if isinstance(now, dict) else "",
            session_posture=payload.get("session_posture"),
        )
    return render_markdown(payload)


def render_markdown(payload: dict[str, Any]) -> str:
    now = payload.get("now", {})
    lines = [f"# {_surface_title(payload)}", ""]
    lines.extend(_header_lines(payload=payload, now=now))
    lines.extend(_packet_authority_lines(payload=payload, now=now))
    lines.extend(_freshness_lines(payload))
    lines.extend(_pending_packet_lines(payload.get("pending_packets", [])))
    lines.extend(_action_request_lines(payload.get("control_packets", [])))
    return "\n".join(lines)


def _header_lines(*, payload: dict[str, Any], now: object) -> list[str]:
    now_map = _mapping(now)
    lines = [
        f"- owner: {now_map.get('owner', 'n/a')}",
        f"- next_action: {now_map.get('next_action', 'n/a')}",
        f"- top_blocker: {now_map.get('top_blocker', 'none')}",
    ]
    loop_decision = _mapping(payload.get("agent_loop_decision"))
    if loop_decision:
        lines.extend(_loop_decision_lines(loop_decision))
    proof_evidence = _mapping(payload.get("proof_evidence"))
    if proof_evidence:
        lines.extend(_proof_evidence_lines(proof_evidence))
    provenance = _mapping(now_map.get("instruction_provenance"))
    if provenance:
        source_file = provenance.get("source_file", "n/a")
        source_line = provenance.get("source_line", 0)
        lines.append(f"- instruction_source: {source_file}:{source_line}")
    return lines


def _loop_decision_lines(loop_decision: dict[str, Any]) -> list[str]:
    return [
        "- loop_decision: "
        f"{loop_decision.get('lifecycle_state', 'n/a')} / "
        f"{loop_decision.get('decision', 'n/a')} / "
        f"{loop_decision.get('required_action', 'n/a')}",
        "- loop_identity: "
        f"{loop_decision.get('actor_id', 'n/a')}:"
        f"{loop_decision.get('actor_role', 'n/a')}:"
        f"{loop_decision.get('session_id', '') or 'unscoped'}",
        "- loop_continue: "
        f"{loop_decision.get('should_continue_loop', False)} | "
        f"safe={loop_decision.get('safe_to_continue', False)} | "
        f"may_mutate={loop_decision.get('may_mutate', False)}",
        "- loop_attention: "
        f"wake={loop_decision.get('wake_required', False)} | "
        f"pivot={loop_decision.get('pivot_required', False)} | "
        f"pending={loop_decision.get('pending_packet_count', 0)}",
        "- loop_policy: "
        f"{loop_decision.get('loop_mode', 'n/a')} | "
        f"intent={loop_decision.get('loop_intent', 'auto')} | "
        f"cadence={loop_decision.get('recommended_cadence_seconds', 0)}s | "
        f"can_run_next={loop_decision.get('can_run_next_command', False)} | "
        f"dogfood={loop_decision.get('dogfood_record_allowed', False)}",
        "- loop_target: "
        f"{loop_decision.get('target_kind', '') or 'none'}:"
        f"{loop_decision.get('target_ref', '') or 'none'} | "
        f"advance={loop_decision.get('advance_allowed', False)} | "
        f"proof={loop_decision.get('proof_state', 'n/a')}",
        "- loop_proofs: "
        f"required={_csv(loop_decision.get('required_proofs')) or 'none'} | "
        f"missing={_csv(loop_decision.get('missing_proofs')) or 'none'}",
        "- loop_wake_source: "
        f"{loop_decision.get('wake_source', 'n/a')} | "
        f"driver={loop_decision.get('loop_driver_agent', 'n/a')} | "
        f"reason={loop_decision.get('policy_reason', 'n/a')}",
        f"- next_loop_command: {loop_decision.get('next_loop_command', '')}",
    ]


def _proof_evidence_lines(proof_evidence: dict[str, Any]) -> list[str]:
    plan = _mapping(proof_evidence.get("plan_target"))
    clock = _mapping(proof_evidence.get("runtime_clock"))
    round_proof = _mapping(proof_evidence.get("round_proof"))
    lines = [
        "- proof_evidence: "
        f"state={proof_evidence.get('proof_state', 'n/a')} | "
        f"satisfied={_csv(proof_evidence.get('satisfied_proofs')) or 'none'} | "
        f"missing={_csv(proof_evidence.get('missing_proofs')) or 'none'}",
        "- proof_runtime_clock: "
        f"{clock.get('state', 'n/a')} | "
        f"event={clock.get('source_latest_event_id', '') or 'none'}",
    ]
    if plan:
        lines.append(
            "- proof_plan_target: "
            f"{plan.get('state', 'n/a')} | "
            f"target={plan.get('target_ref', '') or 'none'} | "
            f"rows={plan.get('row_count', 0)} | "
            f"matches={_matched_row_ids(plan.get('matched_rows')) or 'none'}"
        )
    if round_proof:
        lines.append(
            "- proof_round: "
            f"{round_proof.get('state', 'n/a')} | "
            f"rows={round_proof.get('row_count', 0)} | "
            f"matches={_matched_round_ids(round_proof.get('matched_rows')) or 'none'}"
        )
    return lines


def _matched_row_ids(rows: object) -> str:
    if not isinstance(rows, list):
        return ""
    return ", ".join(
        str(row.get("row_id") or "").strip()
        for row in rows
        if isinstance(row, dict) and str(row.get("row_id") or "").strip()
    )


def _matched_round_ids(rows: object) -> str:
    if not isinstance(rows, list):
        return ""
    return ", ".join(
        str(row.get("proof_id") or "").strip()
        for row in rows
        if isinstance(row, dict) and str(row.get("proof_id") or "").strip()
    )


def _packet_authority_lines(*, payload: dict[str, Any], now: object) -> list[str]:
    lines: list[str] = []
    loop_decision = _mapping(payload.get("agent_loop_decision"))
    decision = _mapping(_mapping(now).get("priority_decision"))
    actor = str(loop_decision.get("actor_id") or "claude")
    canonical = str(
        loop_decision.get("active_packet_id")
        or payload.get("canonical_active_packet_for_actor")
        or payload.get("canonical_active_packet_for_claude")
        or ""
    )
    legacy_unscoped = str(
        loop_decision.get("legacy_unscoped_packet_id")
        or payload.get("legacy_unscoped_packet_for_actor")
        or payload.get("legacy_unscoped_packet_for_claude")
        or ""
    )
    legacy_pid = str(decision.get("selected_instruction_id") or "") if decision else ""
    if canonical:
        lines.append(f"- active_packet ({actor}, typed): {canonical}")
        if legacy_unscoped and legacy_unscoped != canonical:
            lines.append(f"- legacy_unscoped_packet (not claimable): {legacy_unscoped}")
        if legacy_pid and legacy_pid != canonical:
            lines.append(
                f"- (legacy priority_decision picked {legacy_pid}; "
                "superseded by typed canonical per rev_pkt_2326/2352)"
            )
        elif decision:
            lines.append(
                "- priority_decision (legacy, agrees): "
                f"{decision.get('rule_id', 'n/a')} -> {legacy_pid}"
            )
    elif loop_decision:
        lines.append(f"- active_packet ({actor}, typed): none")
        if legacy_unscoped:
            lines.append(f"- legacy_unscoped_packet (not claimable): {legacy_unscoped}")
    elif decision:
        lines.append(
            "- priority_decision (legacy): "
            f"{decision.get('rule_id', 'n/a')} -> "
            f"{decision.get('selected_instruction_id', 'n/a')}"
        )
    ack = _mapping(payload.get("ack_freshness"))
    if ack.get("available"):
        label = "current" if ack.get("is_current") else "stale"
        lines.append(f"- implementer_ack: {label}")
    return lines


def _freshness_lines(payload: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    codex = _mapping(payload.get("active_codex_sessions"))
    freshness = _mapping(payload.get("typed_snapshot_freshness"))
    state = str(freshness.get("typed_snapshot_state") or "").strip()
    unavailable = state != "available"
    coord = payload.get("coordination_state", {})
    has_coord = isinstance(coord, dict) and bool(coord.get("observed_runtime"))
    if codex:
        lines.append(_codex_sessions_line(codex, state, unavailable, has_coord))
    lines.extend(_coordination_lines(coord, freshness, state, unavailable))
    return lines


def _codex_sessions_line(
    codex: dict[str, Any],
    state: str,
    unavailable: bool,
    has_coord: bool,
) -> str:
    legacy_live = codex.get("live_count", 0)
    legacy_total = codex.get("count", 0)
    typed_live = codex.get("typed_live_count")
    typed_total = codex.get("typed_session_count")
    if unavailable:
        return (
            "- codex_sessions: typed work-board unavailable "
            f"(freshness={state or 'missing'}) "
            f"[legacy session-probe: {legacy_live}/{legacy_total}]"
        )
    if isinstance(typed_live, int) and isinstance(typed_total, int):
        return (
            f"- codex_sessions: {typed_live} live / {typed_total} "
            f"(typed work-board) [legacy session-probe: {legacy_live}/{legacy_total}]"
        )
    if has_coord:
        return (
            f"- codex_sessions (legacy): {legacy_live} live / {legacy_total} "
            "registered [typed work-board has evidence; prefer canonical_active_packet]"
        )
    return (
        f"- codex_sessions (legacy, unverified): {legacy_live} live / "
        f"{legacy_total} registered [no typed work-board evidence in this projection]"
    )


def _coordination_lines(
    coord: object,
    freshness: dict[str, Any],
    state: str,
    unavailable: bool,
) -> list[str]:
    if unavailable:
        return [
            "- coordination_topology: unavailable "
            f"(freshness={state or 'missing'}; "
            f"refreshed_at={freshness.get('refreshed_at_utc') or 'n/a'})"
        ]
    if not isinstance(coord, dict) or not coord:
        return []
    observed = _mapping(coord.get("observed_runtime"))
    actor_labels = list(observed.get("active_runtime_providers") or [])
    for channel in observed.get("active_operator_channels") or []:
        actor_labels.append(f"dashboard:{channel}")
    actors_text = ", ".join(actor_labels) if actor_labels else "none"
    topology = str(coord.get("coordination_topology") or "unknown")
    lines = [
        f"- coordination_topology: {topology} "
        f"({int(observed.get('active_actor_count') or 0)} active actors: {actors_text})",
        f"- authority_mode: {coord.get('authority_mode') or 'unknown'} | "
        f"recovery: {coord.get('recovery_eligibility') or 'unknown'}",
    ]
    if topology == "multi_agent_active" and coord.get("legacy_reviewer_mode") == "single_agent":
        lines.append(
            "- WARNING: legacy_reviewer_mode='single_agent' is authority/review-gate "
            "vocabulary; observed runtime is multi_agent_active per typed work-board."
        )
    return lines


def _pending_packet_lines(raw_packets: object) -> list[str]:
    packets = raw_packets if isinstance(raw_packets, list) else []
    lines = ["", "## Pending Packets", ""]
    if not packets:
        lines.append("- none")
        return lines
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        lines.append(
            f"- `{packet.get('packet_id')}` {packet.get('kind') or 'packet'} "
            f"{packet.get('requested_action')}: {packet.get('summary')}"
        )
    return lines


def _action_request_lines(raw_packets: object) -> list[str]:
    packets = raw_packets if isinstance(raw_packets, list) else []
    lines = ["", "## Action Requests", ""]
    if not packets:
        lines.append("- none")
        return lines
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        state = packet.get("lifecycle_current_state") or packet.get("status") or "unknown"
        reason = packet.get("execution_failed_reason") or packet.get(
            "apply_pending_after_execution_reason",
            "",
        )
        reason_suffix = f" ({reason})" if reason else ""
        zref = packet.get("semantic_zref")
        zref_suffix = f" `{zref}`" if zref else ""
        lines.append(
            f"- `{packet.get('packet_id')}` {packet.get('requested_action')}: "
            f"`{state}`{reason_suffix}{zref_suffix}"
        )
    return lines


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _surface_title(payload: dict[str, Any]) -> str:
    return "Agent Loop" if payload.get("command") == "agent-loop" else "Claude Loop"


def _csv(value: object) -> str:
    if not isinstance(value, list):
        return ""
    return ",".join(str(item) for item in value if str(item or "").strip())


__all__ = ["render", "render_markdown"]
