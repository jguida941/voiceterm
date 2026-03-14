"""Session-surface builders for the Operator Console."""

from __future__ import annotations

from dataclasses import dataclass

from dev.scripts.devctl.runtime import ReviewState

from ..core.models import AgentLaneData
from .session_trace_reader import SessionTraceSnapshot
from .session_builder_support import (
    age_label,
    extract_lane_agents,
    lane_state_label,
    preferred_terminal_text,
    registry_mode_label,
    render_registry_text,
    render_stats_text,
    trace_signal_lines,
    trimmed_block,
)

@dataclass(frozen=True)
class SessionSurfaceText:
    """Text payloads for the three session sub-panels."""

    terminal_text: str
    stats_text: str
    registry_text: str


def build_codex_session_surface(
    *,
    live_trace: SessionTraceSnapshot | None,
    lane: AgentLaneData | None,
    sections: dict[str, str],
    last_codex_poll: str | None,
    last_worktree_hash: str | None,
    review_contract: ReviewState | None,
) -> SessionSurfaceText:
    """Build the Codex terminal, stats, and registry panes."""
    if live_trace is not None:
        return _build_live_session_surface(
            lane_name="Codex",
            live_trace=live_trace,
            lane=lane,
            review_contract=review_contract,
            lane_agents=extract_lane_agents(review_contract, lane_name="codex"),
            fallback_lines=(
                ("last_poll", last_codex_poll or "(unknown)"),
                ("worktree_hash", last_worktree_hash or "(unknown)"),
            ),
        )

    return _build_bridge_session_surface(
        lane_name="Codex",
        lane=lane,
        review_contract=review_contract,
        lane_agents=extract_lane_agents(review_contract, lane_name="codex"),
        terminal_blocks=(
            ("poll_status", sections.get("Poll Status", "(missing)")),
            ("current_verdict", sections.get("Current Verdict", "(missing)")),
            ("open_findings", sections.get("Open Findings", "(missing)")),
        ),
        stats_lines=(
            ("last_poll", last_codex_poll or "(unknown)"),
            ("worktree_hash", last_worktree_hash or "(unknown)"),
        ),
    )


def build_claude_session_surface(
    *,
    live_trace: SessionTraceSnapshot | None,
    lane: AgentLaneData | None,
    sections: dict[str, str],
    review_contract: ReviewState | None,
) -> SessionSurfaceText:
    """Build the Claude terminal, stats, and registry panes."""
    if live_trace is not None:
        return _build_live_session_surface(
            lane_name="Claude",
            live_trace=live_trace,
            lane=lane,
            review_contract=review_contract,
            lane_agents=extract_lane_agents(review_contract, lane_name="claude"),
            fallback_lines=(),
        )

    return _build_bridge_session_surface(
        lane_name="Claude",
        lane=lane,
        review_contract=review_contract,
        lane_agents=extract_lane_agents(review_contract, lane_name="claude"),
        terminal_blocks=(
            (
                "current_instruction",
                sections.get("Current Instruction For Claude", "(missing)"),
            ),
            ("claude_status", sections.get("Claude Status", "(missing)")),
            ("claude_questions", sections.get("Claude Questions", "(missing)")),
            ("claude_ack", sections.get("Claude Ack", "(missing)")),
        ),
        stats_lines=(),
    )


def build_cursor_session_surface(
    *,
    live_trace: SessionTraceSnapshot | None,
    lane: AgentLaneData | None,
    sections: dict[str, str],
    review_contract: ReviewState | None,
) -> SessionSurfaceText:
    """Build the Cursor terminal, stats, and registry panes."""
    if live_trace is not None:
        return _build_live_session_surface(
            lane_name="Cursor",
            live_trace=live_trace,
            lane=lane,
            review_contract=review_contract,
            lane_agents=extract_lane_agents(review_contract, lane_name="cursor"),
            fallback_lines=(),
        )

    return _build_bridge_session_surface(
        lane_name="Cursor",
        lane=lane,
        review_contract=review_contract,
        lane_agents=extract_lane_agents(review_contract, lane_name="cursor"),
        terminal_blocks=(
            ("cursor_status", sections.get("Cursor Status", "(missing)")),
            ("cursor_focus", sections.get("Cursor Focus", "(missing)")),
        ),
        stats_lines=(),
    )


