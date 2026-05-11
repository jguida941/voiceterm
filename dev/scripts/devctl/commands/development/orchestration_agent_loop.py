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
) -> tuple[DevelopmentAgentLoopInput, ...]:
    rows: list[DevelopmentAgentLoopInput] = []
    for row in agent_loop_rows(review_state, dashboard=dashboard):
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
