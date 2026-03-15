"""Projection bundle writers for review-channel state surfaces."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .core import LaneAssignment
from .context_refs import (
    context_pack_ref_summary,
    normalize_context_pack_refs,
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
    current_focus = bridge.get("current_instruction") or _current_focus_line(review_state)
    return {
        "schema_version": 1,
        "command": "review-channel",
        "timestamp": review_state.get("timestamp"),
        "ok": review_state.get("ok"),
        "review": review_state.get("review"),
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
    lines.append("")
    lines.append("## Current Instruction")
    lines.append(_current_focus_line(review_state))
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


def _current_focus_line(review_state: dict[str, object]) -> str:
    bridge = review_state.get("bridge", {})
    if isinstance(bridge, dict):
        current_instruction = str(bridge.get("current_instruction") or "").strip()
        if current_instruction:
            return current_instruction
    queue = review_state.get("queue", {})
    if isinstance(queue, dict):
        derived_next_instruction = str(
            queue.get("derived_next_instruction") or ""
        ).strip()
        if derived_next_instruction:
            return derived_next_instruction
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return "(missing)"
    pending_packet = next(
        (
            packet
            for packet in packets
            if isinstance(packet, dict) and packet.get("status") == "pending"
        ),
        None,
    )
    if isinstance(pending_packet, dict):
        summary = str(pending_packet.get("summary") or "").strip()
        if summary:
            return summary
    latest_packet = packets[0] if packets else None
    if isinstance(latest_packet, dict):
        summary = str(latest_packet.get("summary") or "").strip()
        if summary:
            return summary
    return "(missing)"
