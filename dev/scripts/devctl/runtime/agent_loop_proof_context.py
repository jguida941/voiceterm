"""Protocol shared by agent-loop proof readers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from .agent_loop_operator_override import AgentLoopOperatorOverride


class LoopProofContext(Protocol):
    review_state: Mapping[str, object]
    actor: str
    role: str
    session: str
    master_plan: Mapping[str, object]
    clock: Mapping[str, object]
    attention: Mapping[str, object]
    loop_intent: str
    requested_plan_ref: str
    requested_packet_id: str
    operator_override: AgentLoopOperatorOverride


__all__ = ["LoopProofContext"]
