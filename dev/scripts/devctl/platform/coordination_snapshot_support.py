"""Helper reductions for coordination snapshot construction."""

from __future__ import annotations

from pathlib import Path

from .coordination_snapshot_models import CoordinationActorRecord

_MAX_ACTORS = 8
_MAX_REASONS = 4


def repo_name(governance: object | None, repo_root: Path) -> str:
    """Resolve the repo name from governance with a root-path fallback."""
    repo_identity = getattr(governance, "repo_identity", None)
    resolved_name = text(getattr(repo_identity, "repo_name", ""))
    return resolved_name or repo_root.name


def declared_topology(*, collaboration: object | None, observed_topology: str) -> str:
    """Prefer collaboration topology when it exists, else observed topology."""
    topology = text(getattr(collaboration, "topology_mode", ""))
    return topology or observed_topology or "single_agent"


def fanout_posture(
    *,
    delegated_work: tuple[object, ...],
    duplicate_worktrees: tuple[str, ...],
    conflicts: tuple[object, ...],
    collaboration: object | None,
    declared_topology: str,
    observed_topology: str,
) -> str:
    """Reduce live/planned worker facts into one bounded fanout posture."""
    requested_budget = sum(
        max(int(getattr(participant, "requested_worker_budget", 0) or 0), 0)
        for participant in tuple(getattr(collaboration, "participants", ()) or ())
    )
    if duplicate_worktrees:
        return "unsafe_duplicate_worktrees"
    if conflicts:
        return "blocked_by_conflict"
    if any(bool(getattr(receipt, "live", False)) for receipt in delegated_work):
        return "active_fanout"
    if delegated_work and requested_budget <= 0:
        return "planned_scaffolding_only"
    if delegated_work:
        return "planned_not_live"
    if requested_budget > 0:
        return "requested_pending_workers"
    if declared_topology == "dual_agent" and observed_topology == "single_agent":
        return "review_loop_not_live"
    return "single_agent_only"


def worktree_strategy(
    *,
    delegated_work: tuple[object, ...],
    duplicate_worktrees: tuple[str, ...],
) -> str:
    """Classify worker worktree isolation from delegated-work receipts."""
    worktrees = [
        text(getattr(receipt, "worktree", ""))
        for receipt in delegated_work
        if text(getattr(receipt, "worktree", ""))
    ]
    if duplicate_worktrees:
        return "duplicate_worker_worktree"
    if delegated_work and len(worktrees) == len(delegated_work):
        return "isolated_worker_worktrees"
    if delegated_work:
        return "partial_worker_worktree_assignment"
    return "shared_primary_worktree"


def resync_reasons(
    *,
    review_state: object | None,
    conflicts: tuple[object, ...],
    declared_topology: str,
    observed_topology: str,
) -> tuple[str, ...]:
    """Collect the bounded reasons that force resync before safe fanout."""
    reasons: list[str] = []
    for conflict in conflicts:
        summary = text(getattr(conflict, "summary", ""))
        if summary:
            reasons.append(summary)
    attention = getattr(review_state, "attention", None)
    attention_status = text(getattr(attention, "status", ""))
    if attention_status and attention_status not in {"clear", "ready"}:
        reasons.append(f"attention:{attention_status}")
    collaboration = getattr(review_state, "collaboration", None)
    for gate in tuple(getattr(collaboration, "ready_gates", ()) or ()):
        gate_id = text(getattr(gate, "gate_id", "gate"))
        gate_status = text(getattr(gate, "status", ""))
        if gate_status in {"blocked", "pending", "planned"}:
            reasons.append(f"{gate_id}:{gate_status}")
    reviewer_runtime = getattr(review_state, "reviewer_runtime", None)
    freshness = text(getattr(reviewer_runtime, "reviewer_freshness", ""))
    if freshness and freshness not in {"fresh", "current"}:
        reasons.append(f"reviewer_freshness:{freshness}")
    if declared_topology != observed_topology and declared_topology != "single_agent":
        reasons.append(f"declared_topology:{declared_topology}")
    return dedupe(reasons)[:_MAX_REASONS]


def safe_to_fanout(
    *,
    fanout_posture: str,
    duplicate_worktrees: tuple[str, ...],
    resync_reasons: tuple[str, ...],
) -> bool:
    """Return whether fanout is safe under the current bounded posture."""
    if duplicate_worktrees or resync_reasons:
        return False
    return fanout_posture in {
        "active_fanout",
        "planned_not_live",
        "requested_pending_workers",
    }


def recommended_topology(
    *,
    observed_topology: str,
    fanout_posture: str,
    safe_to_fanout: bool,
    resync_reasons: tuple[str, ...],
) -> str:
    """Project the topology recommendation implied by the bounded posture."""
    if resync_reasons:
        return "single_agent"
    if safe_to_fanout and fanout_posture in {
        "active_fanout",
        "planned_not_live",
        "requested_pending_workers",
    }:
        return "multi_agent_orchestrated"
    if observed_topology == "dual_agent":
        return "dual_agent"
    return "single_agent"


