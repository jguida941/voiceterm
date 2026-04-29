"""Read-only Claude loop surface backed by DashboardSnapshot v3."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...review_channel.event_store import resolve_artifact_paths
from ...runtime.instruction_authority import (
    DEFAULT_INSTRUCTION_TRANSITIONS_REL,
    instruction_transition_receipt_from_mapping,
)
from ...runtime.dashboard_snapshot_authority import build_dashboard_snapshot


def run(args) -> int:
    """Render one or more Claude-loop snapshots from typed dashboard state."""
    if bool(getattr(args, "follow", False)):
        return _run_follow(args)
    payload = build_claude_loop_snapshot(args)
    print(_render(args, payload))
    return 0


def build_claude_loop_snapshot(args) -> dict[str, Any]:
    """Return the bounded Claude-loop view over the shared dashboard contract."""
    repo_root = Path(getattr(args, "repo_root", None) or REPO_ROOT).resolve()
    dashboard = build_dashboard_snapshot(
        repo_root=repo_root,
        view="overview",
        role="dashboard",
    )
    review_state = _load_review_state(repo_root)
    now = dict(dashboard.get("now", {}))
    now["instruction_provenance"] = _current_instruction_provenance(
        dashboard=dashboard,
        review_state=review_state,
    )
    now["priority_decision"] = _current_priority_decision(review_state)
    payload: dict[str, Any] = {"schema_version": 1, "command": "claude-loop"}
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
            ("pending_packets", _claude_packets(dashboard.get("pending_packets"))),
        )
    )
    payload.update(
        (
            ("active_codex_sessions", dashboard.get("active_codex_sessions", {})),
            ("agent_mind", dashboard.get("agent_mind", {})),
            ("system_topology", dashboard.get("system_topology", {})),
        )
    )
    return payload


def _claude_packets(raw_packets: object) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    if not isinstance(raw_packets, list):
        return packets
    for packet in raw_packets:
        if not isinstance(packet, dict):
            continue
        if str(packet.get("to_agent") or "").strip() != "claude":
            continue
        packets.append(
            dict(
                (
                    ("packet_id", packet.get("packet_id")),
                    ("from_agent", packet.get("from_agent")),
                    ("summary", packet.get("summary")),
                    ("status", packet.get("status")),
                    ("requested_action", packet.get("requested_action")),
                    ("policy_hint", packet.get("policy_hint")),
                    ("target_ref", packet.get("target_ref")),
                    ("posted_at", packet.get("posted_at")),
                )
            )
        )
    return packets


def _load_review_state(repo_root: Path) -> dict[str, Any]:
    try:
        artifact_paths = resolve_artifact_paths(repo_root=repo_root)
        path = Path(artifact_paths.projections_root) / "review_state.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _current_priority_decision(review_state: dict[str, Any]) -> dict[str, Any]:
    queue = _mapping(review_state.get("queue"))
    decision = _mapping(queue.get("instruction_priority_decision"))
    if decision:
        return dict(decision)
    source = _mapping(queue.get("derived_next_instruction_source"))
    return dict(_mapping(source.get("priority_decision")))


def _current_instruction_provenance(
    *,
    dashboard: dict[str, Any],
    review_state: dict[str, Any],
) -> dict[str, Any]:
    queue = _mapping(review_state.get("queue"))
    source = _mapping(queue.get("derived_next_instruction_source"))
    provenance = _mapping(source.get("provenance"))
    if provenance:
        return dict(provenance)

    control_plane = _mapping(dashboard.get("control_plane"))
    coordination = _mapping(control_plane.get("coordination"))
    active_target = _mapping(coordination.get("active_target"))
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


def _run_follow(args) -> int:
    interval_seconds = _parse_interval_seconds(getattr(args, "interval", "5"))
    max_snapshots = getattr(args, "max_follow_snapshots", None)
    count = 0
    try:
        while True:
            count += 1
            payload = build_claude_loop_snapshot(args)
            payload["follow"] = dict(
                enabled=True,
                snapshot_seq=count,
                interval_seconds=interval_seconds,
            )
            print(_render(args, payload))
            print("", flush=True)
            if max_snapshots is not None and count >= int(max_snapshots):
                return 0
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        return 0


def _render(args, payload: dict[str, Any]) -> str:
    fmt = str(getattr(args, "format", "md") or "md")
    if fmt == "json":
        return json.dumps(payload, indent=2)
    return _render_markdown(payload)


def _render_markdown(payload: dict[str, Any]) -> str:
    now = payload.get("now", {})
    ack = payload.get("ack_freshness", {})
    packets = payload.get("pending_packets", [])
    codex = payload.get("active_codex_sessions", {})
    lines = ["# Claude Loop", ""]
    lines.append(f"- owner: {now.get('owner', 'n/a')}")
    lines.append(f"- next_action: {now.get('next_action', 'n/a')}")
    lines.append(f"- top_blocker: {now.get('top_blocker', 'none')}")
    provenance = _mapping(now.get("instruction_provenance"))
    if provenance:
        source_file = provenance.get("source_file", "n/a")
        source_line = provenance.get("source_line", 0)
        lines.append(f"- instruction_source: {source_file}:{source_line}")
    decision = _mapping(now.get("priority_decision"))
    if decision:
        lines.append(
            "- priority_decision: "
            f"{decision.get('rule_id', 'n/a')} -> "
            f"{decision.get('selected_instruction_id', 'n/a')}"
        )
    if isinstance(ack, dict) and ack.get("available"):
        label = "current" if ack.get("is_current") else "stale"
        lines.append(f"- implementer_ack: {label}")
    if isinstance(codex, dict):
        lines.append(
            f"- codex_sessions: {codex.get('live_count', 0)} live / "
            f"{codex.get('count', 0)} registered"
        )
    lines.append("")
    lines.append("## Pending Packets")
    if not packets:
        lines.append("")
        lines.append("- none")
        return "\n".join(lines)
    lines.append("")
    for packet in packets:
        lines.append(
            f"- `{packet.get('packet_id')}` {packet.get('requested_action')}: "
            f"{packet.get('summary')}"
        )
    return "\n".join(lines)


def _parse_interval_seconds(raw: object) -> float:
    text = str(raw or "5").strip().lower()
    multiplier = 1.0
    if text.endswith("ms"):
        multiplier = 0.001
        text = text[:-2]
    elif text.endswith("s"):
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 60.0
        text = text[:-1]
    try:
        value = float(text)
    except ValueError:
        value = 5.0
    return max(0.1, value * multiplier)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


__all__ = ["build_claude_loop_snapshot", "run"]