def _build_live_session_surface(
    *,
    lane_name: str,
    live_trace: SessionTraceSnapshot,
    lane: AgentLaneData | None,
    review_contract: ReviewState | None,
    lane_agents: tuple[object, ...],
    fallback_lines: tuple[tuple[str, str], ...],
) -> SessionSurfaceText:
    terminal_text = preferred_terminal_text(live_trace)

    stats_lines = [
        ("source", "live session trace"),
        ("session_name", live_trace.session_name),
        ("capture_mode", live_trace.capture_mode or "terminal-script"),
        ("prepared_at", live_trace.prepared_at or "(unknown)"),
        ("updated_at", live_trace.updated_at or "(unknown)"),
        ("trace_age", age_label(live_trace.updated_at)),
        ("lane_state", lane_state_label(lane)),
    ]
    if live_trace.worker_budget is not None:
        stats_lines.append(("worker_budget", str(live_trace.worker_budget)))
    if live_trace.lane_count is not None:
        stats_lines.append(("declared_lanes", str(live_trace.lane_count)))

    signal_source = "\n".join(
        text
        for text in (live_trace.screen_text, live_trace.history_text)
        if text.strip()
    )
    signal_lines = trace_signal_lines(signal_source or terminal_text)
    for label, value in fallback_lines:
        stats_lines.append((label, value))
    stats_lines.extend(signal_lines)
    _append_attention_stats(stats_lines, review_contract)
    stats_lines.append(
        ("registry_mode", registry_mode_label(review_contract, live_trace))
    )
    stats_lines.append(("log_path", live_trace.log_path))

    screen_lines = trimmed_block(terminal_text, max_lines=14)
    stats_lines.append(("screen_snapshot", "\n".join(screen_lines)))

    return SessionSurfaceText(
        terminal_text=terminal_text,
        stats_text=render_stats_text(stats_lines),
        registry_text=render_registry_text(
            lane_name=lane_name,
            lane_agents=lane_agents,
            review_contract=review_contract,
        ),
    )


def _build_bridge_session_surface(
    *,
    lane_name: str,
    lane: AgentLaneData | None,
    review_contract: ReviewState | None,
    lane_agents: tuple[object, ...],
    terminal_blocks: tuple[tuple[str, str], ...],
    stats_lines: tuple[tuple[str, str], ...],
) -> SessionSurfaceText:
    review = review_contract.review if review_contract is not None else None

    terminal_lines = [
        "live_terminal: unavailable",
        "mode: bridge/projection fallback",
        "",
    ]
    for heading, body in terminal_blocks:
        terminal_lines.append(f"{heading}:")
        terminal_lines.extend(trimmed_block(body, max_lines=18))
        terminal_lines.append("")

    rendered_stats = [
        ("source", "review-channel projection + markdown bridge"),
        (
            "surface_mode",
            review.surface_mode if review is not None else "markdown-bridge",
        ),
        ("session_id", review.session_id if review is not None else "markdown-bridge"),
        ("active_lane", review.active_lane if review is not None else "review"),
        ("lane_state", lane_state_label(lane)),
        *stats_lines,
        (
            "registry_mode",
            "runtime review contract only"
            if review_contract is not None and review_contract.registry.agents
            else "repo projection only",
        ),
    ]
    _append_attention_stats(rendered_stats, review_contract)

    return SessionSurfaceText(
        terminal_text="\n".join(line for line in terminal_lines if line is not None).strip(),
        stats_text=render_stats_text(rendered_stats),
        registry_text=render_registry_text(
            lane_name=lane_name,
            lane_agents=lane_agents,
            review_contract=review_contract,
        ),
    )


def _append_attention_stats(
    stats_lines: list[tuple[str, str]],
    review_contract: ReviewState | None,
) -> None:
    attention = review_contract.attention if review_contract is not None else None
    if attention is None or attention.status == "healthy":
        return
    stats_lines.append(("attention_status", attention.status))
    stats_lines.append(("attention_summary", attention.summary))
    if attention.recommended_command:
        stats_lines.append(("attention_command", attention.recommended_command))
