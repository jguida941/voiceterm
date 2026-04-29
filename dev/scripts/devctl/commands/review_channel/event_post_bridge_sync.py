"""Bridge projection sync after posting a live review-channel instruction."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.bridge_file import rewrite_bridge_markdown
from ...review_channel.bridge_projection import render_bridge_projection
from ...review_channel.core import DEFAULT_BRIDGE_REL
from ...review_channel.heartbeat import compute_non_audit_worktree_hash


def sync_bridge_after_posted_current_instruction(
    *,
    repo_root: Path,
    paths: dict[str, object],
    packet: dict[str, object],
    review_state_payload: dict[str, object],
    compute_worktree_hash_fn=compute_non_audit_worktree_hash,
    render_bridge_projection_fn=render_bridge_projection,
) -> dict[str, object] | None:
    """Converge the compatibility bridge when a post becomes the live instruction."""
    if not _posted_packet_drives_current_instruction(packet, review_state_payload):
        return None
    bridge_path = paths.get("bridge_path")
    if not isinstance(bridge_path, Path):
        bridge_path = repo_root / DEFAULT_BRIDGE_REL
    if not bridge_path.is_file():
        return {
            "synced": False,
            "reason": "bridge_missing",
            "packet_id": str(packet.get("packet_id") or ""),
        }
    try:
        bridge_rel = str(bridge_path.relative_to(repo_root))
    except ValueError:
        bridge_rel = DEFAULT_BRIDGE_REL
    try:
        worktree_hash = compute_worktree_hash_fn(
            repo_root=repo_root,
            excluded_rel_paths=(bridge_rel,),
        )

        def transform(_bridge_text: str) -> str:
            rendered, _metadata = render_bridge_projection_fn(
                review_state=review_state_payload,
                last_worktree_hash=worktree_hash,
            )
            return rendered

        rewrite_bridge_markdown(bridge_path, transform=transform)
    except (OSError, ValueError) as exc:
        return {
            "synced": False,
            "reason": f"sync_failed:{exc}",
            "packet_id": str(packet.get("packet_id") or ""),
        }
    return {
        "synced": True,
        "reason": "posted_current_instruction",
        "packet_id": str(packet.get("packet_id") or ""),
    }


def _posted_packet_drives_current_instruction(
    packet: dict[str, object],
    review_state_payload: dict[str, object],
) -> bool:
    packet_id = str(packet.get("packet_id") or "").strip()
    if not packet_id:
        return False
    queue = review_state_payload.get("queue")
    if not isinstance(queue, dict):
        return False
    source = queue.get("derived_next_instruction_source")
    if not isinstance(source, dict):
        return False
    return str(source.get("packet_id") or "").strip() == packet_id
