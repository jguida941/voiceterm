"""Markdown rendering helpers for review-channel projection bundles."""

from __future__ import annotations

from .attach_auth_render import append_attach_auth_policy_markdown
from .context_refs import context_pack_ref_summary
from .current_session_projection import (
    append_current_session_markdown,
    current_focus_line,
)
from .doctor_markdown import append_doctor_markdown
from .projection_markdown import append_push_markdown
from .pending_packets import (
    partition_live_packet_queue,
    reconcile_review_state_packet_queue,
)


def render_latest_markdown(
    review_state: dict[str, object],
    agent_registry: dict[str, object],
) -> str:
    """Build a complete markdown status rendering from review state."""
    queue = review_state.get("queue", {})
    bridge = review_state.get("bridge", {})
    current_session = review_state.get("current_session", {})
    packet_inbox = review_state.get("packet_inbox", {})
    review_candidate = review_state.get("review_candidate", {})
    md_compat = review_state.get("_compat") or {}
    runtime = md_compat.get("runtime", {})
    service_identity = md_compat.get("service_identity", {})
    attach_auth_policy = md_compat.get("attach_auth_policy", {})
    planned_topology = md_compat.get("planned_topology", {})
    push_enforcement = md_compat.get("push_enforcement", {})
    push_decision = md_compat.get("push_decision", {})
    doctor = md_compat.get("doctor", {})
    agents = agent_registry.get("agents", [])
    packets = review_state.get("packets", [])

    lines = ["# review-channel status", ""]
    lines.append(f"- timestamp: {review_state.get('timestamp')}")
    lines.append(f"- ok: {review_state.get('ok')}")
    lines.append(f"- pending_total: {queue.get('pending_total')}")
    lines.append(
        "- stale_packet_count: "
        f"{queue.get('stale_packet_count')} (expired pending packets)"
    )
    lines.append(
        f"- last_codex_poll_utc: {bridge.get('last_codex_poll_utc') or 'n/a'}"
    )
    lines.append(
        f"- last_worktree_hash: {bridge.get('last_worktree_hash') or 'n/a'}"
    )

    reviewed_hash_current = bridge.get("reviewed_hash_current")
    if reviewed_hash_current is not None:
        lines.append(f"- reviewed_hash_current: {reviewed_hash_current}")

    _append_service_identity(lines, service_identity)
    append_attach_auth_policy_markdown(lines, attach_auth_policy)
    append_runtime_markdown(lines, runtime)
    append_doctor_markdown(lines, doctor)
    append_push_markdown(lines, push_enforcement, push_decision)
    append_current_session_markdown(lines, current_session)
    _append_packet_inbox(lines, packet_inbox)
    append_review_candidate_markdown(lines, review_candidate)

    lines.append("")
    lines.append("## Current Instruction")
    lines.append(current_focus_line(review_state))

    _append_derived_instruction(lines, queue)
    _append_packet_queue_reconciliation(lines, review_state)
    append_planned_topology_markdown(lines, planned_topology)
    _append_agents(lines, agents)
    _append_packets(lines, packets)

    return "\n".join(lines)


# ── Section renderers ────────────────────────────────────────────


def _append_service_identity(lines: list[str], service_identity: object) -> None:
    if not isinstance(service_identity, dict):
        return
    lines.append("")
    lines.append("## Service Identity")
    for key in ("service_id", "project_id", "repo_root", "worktree_root",
                "bridge_path", "review_channel_path", "status_root"):
        lines.append(f"- {key}: {service_identity.get(key) or 'n/a'}")


def _append_derived_instruction(lines: list[str], queue: object) -> None:
    if not isinstance(queue, dict):
        return
    derived = queue.get("derived_next_instruction")
    source = queue.get("derived_next_instruction_source")
    if not derived:
        return
    lines.append("")
    lines.append("## Derived Next Instruction")
    lines.append(str(derived))
    if isinstance(source, dict):
        lines.append(f"- source: {source.get('source_path') or 'unknown'}")
        if source.get("phase_heading"):
            lines.append(f"- phase: {source['phase_heading']}")


