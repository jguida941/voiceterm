"""Support helpers for implementer-side review wait state."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from ...review_channel.events import filter_inbox_packets, load_or_refresh_event_bundle
from ...review_channel.handoff import extract_bridge_snapshot
from ..review_channel_command import RuntimePaths
from ._bridge_poll import BridgePollResult, _bridge_poll_errors


def build_typed_reviewer_token(
    poll: BridgePollResult,
    *,
    latest_pending_packet_id: str = "",
) -> str:
    """Build a deterministic wake token from typed bridge-poll fields."""
    payload = "\0".join(
        [
            poll.turn_state_token,
            latest_pending_packet_id,
        ]
    ).strip("\0")
    if not payload:
        return ""
    return sha256(payload.encode("utf-8")).hexdigest()


def validate_wait_bridge_content(bridge_text: str) -> list[str]:
    """Return non-ACK bridge validation errors. Empty list = content is valid."""
    return _bridge_poll_errors(extract_bridge_snapshot(bridge_text))


def load_pending_claude_packets(
    repo_root: Path,
    paths: RuntimePaths,
) -> list[dict[str, object]]:
    """Return the newest pending packets targeted at Claude, if available."""
    if paths.review_channel_path is None or paths.artifact_paths is None:
        return []
    try:
        bundle = load_or_refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=paths.review_channel_path,
            artifact_paths=paths.artifact_paths,
        )
    except ValueError:
        return []
    return filter_inbox_packets(
        bundle.review_state,
        target="claude",
        status="pending",
        limit=1,
    )


def latest_pending_packet_id(packets: list[dict[str, object]]) -> str:
    """Return the newest pending Claude-targeted packet id."""
    if not packets:
        return ""
    latest = packets[0]
    if not isinstance(latest, dict):
        return ""
    return str(latest.get("packet_id") or "").strip()
