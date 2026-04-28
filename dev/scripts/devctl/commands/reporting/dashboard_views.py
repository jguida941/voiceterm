"""Dashboard view-to-section policy."""

from __future__ import annotations

VIEW_SECTIONS: dict[str, frozenset[str]] = dict(
    overview=frozenset(),
    dev=frozenset({
        "repo", "now", "review", "workers", "plan", "findings",
        "reviewer_activity", "quality", "flow", "timeline", "summary",
        "coordination", "control_plane", "agent_mind", "session_outcomes",
        "ack_freshness", "active_codex_sessions", "system_topology",
    }),
    analytics=frozenset({
        "repo", "analytics", "timeline", "summary",
    }),
    quality=frozenset({
        "repo", "quality", "audit", "summary",
    }),
    audit=frozenset({
        "repo", "audit", "summary",
    }),
    publication=frozenset({
        "repo", "publication", "flow", "coordination", "control_plane", "summary",
        "session_outcomes", "ack_freshness",
    }),
    health=frozenset({
        "repo", "health", "review", "coordination", "control_plane",
        "reviewer_activity", "summary", "active_codex_sessions",
        "session_outcomes", "agent_mind", "ack_freshness",
    }),
)


__all__ = ["VIEW_SECTIONS"]
