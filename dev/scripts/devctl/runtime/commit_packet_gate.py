"""Shared fail-closed gate: block commit-capable lanes on pending reviewer packets.

This gate is intentionally lease-independent. A held attention-revision lease
does NOT suppress this check. When a reviewer posts finding/instruction packets
after a lease was acquired, the commit must still block.

Both the governed commit path (governed_executor_commit_phase) and the snapshot
receipt-commit path (review_snapshot) call this gate before any irreversible
git commit.
"""

from __future__ import annotations

from pathlib import Path

from ..review_channel.event_reducer import load_or_refresh_event_bundle
from ..review_channel.events import resolve_artifact_paths
from .review_state_parser import review_state_from_payload


def pending_reviewer_packets_block_commit(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
    target_agent: str = "",
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

    packet_inbox = getattr(review_state, "packet_inbox", None)
    if packet_inbox is None:
        return (
            "Commit blocked: typed review state has no packet inbox. "
            "Cannot verify pending reviewer packets."
        )

    agent_records = tuple(getattr(packet_inbox, "agents", ()) or ())
    normalized_target = target_agent.strip().lower()

    if not normalized_target:
        return (
            "Commit blocked: writable execution target could not be resolved "
            "from typed review state. Cannot determine which lane to check "
            "for pending reviewer packets. Resolve the review-channel "
            "projection and ensure a writable lane is configured."
        )

    blocking: list[tuple[str, list[str]]] = []
    for record in agent_records:
        agent = str(getattr(record, "agent", "") or "").strip()
        if normalized_target and agent.lower() != normalized_target:
            continue
        if _has_actionable_attention(record):
            ids = [
                str(p) for p in
                (getattr(record, "pending_actionable_packet_ids", ()) or ())
            ]
            blocking.append((agent, ids))

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


# ── Internal helpers ───────────────────────────────────────────


def _has_actionable_attention(record: object) -> bool:
    """Mirror of governed_executor_commit_runtime._has_actionable_packet_attention."""
    pending = getattr(record, "pending_actionable_packet_ids", ()) or ()
    if pending:
        return True
    wake_reason = str(getattr(record, "wake_reason", "") or "").strip()
    return wake_reason == "finding_pending"


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
