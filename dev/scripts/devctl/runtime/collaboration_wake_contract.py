"""Shared wake-continuity helpers for typed collaboration/runtime state."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from .review_state_models import CollaborationParticipantState

_WAKE_MODE_VALUES = frozenset(
    {"continuous", "tick_based", "manual_nudge_required", "inactive", "unknown"}
)
_AUTONOMOUS_WAKE_MODES = frozenset({"continuous", "tick_based"})


class LoopAutonomyState(NamedTuple):
    loop_wake_mode: str = "unknown"
    loop_wake_interval_seconds: int = 0
    loop_driver_agent: str = ""
    loop_autonomy_ok: bool = False
    loop_gap_summary: str = ""

    @classmethod
    def from_mapping(cls, value: object) -> LoopAutonomyState | None:
        if not isinstance(value, Mapping):
            return None
        if not any(
            key in value
            for key in (
                "loop_autonomy_ok",
                "loop_wake_mode",
                "loop_wake_interval_seconds",
                "loop_driver_agent",
                "loop_gap_summary",
            )
        ):
            return None
        state = cls(
            loop_wake_mode=normalize_wake_mode(value.get("loop_wake_mode")),
            loop_wake_interval_seconds=max(
                0, int(value.get("loop_wake_interval_seconds") or 0)
            ),
            loop_driver_agent=str(value.get("loop_driver_agent") or "").strip(),
            loop_autonomy_ok=bool(value.get("loop_autonomy_ok", False)),
            loop_gap_summary=str(value.get("loop_gap_summary") or "").strip(),
        )
        if (
            not state.loop_autonomy_ok
            and state.loop_wake_mode == "unknown"
            and state.loop_wake_interval_seconds == 0
            and not state.loop_driver_agent
            and not state.loop_gap_summary
        ):
            return None
        return state


def normalize_wake_mode(value: object) -> str:
    mode = str(value or "").strip().lower()
    if not mode:
        return "unknown"
    return mode if mode in _WAKE_MODE_VALUES else "unknown"


def participant_wake_mode(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    agent_id: str,
) -> str:
    if not str(agent_id or "").strip():
        return "inactive"
    for participant in participants:
        participant_id = participant.agent_id or participant.provider
        if not _same_agent(participant_id, agent_id):
            continue
        mode = normalize_wake_mode(participant.host_wake_mode)
        if mode != "unknown":
            return mode
        if not participant.live:
            return "inactive"
        return "unknown"
    return "inactive"


def participant_wake_interval(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    agent_id: str,
) -> int:
    if not str(agent_id or "").strip():
        return 0
    for participant in participants:
        participant_id = participant.agent_id or participant.provider
        if not _same_agent(participant_id, agent_id):
            continue
        return max(0, int(participant.wake_interval_seconds or 0))
    return 0


def wake_continuity_contract(
    *,
    reviewer_mode: str,
    mutation_owner: str,
    verification_owner: str,
    watcher_owner: str,
    participants: tuple[CollaborationParticipantState, ...],
) -> tuple[str, str, str, bool, str]:
    mutation_wake_mode = participant_wake_mode(
        participants=participants,
        agent_id=mutation_owner,
    )
    verification_wake_mode = participant_wake_mode(
        participants=participants,
        agent_id=verification_owner,
    )
    watcher_wake_mode = participant_wake_mode(
        participants=participants,
        agent_id=watcher_owner,
    )
    if reviewer_mode != "active_dual_agent":
        return (
            mutation_wake_mode,
            verification_wake_mode,
            watcher_wake_mode,
            True,
            "",
        )

    gaps: list[str] = []
    for lane_name, owner, mode in (
        ("mutation", mutation_owner, mutation_wake_mode),
        ("verification", verification_owner, verification_wake_mode),
        ("watcher", watcher_owner, watcher_wake_mode),
    ):
        if not owner:
            gaps.append(f"{lane_name}=unassigned")
            continue
        if mode != "continuous":
            gaps.append(f"{lane_name}={owner}/{mode}")
    if not gaps:
        return (
            mutation_wake_mode,
            verification_wake_mode,
            watcher_wake_mode,
            True,
            "",
        )
    return (
        mutation_wake_mode,
        verification_wake_mode,
        watcher_wake_mode,
        False,
        "compatibility active reviewer mode requires continuous attention-capable "
        "mutation, verification, and watcher lanes: " + "; ".join(gaps),
    )


def loop_autonomy_contract(
    *,
    reviewer_mode: str,
    mutation_owner: str,
    verification_owner: str,
    watcher_owner: str,
    participants: tuple[CollaborationParticipantState, ...],
) -> LoopAutonomyState:
    mutation_wake_mode = participant_wake_mode(
        participants=participants,
        agent_id=mutation_owner,
    )
    verification_wake_mode = participant_wake_mode(
        participants=participants,
        agent_id=verification_owner,
    )
    watcher_wake_mode = participant_wake_mode(
        participants=participants,
        agent_id=watcher_owner,
    )
    mutation_wake_interval = participant_wake_interval(
        participants=participants,
        agent_id=mutation_owner,
    )
    verification_wake_interval = participant_wake_interval(
        participants=participants,
        agent_id=verification_owner,
    )
    watcher_wake_interval = participant_wake_interval(
        participants=participants,
        agent_id=watcher_owner,
    )

    normalized_mode = str(reviewer_mode or "").strip() or "single_agent"
    if normalized_mode == "active_dual_agent":
        lane_rows = (
            ("mutation", mutation_owner, mutation_wake_mode, mutation_wake_interval),
            (
                "verification",
                verification_owner,
                verification_wake_mode,
                verification_wake_interval,
            ),
            ("watcher", watcher_owner, watcher_wake_mode, watcher_wake_interval),
        )
        blockers: list[str] = []
        intervals: list[int] = []
        saw_tick = False
        for lane_name, owner, mode, interval in lane_rows:
            if not owner:
                blockers.append(f"{lane_name}=unassigned")
                continue
            if mode not in _AUTONOMOUS_WAKE_MODES:
                blockers.append(f"{lane_name}={owner}/{mode}")
                continue
            if mode == "tick_based":
                saw_tick = True
                intervals.append(interval if interval > 0 else 0)
        if blockers:
            return LoopAutonomyState(
                loop_wake_mode=_blocked_loop_mode(tuple(row[2] for row in lane_rows)),
                loop_wake_interval_seconds=0,
                loop_driver_agent="multi_lane",
                loop_autonomy_ok=False,
                loop_gap_summary=(
                    "compatibility active reviewer loop lacks autonomous attention coverage: "
                    + "; ".join(blockers)
                ),
            )
        return LoopAutonomyState(
            loop_wake_mode="tick_based" if saw_tick else "continuous",
            loop_wake_interval_seconds=max(intervals) if intervals else 0,
            loop_driver_agent="multi_lane",
            loop_autonomy_ok=True,
            loop_gap_summary="",
        )

    candidate_rows = _candidate_loop_rows(
        mutation_owner=mutation_owner,
        mutation_wake_mode=mutation_wake_mode,
        mutation_wake_interval=mutation_wake_interval,
        verification_owner=verification_owner,
        verification_wake_mode=verification_wake_mode,
        verification_wake_interval=verification_wake_interval,
        watcher_owner=watcher_owner,
        watcher_wake_mode=watcher_wake_mode,
        watcher_wake_interval=watcher_wake_interval,
    )
    for owner, mode, interval in candidate_rows:
        if mode not in _AUTONOMOUS_WAKE_MODES:
            continue
        return LoopAutonomyState(
            loop_wake_mode=mode,
            loop_wake_interval_seconds=interval if mode == "tick_based" else 0,
            loop_driver_agent=owner,
            loop_autonomy_ok=True,
            loop_gap_summary="",
        )
    blocked_mode = _blocked_loop_mode(tuple(mode for _, mode, _ in candidate_rows))
    return LoopAutonomyState(
        loop_wake_mode=blocked_mode,
        loop_wake_interval_seconds=0,
        loop_driver_agent=_first_owner(candidate_rows),
        loop_autonomy_ok=False,
        loop_gap_summary=(
            f"{normalized_mode} loop has no wake-capable owner; "
            + _candidate_summary(candidate_rows)
        ),
    )


def _same_agent(left: str, right: str) -> bool:
    return bool(left and right and left.strip().lower() == right.strip().lower())


def _candidate_loop_rows(
    *,
    mutation_owner: str,
    mutation_wake_mode: str,
    mutation_wake_interval: int,
    verification_owner: str,
    verification_wake_mode: str,
    verification_wake_interval: int,
    watcher_owner: str,
    watcher_wake_mode: str,
    watcher_wake_interval: int,
) -> tuple[tuple[str, str, int], ...]:
    rows = (
        (mutation_owner, mutation_wake_mode, mutation_wake_interval),
        (verification_owner, verification_wake_mode, verification_wake_interval),
        (watcher_owner, watcher_wake_mode, watcher_wake_interval),
    )
    ordered: list[tuple[str, str, int]] = []
    seen: set[str] = set()
    for owner, mode, interval in rows:
        if not owner or owner in seen:
            continue
        seen.add(owner)
        ordered.append((owner, mode, interval))
    return tuple(ordered)


def _blocked_loop_mode(modes: tuple[str, ...]) -> str:
    if "manual_nudge_required" in modes:
        return "manual_nudge_required"
    if "unknown" in modes:
        return "unknown"
    if "inactive" in modes:
        return "inactive"
    return "unknown"


def _first_owner(rows: tuple[tuple[str, str, int], ...]) -> str:
    for owner, _mode, _interval in rows:
        if owner:
            return owner
    return ""


def _candidate_summary(rows: tuple[tuple[str, str, int], ...]) -> str:
    if not rows:
        return "no typed participants are assigned."
    return ", ".join(f"{owner}/{mode}" for owner, mode, _interval in rows)