def duplicate_worktrees(
    *,
    delegated_work: tuple[object, ...],
    startup_duplicates: tuple[str, ...],
) -> tuple[str, ...]:
    """Merge startup duplicate-worktree detection with receipt evidence."""
    counts: dict[str, int] = {}
    duplicates = list(startup_duplicates)
    for receipt in delegated_work:
        worktree = text(getattr(receipt, "worktree", ""))
        if not worktree:
            continue
        counts[worktree] = counts.get(worktree, 0) + 1
        if counts[worktree] == 2 and worktree not in duplicates:
            duplicates.append(worktree)
    return tuple(duplicates)


def actor_records(
    *,
    review_state: object | None,
    active_participants: tuple[str, ...],
) -> tuple[CoordinationActorRecord, ...]:
    """Build a bounded actor roster from registry, participants, and lanes."""
    active_actor_ids = {
        text(value).split(":", 1)[0]
        for value in active_participants
        if text(value)
    }
    records: list[CoordinationActorRecord] = []
    registry = getattr(review_state, "registry", None)
    for agent in tuple(getattr(registry, "agents", ()) or ()):
        actor_id = text(getattr(agent, "agent_id", ""))
        if not actor_id:
            continue
        presence = "live" if actor_id in active_actor_ids else "configured"
        records.append(
            CoordinationActorRecord(
                actor_id=actor_id,
                provider=text(getattr(agent, "provider", "")),
                role=text(getattr(agent, "current_job", "")) or text(getattr(agent, "lane", "")),
                presence=presence,
                session_name=text(getattr(agent, "lane_title", "")),
                job_state=text(getattr(agent, "job_state", "")),
                waiting_on=text(getattr(agent, "waiting_on", "")),
                worktree=text(getattr(agent, "worktree", "")),
                branch=text(getattr(agent, "branch", "")),
                summary=registry_summary(agent),
            )
        )
    append_participant_records(records=records, review_state=review_state)
    append_delegated_records(records=records, review_state=review_state)
    if records:
        return tuple(records[:_MAX_ACTORS])
    return tuple(
        CoordinationActorRecord(
            actor_id=value.split(":", 1)[0],
            provider=value.split(":", 1)[0],
            role=value.split(":", 1)[1] if ":" in value else "",
            presence="live",
        )
        for value in active_participants[:_MAX_ACTORS]
    )


def append_participant_records(*, records: list[CoordinationActorRecord], review_state: object | None) -> None:
    """Add participant rows that are not already covered by the registry."""
    collaboration = getattr(review_state, "collaboration", None)
    known_actor_ids = {record.actor_id for record in records}
    for participant in tuple(getattr(collaboration, "participants", ()) or ()):
        actor_id = text(getattr(participant, "agent_id", "")) or text(
            getattr(participant, "provider", "")
        )
        if not actor_id or actor_id in known_actor_ids:
            continue
        records.append(
            CoordinationActorRecord(
                actor_id=actor_id,
                provider=text(getattr(participant, "provider", "")),
                role=text(getattr(participant, "role", "")),
                presence="live" if bool(getattr(participant, "live", False)) else "configured",
                session_name=text(getattr(participant, "session_name", "")),
                summary=text(getattr(participant, "status", "")),
            )
        )
        known_actor_ids.add(actor_id)


def append_delegated_records(*, records: list[CoordinationActorRecord], review_state: object | None) -> None:
    """Add delegated-lane rows after the actor roster is populated."""
    collaboration = getattr(review_state, "collaboration", None)
    for receipt in tuple(getattr(collaboration, "delegated_work", ()) or ()):
        actor_id = text(getattr(receipt, "agent_id", ""))
        if not actor_id:
            continue
        records.append(
            CoordinationActorRecord(
                actor_id=actor_id,
                provider=text(getattr(receipt, "provider", "")),
                role=text(getattr(receipt, "role", "")),
                presence="live" if bool(getattr(receipt, "live", False)) else "planned",
                session_name=text(getattr(receipt, "owner_session", "")),
                lane=text(getattr(receipt, "lane", "")),
                mp_scope=text(getattr(receipt, "mp_scope", "")),
                worktree=text(getattr(receipt, "worktree", "")),
                branch=text(getattr(receipt, "branch", "")),
                summary=text(getattr(receipt, "status", "")),
            )
        )


def registry_summary(agent: object) -> str:
    """Render a small summary string for a registry agent row."""
    job_state = text(getattr(agent, "job_state", ""))
    waiting_on = text(getattr(agent, "waiting_on", ""))
    if job_state and waiting_on:
        return f"{job_state}; waiting_on={waiting_on}"
    return job_state or waiting_on


def coordination_summary(
    *,
    observed_topology: str,
    declared_topology: str,
    fanout_posture: str,
    recommended_topology: str,
    resync_reasons: tuple[str, ...],
) -> str:
    """Render the bounded coordination summary string."""
    summary = (
        f"observed={observed_topology}; declared={declared_topology}; "
        f"fanout={fanout_posture}; recommended={recommended_topology}"
    )
    if resync_reasons:
        summary += "; resync required"
    return summary


def dedupe(values: list[str]) -> tuple[str, ...]:
    """Preserve order while dropping duplicates and blanks."""
    ordered: list[str] = []
    for value in values:
        if value and value not in ordered:
            ordered.append(value)
    return tuple(ordered)


def text(value: object) -> str:
    """Normalize an arbitrary value into a stripped string."""
    return str(value or "").strip()

