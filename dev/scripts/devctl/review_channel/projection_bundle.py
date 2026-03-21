"""Projection bundle writers for review-channel state surfaces."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .attach_auth_render import append_attach_auth_policy_markdown
from .core import LaneAssignment
from .context_refs import (
    context_pack_ref_summary,
    normalize_context_pack_refs,
)
from .current_session_projection import (
    append_current_session_markdown,
    current_focus_line,
)


@dataclass(frozen=True)
class ReviewChannelProjectionPaths:
    """Paths written for the latest review projections."""

    root_dir: str
    review_state_path: str
    compact_path: str
    full_path: str
    actions_path: str
    trace_path: str
    latest_markdown_path: str
    agent_registry_path: str


def projection_paths_to_dict(
    paths: ReviewChannelProjectionPaths | None,
) -> dict[str, str] | None:
    """Convert projection paths into a report-friendly dict."""
    if paths is None:
        return None
    return asdict(paths)


def build_agent_registry_from_lanes(
    lanes: list[LaneAssignment],
    *,
    timestamp: str,
    provider_state: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    """Build the typed lane registry shared by review projections."""
    provider_state = provider_state or {}
    registry_agents: list[dict[str, object]] = []
    for lane in lanes:
        state = provider_state.get(lane.provider, {})
        registry_agents.append(
            {
                "agent_id": lane.agent_id,
                "provider": lane.provider,
                "display_name": lane.agent_id,
                "current_job": lane.lane,
                "job_state": state.get("job_state", "assigned"),
                "waiting_on": state.get("waiting_on"),
                "last_packet_seen": state.get("last_packet_seen"),
                "last_packet_applied": state.get("last_packet_applied"),
                "script_profile": state.get(
                    "script_profile",
                    "markdown-bridge-conductor",
                ),
                "lane": lane.provider,
                "lane_title": lane.lane,
                "mp_scope": lane.mp_scope,
                "worktree": lane.worktree,
                "branch": lane.branch,
                "updated_at": timestamp,
            }
        )
    return {
        "schema_version": 1,
        "command": "review-channel",
        "timestamp": timestamp,
        "agents": registry_agents,
    }


def write_projection_bundle(
    *,
    output_root: Path,
    review_state: dict[str, object],
    agent_registry: dict[str, object],
    action: str,
    trace_events: list[dict[str, object]] | None = None,
    full_extras: dict[str, object] | None = None,
) -> ReviewChannelProjectionPaths:
    """Write a projection bundle from one reduced review-state snapshot."""
    compact = _build_compact_projection(review_state)
    actions = _build_actions_projection(review_state)
    full = {
        "schema_version": 1,
        "command": "review-channel",
        "action": action,
        "timestamp": review_state.get("timestamp"),
        "ok": review_state.get("ok"),
        "review_state": review_state,
        "agent_registry": agent_registry,
        "warnings": review_state.get("warnings", []),
        "errors": review_state.get("errors", []),
    }
    if isinstance(full_extras, dict):
        full.update(full_extras)
    latest_markdown = _render_latest_markdown(review_state, agent_registry)

    registry_dir = output_root / "registry"
    registry_dir.mkdir(parents=True, exist_ok=True)

    review_state_path = output_root / "review_state.json"
    compact_path = output_root / "compact.json"
    full_path = output_root / "full.json"
    actions_path = output_root / "actions.json"
    trace_path = output_root / "trace.ndjson"
    latest_markdown_path = output_root / "latest.md"
    agent_registry_path = registry_dir / "agents.json"

    review_state_path.write_text(json.dumps(review_state, indent=2), encoding="utf-8")
    compact_path.write_text(json.dumps(compact, indent=2), encoding="utf-8")
    full_path.write_text(json.dumps(full, indent=2), encoding="utf-8")
    actions_path.write_text(json.dumps(actions, indent=2), encoding="utf-8")
    trace_path.write_text(_render_trace_projection(trace_events or []), encoding="utf-8")
    latest_markdown_path.write_text(latest_markdown, encoding="utf-8")
    agent_registry_path.write_text(
        json.dumps(agent_registry, indent=2),
        encoding="utf-8",
    )

    return ReviewChannelProjectionPaths(
        root_dir=str(output_root),
        review_state_path=str(review_state_path),
        compact_path=str(compact_path),
        full_path=str(full_path),
        actions_path=str(actions_path),
        trace_path=str(trace_path),
        latest_markdown_path=str(latest_markdown_path),
        agent_registry_path=str(agent_registry_path),
    )


def _build_compact_projection(review_state: dict[str, object]) -> dict[str, object]:
    queue = review_state.get("queue", {})
    bridge = review_state.get("bridge", {})
    current_session = review_state.get("current_session", {})
    compat = review_state.get("_compat") or {}
    service_identity = compat.get("service_identity")
    attach_auth_policy = compat.get("attach_auth_policy")
    current_focus = current_focus_line(review_state)
    return {
        "schema_version": 1,
        "command": "review-channel",
        "timestamp": review_state.get("timestamp"),
        "ok": review_state.get("ok"),
        "review": review_state.get("review"),
        "current_session": current_session,
        "service_identity": service_identity,
        "attach_auth_policy": attach_auth_policy,
        "bridge": {
            "last_codex_poll_utc": bridge.get("last_codex_poll_utc"),
            "last_worktree_hash": bridge.get("last_worktree_hash"),
            "current_instruction": current_focus,
        },
        "queue": {
            **queue,
            "current_focus": current_focus,
        },
        "warnings": review_state.get("warnings", []),
        "errors": review_state.get("errors", []),
    }


def _build_actions_projection(review_state: dict[str, object]) -> dict[str, object]:
    packets = review_state.get("packets")
    action_rows: list[dict[str, object]] = []
    if isinstance(packets, list):
        for packet in packets:
            if not isinstance(packet, dict):
                continue
            action_rows.append(
                {
                    "packet_id": packet.get("packet_id"),
                    "requested_action": packet.get("requested_action"),
                    "policy_hint": packet.get("policy_hint"),
                    "approval_required": packet.get("approval_required"),
                    "status": packet.get("status"),
                    "context_pack_refs": normalize_context_pack_refs(
                        packet.get("context_pack_refs")
                    ),
                }
            )
    return {
        "schema_version": 1,
        "command": "review-channel",
        "timestamp": review_state.get("timestamp"),
        "actions": action_rows,
    }


def _render_trace_projection(trace_events: list[dict[str, object]]) -> str:
    lines: list[str] = []
    for event in trace_events:
        lines.append(json.dumps(event, sort_keys=True))
    return "\n".join(lines) + ("\n" if lines else "")


def _render_latest_markdown(
    review_state: dict[str, object],
    agent_registry: dict[str, object],
) -> str:
    queue = review_state.get("queue", {})
    bridge = review_state.get("bridge", {})
    current_session = review_state.get("current_session", {})
    md_compat = review_state.get("_compat") or {}
    runtime = md_compat.get("runtime", {})
    service_identity = md_compat.get("service_identity", {})
    attach_auth_policy = md_compat.get("attach_auth_policy", {})
    agents = agent_registry.get("agents", [])
    packets = review_state.get("packets", [])
    lines = ["# review-channel status", ""]
    lines.append(f"- timestamp: {review_state.get('timestamp')}")
    lines.append(f"- ok: {review_state.get('ok')}")
    lines.append(f"- pending_total: {queue.get('pending_total')}")
    lines.append(f"- stale_packet_count: {queue.get('stale_packet_count')}")
    lines.append(
        f"- last_codex_poll_utc: {bridge.get('last_codex_poll_utc') or 'n/a'}"
    )
    lines.append(
        f"- last_worktree_hash: {bridge.get('last_worktree_hash') or 'n/a'}"
    )
    reviewed_hash_current = bridge.get("reviewed_hash_current")
    if reviewed_hash_current is not None:
        lines.append(f"- reviewed_hash_current: {reviewed_hash_current}")
    if isinstance(service_identity, dict):
        lines.append("")
        lines.append("## Service Identity")
        lines.append(f"- service_id: {service_identity.get('service_id') or 'n/a'}")
        lines.append(f"- project_id: {service_identity.get('project_id') or 'n/a'}")
        lines.append(f"- repo_root: {service_identity.get('repo_root') or 'n/a'}")
        lines.append(
            f"- worktree_root: {service_identity.get('worktree_root') or 'n/a'}"
        )
        lines.append(f"- bridge_path: {service_identity.get('bridge_path') or 'n/a'}")
        lines.append(
            "- review_channel_path: "
            f"{service_identity.get('review_channel_path') or 'n/a'}"
        )
        lines.append(f"- status_root: {service_identity.get('status_root') or 'n/a'}")
    append_attach_auth_policy_markdown(lines, attach_auth_policy)
    _append_runtime_markdown(lines, runtime)
    append_current_session_markdown(lines, current_session)
    lines.append("")
    lines.append("## Current Instruction")
    lines.append(current_focus_line(review_state))
    derived_next_instruction = queue.get("derived_next_instruction")
    derived_source = queue.get("derived_next_instruction_source")
    if derived_next_instruction:
        lines.append("")
        lines.append("## Derived Next Instruction")
        lines.append(str(derived_next_instruction))
        if isinstance(derived_source, dict):
            lines.append(
                f"- source: {derived_source.get('source_path') or 'unknown'}"
            )
            if derived_source.get("phase_heading"):
                lines.append(f"- phase: {derived_source['phase_heading']}")
    lines.append("")
    lines.append("## Agents")
    if isinstance(agents, list):
        for agent in agents:
            if not isinstance(agent, dict):
                continue
            lines.append(
                f"- {agent.get('agent_id')}: {agent.get('job_state')} | "
                f"{agent.get('lane_title')} | {agent.get('branch')}"
            )
    if isinstance(packets, list) and packets:
        lines.append("")
        lines.append("## Packets")
        for packet in packets[:5]:
            if not isinstance(packet, dict):
                continue
            summary = (
                f"- {packet.get('packet_id')}: {packet.get('status')} | "
                f"{packet.get('from_agent')} -> {packet.get('to_agent')} | "
                f"{packet.get('summary')}"
            )
            pack_kinds = context_pack_ref_summary(packet.get("context_pack_refs"))
            if pack_kinds:
                summary += f" | packs: {pack_kinds}"
            lines.append(summary)
    return "\n".join(lines)


def _append_runtime_markdown(lines: list[str], runtime: object) -> None:
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
