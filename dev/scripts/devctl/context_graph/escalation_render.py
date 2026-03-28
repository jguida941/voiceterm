"""Markdown rendering helpers for bounded context-escalation packets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PacketRenderPayload:
    """Compact input bundle for packet markdown rendering."""

    trigger: str
    query_terms: tuple[str, ...]
    canonical_refs: tuple[str, ...]
    matched_nodes: int
    edge_count: int
    guidance_lines: tuple[str, ...] = ()
    decision_lines: tuple[str, ...] = ()
    history_lines: tuple[str, ...] = ()
    watchdog_lines: tuple[str, ...] = ()
    reliability_lines: tuple[str, ...] = ()
    quality_lines: tuple[str, ...] = ()


def render_packet_markdown(payload: PacketRenderPayload) -> str:
    """Render one bounded prompt-safe context recovery packet."""
    lines = [
        "## Context Recovery Packet",
        "",
        f"- Trigger: `{payload.trigger}`",
        "- Query terms: " + ", ".join(f"`{term}`" for term in payload.query_terms),
        f"- Graph matches: nodes={payload.matched_nodes}, edges={payload.edge_count}",
        "- Canonical refs:",
    ]
    for ref in payload.canonical_refs:
        lines.append(f"  - `{ref}`")
    _append_section(
        lines,
        title="## Probe Guidance",
        intro=(
            "Treat these probe-backed remediation hints as the default repair "
            "plan unless you can justify waiving them."
        ),
        entries=payload.guidance_lines,
    )
    _append_section(
        lines,
        title="## Decision Constraints",
        intro=(
            "These decision-mode constraints gate how much of the proposed fix "
            "may be auto-applied versus escalated for approval."
        ),
        entries=payload.decision_lines,
    )
    _append_section(
        lines,
        title="## Recent Fix History",
        intro=(
            "Use these adjudicated recent outcomes to reuse proven fixes and "
            "avoid repeating recently waived or deferred patterns."
        ),
        entries=payload.history_lines,
    )
    _append_section(
        lines,
        title="## Watchdog Episode Digest",
        intro="Recent guarded-coding trends relevant to this scope:",
        entries=payload.watchdog_lines,
    )
    _append_section(
        lines,
        title="## Command Reliability Signals",
        intro="Recent command/runtime reliability metrics relevant to this scope:",
        entries=payload.reliability_lines,
    )
    _append_section(
        lines,
        title="## Repo Quality Feedback",
        intro="Latest governance-quality recommendations relevant to this scope:",
        entries=payload.quality_lines,
    )
    lines.extend(
        [
            "",
            (
                "Read these refs before editing outside the current read set or "
                "when blast radius is unclear."
            ),
        ]
    )
    return "\n".join(lines)


def append_compact_context_packet_markdown(
    text: str,
    packet: ContextEscalationPacket | None,
    *,
    max_refs: int = 3,
) -> str:
    """Append a flat markdown summary suitable for fixed-section bridge writes."""
    base_text = str(text or "").strip()
    compact_markdown = compact_context_packet_markdown(packet, max_refs=max_refs)
    if not compact_markdown:
        return base_text
    if not base_text:
        return compact_markdown
    return f"{base_text}\n{compact_markdown}"


def compact_context_packet_markdown(
    packet: ContextEscalationPacket | None,
    *,
    max_refs: int = 3,
) -> str:
    """Render one compact packet summary without nested markdown headings."""
    if packet is None:
        return ""

    query_terms = ", ".join(f"`{term}`" for term in packet.query_terms)
    lines = [
        "- Context packet: "
        f"trigger `{packet.trigger}`; query terms: {query_terms or '`n/a`'}",
    ]
    refs = tuple(ref for ref in packet.canonical_refs[:max_refs] if ref)
    if refs:
        lines.append("- Canonical refs:")
        for ref in refs:
            lines.append(f"  - `{ref}`")
    return "\n".join(lines)


def _append_section(
    lines: list[str],
    *,
    title: str,
    intro: str,
    entries: tuple[str, ...],
) -> None:
    if not entries:
        return
    lines.extend(["", title, "", intro])
    for entry in entries:
        lines.append(f"- {entry}")
