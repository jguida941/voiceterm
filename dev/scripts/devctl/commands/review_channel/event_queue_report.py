"""Queue report helpers for event-backed review-channel actions."""

from __future__ import annotations

from ...runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL
from ...runtime.master_plan_store import read_plan_rows_jsonl
from ...review_channel.agent_sync_readers import agent_sync_pending_packet_ids
from ...review_channel.event_projection_queue import build_event_queue_summary
from ...review_channel.pending_packets import live_pending_packets


def queue_for_event_report(
    *,
    args,
    bundle,
    packets: list[dict[str, object]] | None,
    repo_root=None,
):
    """Return the queue summary for one event-backed action report."""
    queue = bundle.review_state.get("queue", {})
    target = str(getattr(args, "target", "") or "").strip()
    target_role = str(getattr(args, "target_role", "") or "").strip()
    target_session_id = str(getattr(args, "target_session_id", "") or "").strip()
    status_filter = str(getattr(args, "status", "") or "").strip()
    if (
        args.action not in {"inbox", "watch", "operator-inbox"}
        or not (target or target_role or target_session_id)
        or packets is None
        or status_filter not in {"", "pending"}
    ):
        return queue
    scope_key = _filtered_scope_key(
        target=target,
        target_role=target_role,
        target_session_id=target_session_id,
    )
    pending_counts = _filtered_pending_counts(
        queue=queue,
        scope_key=scope_key,
        packet_count=len(packets),
    )
    stale_count = 0
    if isinstance(queue, dict):
        stale_count = int(queue.get("stale_packet_count") or 0)
    summary = build_event_queue_summary(
        pending_counts,
        stale_count,
        packets=packets,
        plan_rows=_read_plan_rows(repo_root),
    )
    summary["filtered_scope"] = {
        "target": target,
        "target_role": target_role,
        "target_session_id": target_session_id,
        "scope_key": scope_key,
    }
    pending_ids = _canonical_agent_sync_pending_ids(
        review_state=bundle.review_state,
        target=target,
    )
    if pending_ids:
        summary["agent_sync_pending_total"] = len(pending_ids)
        summary["agent_sync_pending_packet_ids"] = list(pending_ids)
        if not packets:
            summary["filtered_pending_note"] = (
                "target has pending agent-sync packet attention outside the "
                "actionable inbox filter"
            )
    return summary


def _read_plan_rows(repo_root) -> tuple[object, ...]:
    if repo_root is None:
        return ()
    path = repo_root / DEFAULT_MASTER_PLAN_STORE_REL
    if not path.is_file():
        return ()
    return tuple(read_plan_rows_jsonl(path))


def _filtered_pending_counts(
    *,
    queue: object,
    scope_key: str,
    packet_count: int,
) -> dict[str, int]:
    keys = set(_existing_pending_count_keys(queue))
    if scope_key:
        keys.add(scope_key)
    return {
        key: packet_count if key == scope_key else 0
        for key in sorted(keys)
        if key
    }


def _existing_pending_count_keys(queue: object) -> tuple[str, ...]:
    if not isinstance(queue, dict):
        return ()
    keys = []
    for key in queue:
        if not isinstance(key, str):
            continue
        if key == "pending_total" or not key.startswith("pending_"):
            continue
        suffix = key.removeprefix("pending_").strip()
        if suffix:
            keys.append(suffix)
    return tuple(keys)


def _filtered_scope_key(
    *,
    target: str,
    target_role: str,
    target_session_id: str,
) -> str:
    if target:
        return _queue_key(target)
    if target_role and target_session_id:
        return f"role_{_queue_key(target_role)}_session_{_queue_key(target_session_id)}"
    if target_role:
        return f"role_{_queue_key(target_role)}"
    if target_session_id:
        return f"session_{_queue_key(target_session_id)}"
    return ""


def _queue_key(value: str) -> str:
    normalized = "".join(
        character.lower() if character.isalnum() else "_"
        for character in str(value or "").strip()
    )
    normalized = "_".join(part for part in normalized.split("_") if part)
    return normalized or "scope"


def _canonical_agent_sync_pending_ids(
    *,
    review_state: dict[str, object],
    target: str,
) -> tuple[str, ...]:
    """Return agent-sync pending IDs that still exist in canonical live rows."""
    pending_ids = agent_sync_pending_packet_ids(review_state, target)
    packet_rows = review_state.get("packets")
    if not isinstance(packet_rows, list):
        return pending_ids
    canonical_live_ids = {
        str(packet.get("packet_id") or "").strip()
        for packet in live_pending_packets(packet_rows)
        if isinstance(packet, dict)
        and str(packet.get("to_agent") or "").strip() == target
    }
    if not canonical_live_ids:
        return ()
    return tuple(packet_id for packet_id in pending_ids if packet_id in canonical_live_ids)
