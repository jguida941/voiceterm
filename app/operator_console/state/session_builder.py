"""Session-surface builders for the Operator Console."""

from __future__ import annotations

from .models import AgentLaneData
from .session_trace_reader import SessionTraceSnapshot
from .value_coercion import safe_text


def build_codex_session_text(
    *,
    live_trace: SessionTraceSnapshot | None,
    lane: AgentLaneData | None,
    sections: dict[str, str],
    last_codex_poll: str | None,
    last_worktree_hash: str | None,
    review_projection: dict[str, object] | None,
) -> str:
    """Build the Codex session pane text from bridge and projection data."""
    if live_trace is not None:
        return _build_live_session_text(
            lane_name="Codex",
            live_trace=live_trace,
            lane=lane,
            agent_lines=_format_agent_lines(review_projection, lane_name="codex"),
        )
    return _build_lane_session_text(
        lane=lane,
        lane_name="Codex",
        state_lines=(
            ("Last Poll", last_codex_poll or "(unknown)"),
            ("Worktree Hash", last_worktree_hash or "(unknown)"),
        ),
        primary_blocks=(
            ("Poll Status", sections.get("Poll Status", "(missing)")),
            ("Current Verdict", sections.get("Current Verdict", "(missing)")),
            ("Open Findings", sections.get("Open Findings", "(missing)")),
        ),
        agent_lines=_format_agent_lines(review_projection, lane_name="codex"),
        review_projection=review_projection,
    )


def build_claude_session_text(
    *,
    live_trace: SessionTraceSnapshot | None,
    lane: AgentLaneData | None,
    sections: dict[str, str],
    review_projection: dict[str, object] | None,
) -> str:
    """Build the Claude session pane text from bridge and projection data."""
    if live_trace is not None:
        return _build_live_session_text(
            lane_name="Claude",
            live_trace=live_trace,
            lane=lane,
            agent_lines=_format_agent_lines(review_projection, lane_name="claude"),
        )
    return _build_lane_session_text(
        lane=lane,
        lane_name="Claude",
        state_lines=(),
        primary_blocks=(
            (
                "Current Instruction",
                sections.get("Current Instruction For Claude", "(missing)"),
            ),
            ("Claude Status", sections.get("Claude Status", "(missing)")),
            ("Claude Questions", sections.get("Claude Questions", "(missing)")),
            ("Claude Ack", sections.get("Claude Ack", "(missing)")),
        ),
        agent_lines=_format_agent_lines(review_projection, lane_name="claude"),
        review_projection=review_projection,
    )


def _build_lane_session_text(
    *,
    lane: AgentLaneData | None,
    lane_name: str,
    state_lines: tuple[tuple[str, str], ...],
    primary_blocks: tuple[tuple[str, str], ...],
    agent_lines: tuple[str, ...],
    review_projection: dict[str, object] | None,
) -> str:
    review = review_projection.get("review") if isinstance(review_projection, dict) else None
    if not isinstance(review, dict):
        review = {}

    lines = [
        f"{lane_name.upper()} SESSION",
        "source: review-channel projection + markdown bridge",
        "live_terminal: unavailable (no PTY trace is projected into the current review-channel payload)",
        f"surface_mode: {safe_text(review.get('surface_mode')) or 'markdown-bridge'}",
        f"session_id: {safe_text(review.get('session_id')) or 'markdown-bridge'}",
        f"active_lane: {safe_text(review.get('active_lane')) or 'review'}",
    ]
    if lane is not None:
        lines.append(f"lane_state: {lane.state_label} [{lane.status_hint}]")
    for label, value in state_lines:
        lines.append(f"{_slug(label)}: {_one_line(value)}")

    for heading, body in primary_blocks:
        lines.append("")
        lines.append(f"{_slug(heading)}:")
        lines.extend(_trimmed_block(body))

    lines.append("")
    lines.append("registry_agents:")
    if agent_lines:
        lines.extend(agent_lines)
    else:
        lines.append("- no agent-registry rows are available for this lane yet")
    return "\n".join(lines)


def _build_live_session_text(
    *,
    lane_name: str,
    live_trace: SessionTraceSnapshot,
    lane: AgentLaneData | None,
    agent_lines: tuple[str, ...],
) -> str:
    lines = [
        f"{lane_name.upper()} SESSION",
        "source: live session trace",
        f"session_name: {live_trace.session_name}",
        f"capture_mode: {live_trace.capture_mode or 'terminal-script'}",
        f"prepared_at: {live_trace.prepared_at or '(unknown)'}",
        f"updated_at: {live_trace.updated_at or '(unknown)'}",
        f"log_path: {live_trace.log_path}",
    ]
    if lane is not None:
        lines.append(f"lane_state: {lane.state_label} [{lane.status_hint}]")
    lines.append("")
    lines.append("tail:")
    lines.extend(_trimmed_block(live_trace.tail_text, max_lines=120))
    if agent_lines:
        lines.append("")
        lines.append("registry_agents:")
        lines.extend(agent_lines)
    return "\n".join(lines)


def _format_agent_lines(
    review_projection: dict[str, object] | None,
    *,
    lane_name: str,
    max_agents: int = 8,
) -> tuple[str, ...]:
    if not isinstance(review_projection, dict):
        return ()
    registry = review_projection.get("agent_registry")
    if not isinstance(registry, dict):
        return ()
    agents = registry.get("agents")
    if not isinstance(agents, list):
        return ()

    lane_agents: list[dict[str, object]] = []
    for item in agents:
        if not isinstance(item, dict):
            continue
        lane = safe_text(item.get("lane")) or safe_text(item.get("provider"))
        if lane != lane_name:
            continue
        lane_agents.append(item)

    if not lane_agents:
        return ()

    lines: list[str] = []
    for item in lane_agents[:max_agents]:
        agent_id = safe_text(item.get("display_name")) or safe_text(item.get("agent_id")) or "(unknown-agent)"
        job_state = safe_text(item.get("job_state")) or "unknown"
        current_job = safe_text(item.get("current_job")) or "(no job recorded)"
        mp_scope = _clean_inline(safe_text(item.get("mp_scope")))
        worktree = _clean_inline(safe_text(item.get("worktree")))
        branch = _clean_inline(safe_text(item.get("branch")))
        lines.append(f"- {agent_id} [{job_state}] {current_job}")
        if mp_scope:
            lines.append(f"  scope: {mp_scope}")
        if worktree:
            lines.append(f"  worktree: {worktree}")
        if branch:
            lines.append(f"  branch: {branch}")

    remaining = len(lane_agents) - min(len(lane_agents), max_agents)
    if remaining > 0:
        plural = "agent" if remaining == 1 else "agents"
        lines.append(f"- ... {remaining} more {plural} in the registry")
    return tuple(lines)


def _trimmed_block(text: str, *, max_lines: int = 8) -> list[str]:
    cleaned = [line.rstrip() for line in text.splitlines()]
    visible = [line for line in cleaned if line.strip()]
    if not visible:
        return ["(empty)"]
    if len(visible) <= max_lines:
        return visible
    trimmed = visible[:max_lines]
    trimmed.append(f"... ({len(visible) - max_lines} more lines)")
    return trimmed


def _clean_inline(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().strip("`")
    return cleaned or None


def _slug(label: str) -> str:
    return label.strip().lower().replace(" ", "_")


def _one_line(text: str, *, max_len: int = 140) -> str:
    for line in text.splitlines():
        stripped = line.strip().lstrip("- ")
        if stripped:
            if len(stripped) <= max_len:
                return stripped
            return stripped[: max_len - 1] + "..."
    return "(empty)"
