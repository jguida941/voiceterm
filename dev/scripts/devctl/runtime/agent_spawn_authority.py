"""Typed agent-spawn authority for dead-peer detection and auto-resurrect.

Replaces bash-permission grants with typed-state authority. The reducer composes
agent-mind cursor staleness, continuation-anchor liveness, and a typed
LifetimeBypassMode receipt before returning any spawn action.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional

UTC = timezone.utc

from .collaboration_wake_contract import LoopAutonomyState
from .governed_exception_base import json_ready_dict
from .lifetime_bypass_mode import (
    BypassAuthorityScope,
    BypassReceipt,
    bypass_receipt_active,
    bypass_receipt_grants_scope,
)


@dataclass(frozen=True, slots=True)
class SpawnDeadAgentAction:
    target_actor_id: str
    target_role: str
    bypass_receipt_id: str
    continuation_anchor_packet_id: str
    staleness_seconds: int
    detected_at_utc: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return json_ready_dict(asdict(self))


def compute_spawn_authority(
    *,
    target_actor_id: str,
    target_role: str,
    agent_mind_cursor_age_seconds: int,
    continuation_anchor_live: bool,
    continuation_anchor_packet_id: str,
    bypass_receipt: Optional[BypassReceipt],
    loop_autonomy_state: LoopAutonomyState | Mapping[str, object] | None = None,
    staleness_threshold_seconds: int = 900,
) -> Optional[SpawnDeadAgentAction]:
    """Return typed spawn action only when all authority gates pass."""
    autonomy = _coerce_loop_autonomy(loop_autonomy_state)
    if autonomy is not None and not autonomy.loop_autonomy_ok:
        return None
    if agent_mind_cursor_age_seconds < staleness_threshold_seconds:
        return None
    if not continuation_anchor_live or not continuation_anchor_packet_id:
        return None
    if bypass_receipt is None:
        return None
    if not bypass_receipt_active(bypass_receipt):
        return None
    if not bypass_receipt_grants_scope(
        bypass_receipt, BypassAuthorityScope.AGENT_SPAWN_ONLY
    ):
        return None
    detected_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return SpawnDeadAgentAction(
        target_actor_id=target_actor_id,
        target_role=target_role,
        bypass_receipt_id=bypass_receipt.receipt_id,
        continuation_anchor_packet_id=continuation_anchor_packet_id,
        staleness_seconds=agent_mind_cursor_age_seconds,
        detected_at_utc=detected_at,
        reason=(
            "agent_mind_cursor_stale:"
            f"{agent_mind_cursor_age_seconds}s>=threshold:"
            f"{staleness_threshold_seconds}s; continuation_anchor:"
            f"{continuation_anchor_packet_id}; bypass_receipt:"
            f"{bypass_receipt.receipt_id}"
            + _loop_autonomy_reason(autonomy)
        ),
    )


def _coerce_loop_autonomy(
    value: LoopAutonomyState | Mapping[str, object] | None,
) -> LoopAutonomyState | None:
    if isinstance(value, LoopAutonomyState):
        return value
    return LoopAutonomyState.from_mapping(value)


def _loop_autonomy_reason(value: LoopAutonomyState | None) -> str:
    if value is None:
        return ""
    return (
        f"; loop_autonomy:{value.loop_wake_mode}"
        f"/driver:{value.loop_driver_agent or 'unknown'}"
    )


__all__ = [
    "SpawnDeadAgentAction",
    "compute_spawn_authority",
]