def append_review_candidate_markdown(
    lines: list[str],
    review_candidate: object,
) -> None:
    if not isinstance(review_candidate, dict):
        return
    candidate_id = str(review_candidate.get("candidate_id") or "").strip()
    if not candidate_id:
        return
    lines.append("")
    lines.append("## Review Candidate")
    lines.append(f"- candidate_id: {candidate_id}")
    lines.append(f"- artifact_kind: {review_candidate.get('artifact_kind') or 'n/a'}")
    lines.append(f"- valid: {bool(review_candidate.get('valid'))}")
    lines.append(f"- ready_for_review: {bool(review_candidate.get('ready_for_review'))}")
    lines.append(f"- worktree_hash: {review_candidate.get('worktree_hash') or 'n/a'}")

    changed_paths = review_candidate.get("changed_paths")
    if isinstance(changed_paths, list) and changed_paths:
        lines.append("- changed_paths:")
        for path in changed_paths[:8]:
            lines.append(f"  - {path}")

    missing_scope_paths = review_candidate.get("missing_scope_paths")
    if isinstance(missing_scope_paths, list) and missing_scope_paths:
        lines.append("- missing_scope_paths:")
        for path in missing_scope_paths[:8]:
            lines.append(f"  - {path}")

    if review_candidate.get("invalidation_reason"):
        lines.append(
            f"- invalidation_reason: {review_candidate.get('invalidation_reason')}"
        )


def append_runtime_markdown(lines: list[str], runtime: object) -> None:
    if not isinstance(runtime, dict):
        return
    daemons = runtime.get("daemons")
    lines.append("")
    lines.append("## Runtime")
    lines.append(f"- active_daemons: {runtime.get('active_daemons') or 0}")
    lines.append(
        f"- last_daemon_event_utc: {runtime.get('last_daemon_event_utc') or 'n/a'}"
    )
    if not isinstance(daemons, dict):
        return
    for daemon_kind in ("publisher", "reviewer_supervisor"):
        daemon_state = daemons.get(daemon_kind)
        if not isinstance(daemon_state, dict):
            continue
        lines.append(
            f"- {daemon_kind}: "
            f"running={bool(daemon_state.get('running'))} "
            f"pid={int(daemon_state.get('pid', 0) or 0)} "
            f"snapshots={int(daemon_state.get('snapshots_emitted', 0) or 0)} "
            f"last_heartbeat_utc={daemon_state.get('last_heartbeat_utc') or 'n/a'} "
            f"stop_reason={daemon_state.get('stop_reason') or 'n/a'}"
        )


def append_planned_topology_markdown(
    lines: list[str],
    planned_topology: object,
) -> None:
    if not isinstance(planned_topology, dict):
        return
    providers = planned_topology.get("providers")
    if not isinstance(providers, (list, tuple)) or not providers:
        return
    lines.append("")
    lines.append("## Planned Topology")
    for provider in providers:
        if not isinstance(provider, dict):
            continue
        requested_budget = provider.get("requested_worker_budget")
        budget_text = "n/a" if requested_budget is None else str(requested_budget)
        lines.append(
            f"- {provider.get('provider')}: "
            f"role={provider.get('role') or 'unknown'} | "
            f"planned_lane_count={provider.get('planned_lane_count') or 0} | "
            f"requested_worker_budget={budget_text}"
        )


def _append_agents(lines: list[str], agents: object) -> None:
    lines.append("")
    lines.append("## Agents")
    if not isinstance(agents, list):
        return
    for agent in agents:
        if not isinstance(agent, dict):
            continue
        lines.append(
            f"- {agent.get('agent_id')}: {agent.get('job_state')} | "
            f"{agent.get('lane_title')} | {agent.get('branch') or 'n/a'}"
        )


