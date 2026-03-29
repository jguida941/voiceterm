"""Shared helper functions for session surface text rendering."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from dev.scripts.devctl.runtime import (
    AgentRegistryEntryState,
    ReviewState,
)

from ..core.models import AgentLaneData
from .session_trace_reader import SessionTraceSnapshot

_TOKENS_RE = re.compile(r"([↑↓])\s*([0-9][0-9.,kK]*)\s*tokens", re.IGNORECASE)
_THOUGHT_RE = re.compile(r"(thought for\s*[0-9]+\s*[smh])", re.IGNORECASE)
_CONTEXT_RE = re.compile(
    r"context\s*left\s*until\s*auto-compact:\s*([0-9]+%)",
    re.IGNORECASE,
)


def render_stats_text(rows: list[tuple[str, str]]) -> str:
    lines: list[str] = []
    for label, value in rows:
        cleaned = value.strip() or "(empty)"
        lines.append(f"{label}: {cleaned}")
    return "\n".join(lines)


def render_registry_text(
    *,
    lane_name: str,
    lane_agents: tuple[AgentRegistryEntryState, ...],
    review_contract: ReviewState | None,
) -> str:
    registry = review_contract.registry if review_contract is not None else None
    has_registry = registry is not None and bool(registry.agents)
    registry_timestamp = registry.timestamp if registry is not None else None
    total_agents = len(lane_agents)
    state_counts = state_counts_for_agents(lane_agents)

    lines = [
        f"source: {'runtime review contract' if has_registry else 'none'}",
        f"updated_at: {registry_timestamp or '(unknown)'}",
        (
            "summary: "
            f"{total_agents} total | "
            f"{state_counts.get('fresh', 0)} fresh | "
            f"{state_counts.get('active', 0)} active | "
            f"{state_counts.get('assigned', 0)} assigned | "
            f"{state_counts.get('stale', 0)} stale"
        ),
        "",
    ]

    if not lane_agents:
        lines.append(
            f"no {lane_name.lower()} lane agents are visible in the current projection"
        )
        return "\n".join(lines)

    for item in lane_agents:
        agent_id = item.display_name or item.agent_id or "(unknown-agent)"
        job_state = item.job_state or "unknown"
        current_job = item.current_job or "(no job recorded)"
        mp_scope = clean_inline(item.mp_scope)
        worktree = clean_inline(item.worktree)
        branch = clean_inline(item.branch)
        updated_at = item.updated_at
        lines.append(f"- {agent_id} [{job_state}] {current_job}")
        if mp_scope:
            lines.append(f"  scope: {mp_scope}")
        if worktree:
            lines.append(f"  worktree: {worktree}")
        if branch:
            lines.append(f"  branch: {branch}")
        if updated_at:
            lines.append(f"  updated_at: {updated_at}")
    return "\n".join(lines)


def extract_lane_agents(
    review_contract: ReviewState | None,
    *,
    lane_name: str,
) -> tuple[AgentRegistryEntryState, ...]:
    if review_contract is None:
        return ()
    return review_contract.lane_agents(lane_name)


def trace_signal_lines(text: str) -> list[tuple[str, str]]:
    lowered = text.lower()
    rows: list[tuple[str, str]] = []

    token_match = None
    for token_match in _TOKENS_RE.finditer(text):
        pass
    if token_match is not None:
        rows.append(("recent_tokens", f"{token_match.group(1)} {token_match.group(2)} tokens"))

    thought_match = None
    for thought_match in _THOUGHT_RE.finditer(lowered):
        pass
    if thought_match is not None:
        rows.append(("recent_thought", thought_match.group(1)))

    context_match = None
    for context_match in _CONTEXT_RE.finditer(lowered):
        pass
    if context_match is not None:
        rows.append(("context_left", context_match.group(1)))

    readable_lines = [line for line in text.splitlines() if line.strip()]
    rows.append(("history_lines", str(len(readable_lines))))
    return rows


def state_counts_for_agents(
    lane_agents: tuple[AgentRegistryEntryState, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in lane_agents:
        state = item.job_state or "unknown"
        counts[state] = counts.get(state, 0) + 1
    return counts


def registry_mode_label(
    review_contract: ReviewState | None,
    live_trace: SessionTraceSnapshot,
) -> str:
    del live_trace
    if review_contract is None or not review_contract.registry.agents:
        return "live trace only"
    return "runtime review contract (can lag the live terminal)"


def lane_state_label(lane: AgentLaneData | None) -> str:
    if lane is None:
        return "(unknown)"
    return f"{lane.state_label} [{lane.status_hint}]"


def preferred_terminal_text(live_trace: SessionTraceSnapshot) -> str:
    screen_text = live_trace.screen_text.strip()
    if screen_text:
        return screen_text
    history_text = live_trace.history_text.strip()
    if history_text:
        return history_text
    return "(no readable terminal output yet)"


def age_label(iso_timestamp: str | None) -> str:
    if iso_timestamp is None:
        return "(unknown)"
    try:
        parsed = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    except ValueError:
        return iso_timestamp
    age_seconds = max(0, int((datetime.now(tz=timezone.utc) - parsed).total_seconds()))
    if age_seconds < 60:
        return f"{age_seconds}s ago"
    minutes, seconds = divmod(age_seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s ago"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m ago"


def trimmed_block(text: str, *, max_lines: int = 8) -> list[str]:
    cleaned = [line.rstrip() for line in text.splitlines()]
    visible = [line for line in cleaned if line.strip()]
    if not visible:
        return ["(empty)"]
    if len(visible) <= max_lines:
        return visible
    trimmed = visible[:max_lines]
    trimmed.append(f"... ({len(visible) - max_lines} more lines)")
    return trimmed


def clean_inline(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().strip("`")
    return cleaned or None
