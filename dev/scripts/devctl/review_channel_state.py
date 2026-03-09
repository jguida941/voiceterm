"""Projection helpers for bridge-backed and event-backed review-channel state."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .common import display_path
from .review_channel import LaneAssignment, ensure_launcher_prereqs
from .review_channel_handoff import (
    BridgeSnapshot,
    bridge_liveness_to_dict,
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from .time_utils import utc_timestamp

DEFAULT_REVIEW_STATUS_DIR_REL = "dev/reports/review_channel/latest"


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


@dataclass(frozen=True)
class ReviewChannelStatusSnapshot:
    """Shared status-refresh result for read-only review consumers."""

    lanes: list[LaneAssignment]
    bridge_liveness: dict[str, object]
    warnings: list[str]
    errors: list[str]
    projection_paths: ReviewChannelProjectionPaths


def refresh_status_snapshot(
    *,
    repo_root: Path,
    bridge_path: Path,
    review_channel_path: Path,
    output_root: Path,
    execution_mode: str = "markdown-bridge",
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> ReviewChannelStatusSnapshot:
    """Refresh the latest review-channel projections for read-only consumers."""
    _, lanes = ensure_launcher_prereqs(
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        execution_mode=execution_mode,
    )
    snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
    bridge_liveness = bridge_liveness_to_dict(summarize_bridge_liveness(snapshot))
    merged_warnings = list(warnings or [])
    merged_errors = list(errors or [])
    codex_poll_state = str(bridge_liveness.get("codex_poll_state") or "unknown")
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    if codex_poll_state == "missing":
        merged_warnings.append(
            "Bridge liveness is missing: the bridge header does not expose a "
            "usable `Last Codex poll` timestamp yet."
        )
    elif codex_poll_state == "stale":
        merged_warnings.append(
            "Bridge liveness is stale: the latest Codex poll timestamp is "
            "older than the five-minute heartbeat contract."
        )
    elif codex_poll_state == "poll_due":
        merged_warnings.append(
            "Bridge liveness is due for refresh: the latest Codex poll "
            "timestamp is older than the 2-3 minute reviewer cadence but "
            "still within the five-minute heartbeat window."
        )
    elif overall_state == "waiting_on_peer":
        merged_warnings.append(
            "Bridge liveness is waiting_on_peer: the current bridge state "
            "still needs a fresh reviewer poll or complete Claude status/ACK "
            "state before the next cycle."
        )
    projection_paths = write_status_projection_bundle(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=output_root,
        lanes=lanes,
        bridge_liveness=bridge_liveness,
        warnings=merged_warnings,
        errors=merged_errors,
    )
    return ReviewChannelStatusSnapshot(
        lanes=lanes,
        bridge_liveness=bridge_liveness,
        warnings=merged_warnings,
        errors=merged_errors,
        projection_paths=projection_paths,
    )


def write_status_projection_bundle(
    *,
    repo_root: Path,
    bridge_path: Path,
    review_channel_path: Path,
    output_root: Path,
    lanes: list[LaneAssignment],
    bridge_liveness: dict[str, object],
    warnings: list[str],
    errors: list[str],
) -> ReviewChannelProjectionPaths:
    """Write bridge-backed status projections for operator/read-only consumers."""
    snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
    timestamp = utc_timestamp()
    review_state = _build_bridge_review_state(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        snapshot=snapshot,
        bridge_liveness=bridge_liveness,
        timestamp=timestamp,
        project_id=project_id_for_repo(repo_root),
        warnings=warnings,
        errors=errors,
    )
    agent_registry = build_agent_registry_from_lanes(
        lanes,
        timestamp=timestamp,
        provider_state={
            "codex": {
                "job_state": str(bridge_liveness.get("overall_state") or "unknown"),
                "waiting_on": (
                    "peer"
                    if str(bridge_liveness.get("overall_state") or "unknown")
                    == "waiting_on_peer"
                    else None
                ),
            },
            "claude": {"job_state": "assigned"},
        },
    )
    return write_projection_bundle(
        output_root=output_root,
        review_state=review_state,
        agent_registry=agent_registry,
        action="status",
        trace_events=[],
        full_extras={"bridge_liveness": bridge_liveness},
    )


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


def project_id_for_repo(repo_root: Path) -> str:
    """Build the stable repo identity used across review-channel artifacts."""
    digest = hashlib.sha256(str(repo_root.resolve()).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _build_bridge_review_state(
    *,
    repo_root: Path,
    bridge_path: Path,
    review_channel_path: Path,
    snapshot: BridgeSnapshot,
    bridge_liveness: dict[str, object],
    timestamp: str,
    project_id: str,
    warnings: list[str],
    errors: list[str],
) -> dict[str, object]:
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    projection_ok = overall_state == "fresh" and not errors
    claude_status_present = bool(bridge_liveness.get("claude_status_present"))
    claude_status = _clean_section(snapshot.sections.get("Claude Status", ""))
    claude_ack = _clean_section(snapshot.sections.get("Claude Ack", ""))
    current_instruction = _clean_section(
        snapshot.sections.get("Current Instruction For Claude", "")
    )
    open_findings = _clean_section(snapshot.sections.get("Open Findings", ""))
    operator_status = (
        "waiting"
        if overall_state == "waiting_on_peer"
        else "warning"
        if overall_state == "stale"
        else "active"
    )
    return {
        "schema_version": 1,
        "command": "review-channel",
        "project_id": project_id,
        "timestamp": timestamp,
        "ok": projection_ok,
        "review": {
            "plan_id": "MP-355",
            "controller_run_id": None,
            "session_id": "markdown-bridge",
            "surface_mode": "markdown-bridge",
            "active_lane": "review",
            "refresh_seq": 1,
            "bridge_path": display_path(bridge_path, repo_root=repo_root),
            "review_channel_path": display_path(review_channel_path, repo_root=repo_root),
        },
        "agents": [
            {
                "agent_id": "codex",
                "display_name": "Codex",
                "role": "reviewer",
                "status": overall_state,
                "capabilities": ["review", "planning", "coordination"],
                "lane": "codex",
            },
            {
                "agent_id": "claude",
                "display_name": "Claude",
                "role": "implementer",
                "status": "active" if claude_status_present else "waiting",
                "capabilities": ["implementation", "fixes", "handoff"],
                "lane": "claude",
            },
            {
                "agent_id": "operator",
                "display_name": "Operator",
                "role": "approver",
                "status": operator_status,
                "capabilities": ["approval", "launch", "rollover"],
                "lane": "operator",
            },
        ],
        "packets": [],
        "queue": {
            "pending_total": 0,
            "pending_codex": 0,
            "pending_claude": 0,
            "pending_operator": 0,
            "stale_packet_count": 0,
        },
        "bridge": {
            "last_codex_poll_utc": snapshot.metadata.get("last_codex_poll_utc"),
            "last_codex_poll_age_seconds": bridge_liveness.get(
                "last_codex_poll_age_seconds"
            ),
            "last_worktree_hash": snapshot.metadata.get("last_non_audit_worktree_hash"),
            "open_findings": open_findings,
            "current_instruction": current_instruction,
            "claude_status": claude_status,
            "claude_ack": claude_ack,
            "last_reviewed_scope": _clean_section(
                snapshot.sections.get("Last Reviewed Scope", "")
            ),
        },
        "warnings": warnings,
        "errors": errors,
    }


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
        "queue": queue,
        "bridge": {
            "last_codex_poll_utc": bridge.get("last_codex_poll_utc"),
            "last_worktree_hash": bridge.get("last_worktree_hash"),
            "current_instruction": current_focus,
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
    lines.append("")
    lines.append("## Current Instruction")
    lines.append(_current_focus_line(review_state))
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
            lines.append(
                f"- {packet.get('packet_id')}: {packet.get('status')} | "
                f"{packet.get('from_agent')} -> {packet.get('to_agent')} | "
                f"{packet.get('summary')}"
            )
    return "\n".join(lines)


def _current_focus_line(review_state: dict[str, object]) -> str:
    bridge = review_state.get("bridge", {})
    if isinstance(bridge, dict):
        current_instruction = str(bridge.get("current_instruction") or "").strip()
        if current_instruction:
            return current_instruction
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


def _clean_section(raw: str) -> str:
    return raw.strip() or "(missing)"
