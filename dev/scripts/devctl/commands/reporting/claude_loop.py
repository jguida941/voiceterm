"""Read-only Claude loop surface backed by DashboardSnapshot v3."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
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
    return dict(
        schema_version=1,
        command="claude-loop",
        dashboard_contract_id=dashboard.get("contract_id"),
        dashboard_schema_version=dashboard.get("schema_version"),
        timestamp=dashboard.get("timestamp"),
        repo=dashboard.get("repo", {}),
        now=dashboard.get("now", {}),
        control_plane=dashboard.get("control_plane", {}),
        ack_freshness=dashboard.get("ack_freshness", {}),
        session_outcomes=dashboard.get("session_outcomes", {}),
        pending_packets=_claude_packets(dashboard.get("pending_packets")),
        active_codex_sessions=dashboard.get("active_codex_sessions", {}),
        agent_mind=dashboard.get("agent_mind", {}),
        system_topology=dashboard.get("system_topology", {}),
    )


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
                packet_id=packet.get("packet_id"),
                from_agent=packet.get("from_agent"),
                summary=packet.get("summary"),
                status=packet.get("status"),
                requested_action=packet.get("requested_action"),
                policy_hint=packet.get("policy_hint"),
                target_ref=packet.get("target_ref"),
                posted_at=packet.get("posted_at"),
            )
        )
    return packets


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


__all__ = ["build_claude_loop_snapshot", "run"]