def _append_packets(lines: list[str], packets: object) -> None:
    if not isinstance(packets, list) or not packets:
        return
    live_packets, history_packets, _ = partition_live_packet_queue(packets)
    if live_packets:
        lines.append("")
        lines.append("## Live Packets")
        for packet in live_packets[:5]:
            summary = _format_packet_line(packet)
            pack_kinds = context_pack_ref_summary(packet.get("context_pack_refs"))
            if pack_kinds:
                summary += f" | packs: {pack_kinds}"
            lines.append(summary)
    if history_packets:
        lines.append("")
        lines.append("## Packet History")
        if len(history_packets) > 5:
            lines.append(f"- showing latest 5 of {len(history_packets)} history packets")
        for packet in history_packets[:5]:
            summary = _format_packet_line(packet, stale_pending=True)
            pack_kinds = context_pack_ref_summary(packet.get("context_pack_refs"))
            if pack_kinds:
                summary += f" | packs: {pack_kinds}"
            lines.append(summary)


def _append_packet_queue_reconciliation(
    lines: list[str],
    review_state: dict[str, object],
) -> None:
    reconciliation = reconcile_review_state_packet_queue(
        review_state,
        history_limit=5,
    )
    if not reconciliation.needs_attention():
        return
    lines.append("")
    lines.append("## Packet Queue Reconciliation")
    lines.append(f"- live_pending_total: {reconciliation.live_pending_total}")
    lines.append(f"- history_total: {reconciliation.history_total}")
    lines.append(f"- expired_pending_total: {reconciliation.stale_pending_total}")
    lines.append(f"- queue_pending_total: {reconciliation.queue_pending_total}")
    lines.append(f"- queue_stale_total: {reconciliation.queue_stale_total}")
    lines.append(
        "- expired_pending_hidden_from_inbox_total: "
        f"{reconciliation.stale_pending_hidden_from_inbox_total}"
    )
    lines.append(f"- history_shown_total: {reconciliation.history_shown_total}")
    lines.append(f"- history_truncated: {reconciliation.history_truncated}")
    if reconciliation.stale_pending_hidden_from_inbox_total:
        lines.append(
            "- note: expired pending packets are archived audit rows whose TTL "
            "elapsed; they stay in history with disposition evidence and are "
            "intentionally excluded from the live inbox until they are reissued"
        )


def _append_packet_inbox(lines: list[str], packet_inbox: object) -> None:
    if not isinstance(packet_inbox, dict):
        return
    attention_revision = str(packet_inbox.get("attention_revision") or "").strip()
    agents = packet_inbox.get("agents")
    if not attention_revision and not isinstance(agents, list):
        return
    lines.append("")
    lines.append("## Packet Inbox")
    lines.append(f"- attention_revision: {attention_revision or 'n/a'}")
    if not isinstance(agents, list):
        return
    for agent in agents:
        if not isinstance(agent, dict):
            continue
        status = str(agent.get("attention_status") or "none").strip() or "none"
        if status == "none" and not agent.get("latest_finding_packet_id"):
            continue
        lines.append(
            f"- {agent.get('agent')}: status={status} "
            f"delivery={agent.get('delivery_state') or 'idle'} "
            f"current_instruction_packet_id={agent.get('current_instruction_packet_id') or 'none'} "
            f"latest_finding_packet_id={agent.get('latest_finding_packet_id') or 'none'}"
        )
    if reconciliation.history_truncated:
        lines.append(
            "- note: this surface is only showing the newest packet-history rows"
        )


def _format_packet_line(packet: object, *, stale_pending: bool = False) -> str:
    if not isinstance(packet, dict):
        return "- packet: (unavailable)"
    status = str(packet.get("status") or "unknown").strip()
    if stale_pending and status == "pending":
        status = "pending (expired)"
    return (
        f"- {packet.get('packet_id')}: {status} | "
        f"{packet.get('from_agent')} -> {packet.get('to_agent')} | "
        f"{packet.get('summary')}"
    )
