"""Lane-barrier helpers for the typed agent work-board."""

from __future__ import annotations

import hashlib

from .agent_work_board_models import LaneBarrierRow


def build_lane_barriers(
    *,
    agent_sync_payload: dict[str, object],
) -> list[LaneBarrierRow]:
    barriers: list[LaneBarrierRow] = []
    agents = agent_sync_payload.get("agents") if isinstance(agent_sync_payload, dict) else None
    if not isinstance(agents, dict):
        return barriers

    for actor_id, row in agents.items():
        if not isinstance(row, dict):
            continue
        awaiting = str(row.get("awaiting_packet_id") or "")
        if not awaiting:
            continue
        target_actor = str(row.get("awaiting_from_agent") or "")
        lane_id = f"{actor_id}_session_{actor_id[:12]}"
        barriers.append(
            LaneBarrierRow(
                barrier_id=_barrier_id(lane_id, "awaiting_reviewer_ack", awaiting),
                lane_id=lane_id,
                actor_id=str(actor_id),
                kind="awaiting_reviewer_ack",
                target_packet_id=awaiting,
                target_capability="",
                target_actor_id=target_actor,
                raised_at_utc="",
                raised_by_event_id="",
                expected_clear_signal=f"{target_actor or 'partner'}.ack({awaiting})",
                summary=(
                    f"{actor_id} lane awaiting "
                    f"{target_actor or 'partner'} ack on {awaiting}"
                ),
            )
        )
    return barriers


def index_barriers_by_lane(barriers: list[LaneBarrierRow]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for barrier in barriers:
        lane_id = barrier["lane_id"]
        index.setdefault(lane_id, []).append(barrier["barrier_id"])
    return index


def _barrier_id(lane_id: str, kind: str, target_ref: str) -> str:
    digest = hashlib.sha1(
        f"{lane_id}|{kind}|{target_ref}".encode("utf-8")
    ).hexdigest()[:12]
    return f"lb_{digest}"
