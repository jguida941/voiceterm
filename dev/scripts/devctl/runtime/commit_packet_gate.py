"""Shared fail-closed gate: block commit-capable lanes on actionable packets.

This gate is intentionally lease-independent. A held attention-revision lease
does NOT suppress this check. When a reviewer posts a mutating action request
or non-review-only instruction after a lease was acquired, the commit must still
block. Review-only findings remain visible through packet surfaces without
creating a commit Catch-22.

Both the governed commit path (governed_executor_commit_phase) and the snapshot
receipt-commit path (review_snapshot) call this gate before any irreversible
git commit.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from ..review_channel.event_reducer import load_or_refresh_event_bundle
from ..review_channel.events import resolve_artifact_paths
from ..review_channel.pending_packets import load_pending_packet_queue
from .review_state_packet_models import AgentAttentionRecord, PacketInboxState
from .review_state_parser import review_state_from_payload
from .review_state_models import ReviewState
from .review_packet_inbox_liveness import (
    is_live_control_packet as _canonical_live_control_packet,
)


def pending_reviewer_packets_block_commit(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
    target_agent: str = "",
    exempt_packet_id: str = "",
) -> str | None:
    """Return a blocking summary when actionable reviewer packets exist.

    When ``target_agent`` is provided, only that agent's inbox is checked.
    When empty, any agent with actionable attention triggers the block.

    Fail-closed: if the typed review state cannot be loaded or the packet
    inbox is missing, returns a blocking summary. A missing/unreadable
    review state cannot silently reopen commit authority.

    Returns None only when the commit path is demonstrably clear.
    """
    if review_channel_path is None:
        return None

    try:
        review_state = _load_review_state(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
        )
    except (ValueError, OSError) as exc:
        return (
            f"Commit blocked: typed review state load failed ({exc}). "
            "Cannot verify pending reviewer packets. "
            "Resolve the review-channel projection before committing."
        )
    if review_state is None:
        return (
            "Commit blocked: typed review state could not be loaded from "
            f"{review_channel_path}. Cannot verify pending reviewer packets. "
            "Resolve the review-channel projection before committing."
        )

    packet_inbox: PacketInboxState | None = getattr(
        review_state, "packet_inbox", None,
    )
    if packet_inbox is None:
        return (
            "Commit blocked: typed review state has no packet inbox. "
            "Cannot verify pending reviewer packets."
        )

    normalized_target = target_agent.strip().lower()

    if not normalized_target:
        return (
            "Commit blocked: writable execution target could not be resolved "
            "from typed review state. Cannot determine which lane to check "
            "for pending reviewer packets. Resolve the review-channel "
            "projection and ensure a writable lane is configured."
        )

    agents = getattr(packet_inbox, "agents", None)
    if agents is None or not isinstance(agents, (list, tuple)):
        return (
            "Commit blocked: packet inbox has malformed or missing agents field. "
            "Cannot verify pending reviewer packets."
        )

    blocking: list[tuple[str, list[str]]] = []
    for record in agents:
        agent_name = getattr(record, "agent", None)
        pending_ids = getattr(record, "pending_actionable_packet_ids", None)
        if not isinstance(agent_name, str) or not isinstance(pending_ids, (list, tuple)):
            return (
                "Commit blocked: malformed agent record in packet inbox "
                f"(agent={type(agent_name).__name__}, ids={type(pending_ids).__name__}). "
                "Cannot verify pending reviewer packets."
            )
        if normalized_target and agent_name.lower() != normalized_target:
            continue
        blocking_ids = _blocking_pending_packet_ids(
            review_state,
            agent_name,
            exempt_packet_id=exempt_packet_id,
        )
        if blocking_ids is None:
            if not _has_actionable_attention(record):
                continue
            ids = [str(p) for p in pending_ids]
            if (
                not ids
                and getattr(record, "wake_reason", "").strip() == "finding_pending"
            ):
                latest_finding = str(
                    getattr(record, "latest_finding_packet_id", "") or ""
                ).strip()
                ids = [latest_finding or "finding_pending"]
        else:
            ids = blocking_ids
        if ids:
            blocking.append((agent_name, ids))

    if not blocking:
        return None

    total = sum(len(ids) for _, ids in blocking)
    parts = "; ".join(
        f"{a}: {', '.join(ids[:3])}" for a, ids in blocking
    )
    return (
        f"Commit blocked: {total} pending reviewer packet(s) "
        f"with actionable attention ({parts}). "
        "Resolve pending packets before committing: "
        "`devctl review-channel --action inbox --status pending --format json`."
    )


def pending_packet_queue_block_commit(
    *,
    repo_root: Path,
    target_agent: str,
    exempt_packet_id: str = "",
) -> str | None:
    """Lightweight event-log gate for packet-authorized commit execution."""
    normalized_target = target_agent.strip().lower()
    if not normalized_target:
        return (
            "Commit blocked: writable execution target could not be resolved "
            "from typed action-request authority."
        )
    try:
        queue = load_pending_packet_queue(repo_root, fail_closed=True)
    except ValueError as exc:
        return (
            f"Commit blocked: typed review packet queue load failed ({exc}). "
            "Cannot verify pending reviewer packets."
        )

    ids: list[str] = []
    for packet in (*queue.pending_packets, *queue.control_packets):
        if not _packet_targets_agent(packet, normalized_target):
            continue
        packet_id = _packet_text(packet, "packet_id")
        if exempt_packet_id and packet_id == exempt_packet_id:
            continue
        if not _is_live_control_packet(packet):
            continue
        if not _packet_blocks_commit(packet):
            continue
        if packet_id:
            ids.append(packet_id)
    if not ids:
        return None
    return (
        f"Commit blocked: {len(ids)} pending reviewer packet(s) "
        f"with actionable attention ({normalized_target}: {', '.join(ids[:3])}). "
        "Resolve pending packets before committing: "
        "`devctl review-channel --action inbox --status pending --format json`."
    )


# ── Shared caller policy ───────────────────────────────────────


def check_commit_packet_gate(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
    load_review_state_fn,
    resolve_target_fn,
    exempt_packet_id: str = "",
) -> str | None:
    """Shared caller policy: load → resolve → gate, skip when not applicable.

    Both governed commit and receipt-commit callers use this to avoid
    duplicating the "skip when no review state / no writable lane" logic.

    Fail-closed contract:
    - review_channel_path=None → skip (no review channel configured)
    - review_channel_path set but directory absent → skip (not yet created)
    - review_channel_path set, directory exists, but load fails → BLOCK
    - review_channel_path set, state loads, no writable lane → skip
    - review_channel_path set, state loads, writable lane → delegate to gate
    """
    if review_channel_path is None:
        return None
    if not review_channel_path.exists():
        return None
    try:
        review_state = load_review_state_fn()
    except (ValueError, OSError) as exc:
        return (
            f"Commit blocked: review state load failed ({exc}). "
            "Cannot verify pending reviewer packets. "
            "Resolve the review-channel projection before committing."
        )
    if review_state is None:
        return (
            "Commit blocked: typed review state could not be loaded from "
            f"{review_channel_path}. Cannot verify pending reviewer packets. "
            "Resolve the review-channel projection before committing."
        )
    target = resolve_target_fn(review_state)
    if not target:
        return None
    return pending_reviewer_packets_block_commit(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        target_agent=target,
        exempt_packet_id=exempt_packet_id,
    )


# ── Internal helpers ───────────────────────────────────────────


def _has_actionable_attention(record: AgentAttentionRecord) -> bool:
    """Mirror of governed_executor_commit_runtime._has_actionable_packet_attention."""
    if record.pending_actionable_packet_ids:
        return True
    return record.wake_reason.strip() == "finding_pending"


def _blocking_pending_packet_ids(
    review_state: ReviewState,
    agent_name: str,
    *,
    exempt_packet_id: str = "",
) -> list[str] | None:
    packets = review_state.packets
    if not isinstance(packets, (list, tuple)):
        return None
    if not packets:
        return None
    blocking_ids: list[str] = []
    for packet in packets:
        if not _packet_targets_agent(packet, agent_name):
            continue
        packet_id = _packet_text(packet, "packet_id")
        if exempt_packet_id and packet_id == exempt_packet_id:
            continue
        if not _is_live_control_packet(packet):
            continue
        if not _packet_blocks_commit(packet):
            continue
        if packet_id:
            blocking_ids.append(packet_id)
    return blocking_ids


def _packet_targets_agent(packet: object, agent_name: str) -> bool:
    return _packet_text(packet, "to_agent").lower() == agent_name.strip().lower()


def _is_live_control_packet(packet: object) -> bool:
    if isinstance(packet, Mapping):
        return _canonical_live_control_packet(packet)
    status = _packet_text(packet, "status")
    if status not in {"pending", "acked"}:
        return False
    if status == "acked" and _packet_text(packet, "kind") != "action_request":
        return False
    if _packet_text(packet, "execution_failed_at_utc"):
        return False
    if _packet_text(packet, "apply_pending_after_execution_at_utc"):
        return False
    expires_at = _parse_packet_utc(packet, "expires_at_utc")
    if expires_at is None:
        return True
    return expires_at > datetime.now(timezone.utc)


def _packet_blocks_commit(packet: object) -> bool:
    kind = _packet_text(packet, "kind")
    if kind == "action_request":
        return True
    if kind == "finding":
        return False
    if kind != "instruction":
        return False
    requested_action = _packet_text(packet, "requested_action")
    policy_hint = _packet_text(packet, "policy_hint")
    return requested_action != "review_only" or policy_hint != "review_only"


def _packet_text(packet: object, field: str) -> str:
    if isinstance(packet, Mapping):
        return str(packet.get(field) or "").strip()
    return str(getattr(packet, field, "") or "").strip()


def _parse_packet_utc(packet: object, field: str) -> datetime | None:
    raw_value = _packet_text(packet, field)
    if not raw_value:
        return None
    try:
        stamp = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


def _load_review_state(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
) -> object | None:
    """Load the latest typed review state from the event-backed projection.

    Returns None only when the review channel path does not exist
    (no projection configured). On load/parse errors, raises ValueError
    so the caller can fail closed.
    """
    if review_channel_path is None or not review_channel_path.exists():
        return None
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    bundle = load_or_refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    return review_state_from_payload(bundle.review_state)
