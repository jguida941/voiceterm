"""Rendering helpers for the ``agent-mind`` command.

Each renderer is a pure function over an :class:`AgentMindSlice` so the
test suite can feed hand-built slices without going through discovery or
JSONL parsing. Three surfaces are provided: compact terminal (default
for operators watching the command interactively), markdown (suitable
for bridge projection or chat pasting), and JSON (the machine-readable
schema that other tools consume).
"""

from __future__ import annotations

import json

from ...runtime.agent_mind_slice import AgentMindEvent, AgentMindSlice


def render_markdown(slice_: AgentMindSlice) -> str:
    """Markdown projection matching the BL-031 spec shape."""
    lines: list[str] = [f"# agent-mind ({slice_.agent_provider})", ""]
    lines.extend(_header_block(slice_))
    lines.append("")
    if not slice_.events:
        lines.append("_no decision-relevant events_")
        return "\n".join(lines)
    lines.append("## Recent decisions")
    lines.append("")
    for index, event in enumerate(slice_.events, start=1):
        lines.append(_format_event_line(index, event))
    return "\n".join(lines)


def render_terminal(slice_: AgentMindSlice) -> str:
    """Compact terminal variant — reuses the markdown body without headings."""
    header = (
        f"agent-mind {slice_.agent_provider} "
        f"events={slice_.event_count} cursor={slice_.last_cursor or '-'}"
    )
    lines: list[str] = [header, "-" * min(80, max(20, len(header)))]
    if slice_.latest_task_complete_at:
        lines.append(f"latest_task_complete: {slice_.latest_task_complete_at}")
    if slice_.latest_escalation_at:
        lines.append(f"latest_escalation: {slice_.latest_escalation_at}")
    if slice_.latest_error_at:
        lines.append(f"latest_error: {slice_.latest_error_at}")
    if not slice_.events:
        lines.append("(no decision-relevant events)")
        return "\n".join(lines)
    for event in slice_.events:
        kind = _kind_label(event)
        timestamp = event.timestamp or "-"
        lines.append(f"{timestamp} | {kind:12s} | {event.summary}")
    return "\n".join(lines)


def render_json(slice_: AgentMindSlice) -> str:
    """Full structured JSON serialization of the typed slice."""
    return json.dumps(slice_.to_dict(), indent=2, sort_keys=True)


def _header_block(slice_: AgentMindSlice) -> list[str]:
    lines = [
        f"- source: `{slice_.session_path}`",
        f"- session_id: `{slice_.session_id}`",
        f"- events: {slice_.event_count}",
    ]
    if slice_.latest_task_complete_at:
        lines.append(f"- latest_task_complete: `{slice_.latest_task_complete_at}`")
    if slice_.latest_escalation_at:
        lines.append(f"- latest_escalation: `{slice_.latest_escalation_at}`")
    if slice_.latest_error_at:
        lines.append(f"- latest_error: `{slice_.latest_error_at}`")
    peer_awareness = slice_.peer_awareness
    if peer_awareness:
        status = "due" if peer_awareness.get("due") else "current"
        lines.append(
            f"- peer_awareness: `{status}` ({peer_awareness.get('reason')})"
        )
        for command in peer_awareness.get("next_commands") or ():
            lines.append(f"- peer_awareness_next: `{command}`")
    lines.append(f"- cursor: `{slice_.last_cursor or '-'}`")
    return lines


def _format_event_line(index: int, event: AgentMindEvent) -> str:
    """Render one numbered entry in the markdown Recent decisions list."""
    kind = _kind_label(event)
    timestamp = event.timestamp or "-"
    if event.event_type == "event_msg:task_complete":
        return f"{index}. `{timestamp}` **TASK COMPLETE** {event.summary}".rstrip()
    if event.event_type == "response_item:function_call" and event.tool_name:
        if event.tool_command:
            return (
                f"{index}. `{timestamp}` [tool] {event.tool_name}: "
                f"{event.tool_command}"
            )
        return f"{index}. `{timestamp}` [tool] {event.tool_name}"
    return f"{index}. `{timestamp}` [{kind}] {event.summary}"


def _kind_label(event: AgentMindEvent) -> str:
    """Short badge used by terminal + markdown renderers."""
    if event.is_escalation:
        return "escalation"
    if event.is_error:
        return "error"
    kind = event.event_type or ""
    if kind == "response_item:reasoning":
        return "reasoning"
    if kind == "response_item:function_call":
        return "tool"
    if kind == "response_item:message":
        return "message"
    if kind == "event_msg:task_complete":
        return "task"
    if kind == "event_msg:agent_message":
        return "agent_msg"
    return "event"
