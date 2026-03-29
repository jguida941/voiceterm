"""Shared bridge runtime state helpers for review-channel command flows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .attention import derive_bridge_attention
from .peer_liveness import STALE_PEER_RECOVERY


@dataclass(frozen=True)
class BridgeStateContext:
    repo_root: Path
    review_channel_path: Path
    bridge_path: Path
    status_dir: Path | None


@dataclass(frozen=True)
class BridgeStateResult:
    lanes: list
    bridge_liveness: dict[str, object]
    bridge_liveness_state: object
    codex_lanes: list
    claude_lanes: list
    cursor_lanes: list
    bridge_heartbeat_refresh: object
    reviewer_state_write: object


def enforce_bridge_launch_attention(
    *,
    action: str,
    bridge_actions: set[str],
    bridge_liveness: dict[str, object],
) -> None:
    if action not in bridge_actions:
        return
    attention = derive_bridge_attention(bridge_liveness)
    attention_status = str(attention.get("status", ""))
    recovery_entry = STALE_PEER_RECOVERY.get(attention_status, {})
    if str(recovery_entry.get("guard_behavior")) == "block_launch":
        raise ValueError(
            f"Peer-liveness guard blocks launch: {attention.get('summary', attention_status)}. "
            f"Recovery: {attention.get('recommended_action', 'inspect bridge state')}."
        )
