"""Collaboration sections for ``devctl develop`` markdown reports."""

from __future__ import annotations


def runtime_lines(runtime) -> list[str]:
    """Render typed runtime/work-board context."""
    if not isinstance(runtime, dict):
        return []
    lines = ["", "## Runtime", ""]
    lines.append(f"- actor: {runtime.get('actor') or '(none)'}")
    if runtime.get("actor_source"):
        lines.append(f"- actor_source: {runtime.get('actor_source')}")
    lines.append(f"- authority_source: {runtime.get('authority_source') or '(none)'}")
    lines.append(
        f"- coordination_topology: {runtime.get('coordination_topology') or '(none)'}"
    )
    lines.append(f"- authority_mode: {runtime.get('authority_mode') or '(none)'}")
    lines.append(f"- safe_to_fanout: {runtime.get('safe_to_fanout')}")
    lines.append(f"- actor_sync_status: {runtime.get('actor_sync_status') or '(none)'}")
    lines.append(
        f"- actor_pending_packet_count: {runtime.get('actor_pending_packet_count')}"
    )
    lines.append(f"- fresh_row_count: {runtime.get('fresh_row_count')}")
    lines.append(f"- stale_row_count: {runtime.get('stale_row_count')}")
    lines.append(f"- discovered_session_count: {runtime.get('discovered_session_count')}")
    lines.append(
        f"- unregistered_session_count: {runtime.get('unregistered_session_count')}"
    )
    if runtime.get("summary"):
        lines.append(f"- summary: {runtime.get('summary')}")
    for row in _rows(runtime):
        lines.append(_runtime_row_text(row))
    for row in _session_rows(runtime):
        lines.append(_session_row_text(row))
    return lines


def peer_mind_lines(peer_minds) -> list[str]:
    """Render peer-mind context while keeping authority limits explicit."""
    if not isinstance(peer_minds, list):
        return []
    lines = ["", "## Peer Mind", ""]
    lines.append("- authority_policy: auxiliary_context_only")
    lines.append("- coverage_scope: provider_latest_projection")
    if not peer_minds:
        lines.append("- peers: (none)")
        return lines
    for peer in peer_minds:
        if not isinstance(peer, dict):
            continue
        lines.extend(_peer_lines(peer))
    return lines


def orchestration_lines(orchestration) -> list[str]:
    """Render orchestration inputs consumed from existing typed surfaces."""
    if not isinstance(orchestration, dict):
        return []
    lines = ["", "## Orchestration Inputs", ""]
    lines.append(
        f"- authority_policy: {orchestration.get('authority_policy') or '(none)'}"
    )
    lines.append(f"- status: {orchestration.get('status') or '(none)'}")
    lines.append(f"- signal_count: {orchestration.get('signal_count')}")
    lines.append(
        f"- stale_projection_count: {orchestration.get('stale_projection_count')}"
    )
    lines.append(
        f"- missing_projection_count: {orchestration.get('missing_projection_count')}"
    )
    lines.append(
        f"- action_required_count: {orchestration.get('action_required_count')}"
    )
    if orchestration.get("summary"):
        lines.append(f"- summary: {orchestration.get('summary')}")
    for signal in _signal_rows(orchestration):
        lines.append(_signal_row_text(signal))
    for row in _agent_loop_rows(orchestration):
        lines.append(_agent_loop_row_text(row))
    return lines


def _runtime_row_text(row: dict[str, object]) -> str:
    packet_id = (
        row.get("attention_packet_id")
        or row.get("active_packet_id")
        or row.get("executing_packet_id")
        or "(none)"
    )
    session_id = _short(row.get("session_id"))
    return (
        f"- {row.get('actor_id') or '(actor)'} "
        f"{row.get('role') or '(role)'} "
        f"session={session_id or '(none)'} "
        f"status={row.get('status') or '(none)'} "
        f"confidence={row.get('confidence_class') or '(none)'} "
        f"idle={row.get('idle_seconds')}s "
        f"mutation={row.get('mutation_mode') or '(none)'} "
        f"packet={packet_id}"
    )


def _peer_lines(peer: dict[str, object]) -> list[str]:
    lines = [
        (
            f"- {peer.get('provider') or '(peer)'}: "
            f"{peer.get('confidence') or '(unknown)'} "
            f"age={peer.get('age_seconds')}s "
            f"events={peer.get('event_count')} "
            f"wake_hint={peer.get('wake_hint') or '(none)'} "
            f"sessions={peer.get('covered_session_count', 0)}/"
            f"{peer.get('known_session_count', 0)} "
            f"omitted={peer.get('omitted_session_count', 0)}"
        )
    ]
    if peer.get("suggested_command"):
        lines.append(f"  suggested: `{peer.get('suggested_command')}`")
    if peer.get("latest_summary"):
        lines.append(f"  latest: {_clip(peer.get('latest_summary'))}")
    return lines


def _signal_rows(orchestration: dict[str, object]) -> list[dict[str, object]]:
    rows = orchestration.get("signals")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _agent_loop_rows(orchestration: dict[str, object]) -> list[dict[str, object]]:
    rows = orchestration.get("agent_loop_decisions")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _signal_row_text(row: dict[str, object]) -> str:
    command = (
        f" | `{row.get('suggested_command')}`"
        if row.get("suggested_command")
        else ""
    )
    details = _signal_details(row)
    return (
        f"- {row.get('source') or '(source)'}:{row.get('signal_id') or '(signal)'} "
        f"{row.get('status') or '(status)'} - {_clip(row.get('summary'))}"
        f"{details}{command}"
    )


def _signal_details(row: dict[str, object]) -> str:
    parts: list[str] = []
    if row.get("severity"):
        parts.append(f"severity={row.get('severity')}")
    if row.get("recommended_action"):
        parts.append(f"action={row.get('recommended_action')}")
    if row.get("source_surface"):
        parts.append(f"surface={row.get('source_surface')}")
    if row.get("closure_check_command"):
        parts.append(f"closure_check={row.get('closure_check_command')}")
    if not parts:
        return ""
    return f" ({'; '.join(parts)})"


def _agent_loop_row_text(row: dict[str, object]) -> str:
    return (
        f"- agent-loop {row.get('actor_id') or '(actor)'}:"
        f"{row.get('actor_role') or '(role)'} "
        f"session={_short(row.get('session_id')) or 'unscoped'} "
        f"state={row.get('lifecycle_state') or '(none)'} "
        f"action={row.get('required_action') or '(none)'} "
        f"safe={row.get('safe_to_continue')} "
        f"mutate={row.get('may_mutate')} "
        f"proof={row.get('proof_state') or '(none)'} "
        f"blocker={_clip(row.get('top_blocker'), limit=120) or '(none)'}"
    )


def _rows(runtime: dict[str, object]) -> list[dict[str, object]]:
    rows = runtime.get("rows")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _session_rows(runtime: dict[str, object]) -> list[dict[str, object]]:
    rows = runtime.get("session_discovery")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _session_row_text(row: dict[str, object]) -> str:
    state = "registered" if row.get("registered") else "unregistered"
    return (
        f"- session {row.get('provider') or '(provider)'} "
        f"{_short(row.get('session_id')) or '(none)'}: {state} "
        f"age={row.get('age_seconds')}s "
        f"visibility={row.get('visibility') or 'session_jsonl'}"
    )


def _clip(value: object, *, limit: int = 220) -> str:
    text = str(value or "").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _short(value: object) -> str:
    text = str(value or "").strip()
    if len(text) <= 12:
        return text
    return text[:12]


__all__ = ["orchestration_lines", "peer_mind_lines", "runtime_lines"]
