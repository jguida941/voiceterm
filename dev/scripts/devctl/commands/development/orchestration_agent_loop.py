"""Agent-loop signals consumed by `/develop` orchestration."""

from __future__ import annotations

from collections.abc import Mapping

from .models import DevelopmentAgentLoopInput, DevelopmentOrchestrationSignal
from .orchestration_agent_loop_parse import agent_loop_input
from .orchestration_agent_loop_rows import agent_loop_rows
from .orchestration_agent_loop_state import (
    agent_loop_rank,
    agent_loop_severity,
    agent_loop_signal_id,
    agent_loop_status,
    agent_loop_summary,
)

_AGENT_LOOP_LIMIT = 5


def agent_loop_inputs(
    review_state: Mapping[str, object],
    *,
    actor: str,
    dashboard: Mapping[str, object] | None = None,
    master_plan: Mapping[str, object] | None = None,
    loop_intent: str = "",
    requested_plan_ref: str = "",
    requested_packet_id: str = "",
    operator_override_requested: bool = False,
    operator_override_reason: str = "",
    operator_override_scope: str = "edit-only",
    operator_override_by: str = "operator",
) -> tuple[DevelopmentAgentLoopInput, ...]:
    rows: list[DevelopmentAgentLoopInput] = []
    for row in agent_loop_rows(
        review_state,
        dashboard=dashboard,
        master_plan=master_plan,
        operator_override_actor=actor,
        loop_intent=loop_intent,
        requested_plan_ref=requested_plan_ref,
        requested_packet_id=requested_packet_id,
        operator_override_requested=operator_override_requested,
        operator_override_reason=operator_override_reason,
        operator_override_scope=operator_override_scope,
        operator_override_by=operator_override_by,
    ):
        parsed = agent_loop_input(row)
        if parsed is not None:
            rows.append(parsed)
    ranked = sorted(rows, key=lambda row: agent_loop_rank(row, actor=actor))
    return tuple(ranked[:_AGENT_LOOP_LIMIT])


def agent_loop_signals(
    rows: tuple[DevelopmentAgentLoopInput, ...],
) -> tuple[DevelopmentOrchestrationSignal, ...]:
    signals: list[DevelopmentOrchestrationSignal] = []
    for row in rows:
        status = agent_loop_status(row)
        if status == "current":
            continue
        signals.append(
            DevelopmentOrchestrationSignal(
                source="agent-loop",
                signal_id=agent_loop_signal_id(row),
                status=status,
                summary=agent_loop_summary(row),
                source_surface="agent-loop",
                severity=agent_loop_severity(row, status),
                recommended_action=row.user_action or row.required_action or "inspect_agent_loop",
                closure_check_command=(
                    row.next_loop_command
                    or "python3 dev/scripts/devctl.py agent-loop --format json"
                ),
                source_command=row.next_loop_command,
                suggested_command=row.next_loop_command,
            )
        )
    return tuple(signals)


__all__ = ["agent_loop_inputs", "agent_loop_signals"]
