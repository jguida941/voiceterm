"""Typed-state dashboard renderers shared by terminal and markdown output."""

from __future__ import annotations

from typing import Any

from .helpers import _BOLD, _DIM, _GREEN, _RESET, _YELLOW


def render_typed_state_terminal(snapshot: dict[str, Any], lines: list[str]) -> None:
    """Typed runtime sections shared by CLI, desktop, and mobile dashboard users."""
    if not _has_typed_sections(snapshot):
        return

    ack = snapshot.get("ack_freshness", {})
    outcomes = snapshot.get("session_outcomes", {})
    codex = snapshot.get("active_codex_sessions", {})
    mind = snapshot.get("agent_mind", {})
    topology = snapshot.get("system_topology", {})

    lines.append(f"{_BOLD}TYPED STATE{_RESET}")
    if isinstance(ack, dict) and ack.get("available"):
        ack_color = _GREEN if ack.get("is_current") else _YELLOW
        lines.append(
            f"  Implementer ACK {ack_color}"
            f"{'current' if ack.get('is_current') else 'stale'}{_RESET} "
            f"{_DIM}{ack.get('implementer_ack_revision', '')}{_RESET}"
        )
    if isinstance(codex, dict):
        lines.append(
            f"  Codex sessions  {codex.get('live_count', 0)} live / "
            f"{codex.get('count', 0)} registered"
        )
    if isinstance(outcomes, dict):
        lines.append(f"  Session outcomes {outcomes.get('count', 0)} recorded")
    if isinstance(mind, dict):
        available = "available" if mind.get("available") else "missing"
        lines.append(
            f"  Agent mind      {available}; "
            f"{mind.get('event_count', 0)} events"
        )
    if isinstance(topology, dict):
        generated = "yes" if topology.get("generated_block_present") else "no"
        debt = "yes" if topology.get("snapshot_builder_debt_mentioned") else "no"
        lines.append(f"  System map      generated={generated}; debt_note={debt}")
    lines.append("")


def render_typed_state_markdown(snapshot: dict[str, Any], lines: list[str]) -> None:
    """Typed runtime sections shared by CLI, desktop, and mobile dashboard users."""
    if not _has_typed_sections(snapshot):
        return

    ack = snapshot.get("ack_freshness", {})
    outcomes = snapshot.get("session_outcomes", {})
    codex = snapshot.get("active_codex_sessions", {})
    mind = snapshot.get("agent_mind", {})
    topology = snapshot.get("system_topology", {})

    lines.append("## Typed State")
    lines.append("")
    if isinstance(ack, dict) and ack.get("available"):
        ack_label = "current" if ack.get("is_current") else "stale"
        lines.append(
            f"- **Implementer ACK**: {ack_label} "
            f"(`{ack.get('implementer_ack_revision', '')}`)"
        )
    if isinstance(codex, dict):
        lines.append(
            f"- **Codex sessions**: {codex.get('live_count', 0)} live / "
            f"{codex.get('count', 0)} registered"
        )
    if isinstance(outcomes, dict):
        lines.append(f"- **Session outcomes**: {outcomes.get('count', 0)} recorded")
    if isinstance(mind, dict):
        available = "available" if mind.get("available") else "missing"
        lines.append(
            f"- **Agent mind**: {available}; {mind.get('event_count', 0)} events"
        )
    if isinstance(topology, dict):
        generated = "yes" if topology.get("generated_block_present") else "no"
        debt = "yes" if topology.get("snapshot_builder_debt_mentioned") else "no"
        lines.append(f"- **System map**: generated={generated}; debt_note={debt}")
    lines.append("")


def _has_typed_sections(snapshot: dict[str, Any]) -> bool:
    sections = (
        snapshot.get("agent_mind"),
        snapshot.get("session_outcomes"),
        snapshot.get("ack_freshness"),
        snapshot.get("active_codex_sessions"),
        snapshot.get("system_topology"),
    )
    return any(isinstance(section, dict) and section for section in sections)


__all__ = ["render_typed_state_markdown", "render_typed_state_terminal"]
