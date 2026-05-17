"""Markdown rendering for typed sync-status sections."""

from __future__ import annotations


def append_coordination_state_section(lines: list[str], coord: object) -> None:
    """Render typed CoordinationStateProjection block when sync-status emits it."""
    if not isinstance(coord, dict) or not coord.get("contract_id"):
        return
    topology = str(coord.get("coordination_topology") or "unknown")
    authority = str(coord.get("authority_mode") or "unknown")
    recovery = str(coord.get("recovery_eligibility") or "unknown")
    legacy_mode = str(coord.get("legacy_reviewer_mode") or "")
    observed = _mapping(coord.get("observed_runtime"))
    actor_labels = _actor_labels(observed)
    actors_text = ", ".join(actor_labels) if actor_labels else "none"
    row_counts = _mapping(observed.get("work_board_row_counts"))
    barrier_total = int(row_counts.get("lane_barriers_total") or 0)

    lines.append("")
    lines.append("## Coordination State (typed)")
    lines.append(f"- coordination_topology: {topology}")
    lines.append(f"- authority_mode: {authority}")
    lines.append(f"- recovery_eligibility: {recovery}")
    lines.append(f"- active_actor_count: {int(observed.get('active_actor_count') or 0)} ({actors_text})")
    if barrier_total:
        lines.append(f"- lane_barriers_total: {barrier_total}")
    if legacy_mode and topology == "multi_agent_active" and legacy_mode == "single_agent":
        lines.append(
            "- WARNING: legacy_reviewer_mode='single_agent' is "
            "authority/review-gate vocabulary; observed runtime is "
            "multi_agent_active per typed work-board."
        )


def append_work_board_section(lines: list[str], work_board: object) -> None:
    """Render typed AgentWorkBoardProjection rows and barriers."""
    if not isinstance(work_board, dict):
        return
    rows = work_board.get("rows") or []
    barriers = work_board.get("barriers") or []
    if not isinstance(rows, list) or (not rows and not barriers):
        return
    lines.append("")
    lines.append("## Work Board (typed rows)")
    event_index = str(work_board.get("event_index") or "")
    if event_index:
        lines.append(f"- source_latest_event_id: {event_index}")
    if not rows:
        lines.append("- (no active rows)")
    _append_work_rows(lines, rows)
    _append_barriers(lines, barriers)


def _append_work_rows(lines: list[str], rows: list[object]) -> None:
    for row in rows:
        if not isinstance(row, dict):
            continue
        lines.append(_work_row_summary(row))
        focus_bits = _focus_bits(row)
        if focus_bits:
            lines.append(f"  - focus: {', '.join(focus_bits)}")
        idle = int(row.get("idle_seconds") or 0)
        blocker = str(row.get("blocker_or_wait_reason") or "")
        source_event = str(row.get("source_event_id") or "unknown")
        confidence = str(row.get("confidence_class") or "unknown")
        lines.append(
            f"  - idle_seconds={idle} blocker={blocker or 'none'} "
            f"source_event_id={source_event} confidence={confidence}"
        )


def _append_barriers(lines: list[str], barriers: object) -> None:
    if not isinstance(barriers, list) or not barriers:
        return
    lines.append("")
    lines.append("## Lane Barriers (typed)")
    for barrier in barriers:
        if isinstance(barrier, dict):
            lines.append(_barrier_line(barrier))


def _work_row_summary(row: dict[str, object]) -> str:
    actor = str(row.get("actor_id") or "unknown")
    role = str(row.get("role") or "unknown")
    provider = str(row.get("provider") or "unknown")
    session = str(row.get("session_id") or row.get("lane_id") or "unknown")
    packet = str(row.get("active_packet_id") or "(none)")
    status = str(row.get("status") or "unknown")
    mutation = str(row.get("mutation_mode") or "unknown")
    branch = str(row.get("branch") or "unknown")
    worktree = str(row.get("worktree_identity") or "unknown")
    return (
        f"- {actor} ({role}/{provider}) session={session} "
        f"packet={packet} status={status} mutation={mutation} "
        f"branch={branch} worktree={worktree}"
    )


def _focus_bits(row: dict[str, object]) -> list[str]:
    pairs = (
        ("command", row.get("current_command")),
        ("check", row.get("current_check")),
        ("file", row.get("current_file_or_module")),
    )
    return [
        f"{label}={value}"
        for label, value in pairs
        if str(value or "").strip()
    ]


def _barrier_line(barrier: dict[str, object]) -> str:
    kind = str(barrier.get("kind") or "unknown")
    actor = str(barrier.get("actor_id") or "unknown")
    target_bits = _target_bits(barrier)
    summary = str(barrier.get("summary") or "")
    line = f"- {actor} blocked by {kind}: {' '.join(target_bits) or '(no target)'}"
    if summary:
        line += f" - {summary}"
    return line


def _target_bits(row: dict[str, object]) -> list[str]:
    pairs = (
        ("target_packet", row.get("target_packet_id")),
        ("target_actor", row.get("target_actor_id")),
    )
    return [
        f"{label}={value}"
        for label, value in pairs
        if str(value or "").strip()
    ]


def _actor_labels(observed: dict[str, object]) -> list[str]:
    providers = list(observed.get("active_runtime_providers") or [])
    channels = list(observed.get("active_operator_channels") or [])
    return [str(item) for item in providers] + [
        f"dashboard:{channel}" for channel in channels
    ]


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}

