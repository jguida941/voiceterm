"""Shared bridge runtime state helpers for review-channel command flows.

Launch-attention gating delegates to the shared turn-authority contract
(``turn_authority.is_attention_launch_blocked``) so blocking predicates
live in one place instead of being duplicated here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .attention import derive_bridge_attention
from .turn_authority import attention_block_detail, is_attention_launch_blocked


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
    """Block launch/rollover when the shared turn-authority contract says so.

    Derives attention status from the raw bridge liveness dict, then delegates
    the blocking decision to ``is_attention_launch_blocked`` so the predicate
    stays aligned with the turn-authority contract.
    """
    if action not in bridge_actions:
        return
    attention = derive_bridge_attention(bridge_liveness)
    attention_status = str(attention.get("status", ""))
    if is_attention_launch_blocked(attention_status):
        summary, recovery = attention_block_detail(attention_status)
        raise ValueError(
            f"Peer-liveness guard blocks launch: {summary}. "
            f"Recovery: {recovery}."
        )
