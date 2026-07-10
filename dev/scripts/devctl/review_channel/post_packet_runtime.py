"""Post-packet side effects that must run before projection refresh."""

from __future__ import annotations

from pathlib import Path

from .action_request_delivery import seed_action_request_delivery_receipt
from .agent_session_outcome_events import append_agent_session_outcome_for_packet
from .event_store import ReviewChannelArtifactPaths
from .packet_creation_binding import maybe_append_packet_creation_binding
from .remote_control_attachment_artifact import heartbeat_repo_remote_control_attachment
from .safe_auto_apply import append_safe_auto_apply_events


def finalize_post_packet(
    *,
    repo_root: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    written_event: dict[str, object],
    existing_events: list[dict[str, object]],
) -> dict[str, object]:
    """Run post-write receipts/outcomes and annotate the returned event."""
    outcome_event = append_agent_session_outcome_for_packet(
        repo_root=repo_root,
        artifact_paths=artifact_paths,
        packet_event=written_event,
        existing_events=[*existing_events, written_event],
    )
    heartbeat_repo_remote_control_attachment(
        repo_root=repo_root,
        provider=str(written_event.get("from_agent") or "").strip(),
        seen_at_utc=str(written_event.get("timestamp_utc") or "").strip(),
    )
    seed_action_request_delivery_receipt(
        artifact_root=Path(artifact_paths.artifact_root),
        packet=written_event,
    )
    binding_event = maybe_append_packet_creation_binding(
        repo_root=repo_root,
        artifact_paths=artifact_paths,
        packet_event=written_event,
        existing_events=[
            *existing_events,
            written_event,
            *([outcome_event] if outcome_event is not None else []),
        ],
    )
    auto_transition_events = append_safe_auto_apply_events(
        repo_root=repo_root,
        artifact_paths=artifact_paths,
        packet_event=written_event,
        existing_events=[
            *existing_events,
            written_event,
            *([outcome_event] if outcome_event is not None else []),
            *([binding_event] if binding_event is not None else []),
        ],
    )
    return _annotate_posted_event(
        written_event,
        outcome_event=outcome_event,
        binding_event=binding_event,
        auto_transition_events=auto_transition_events,
    )


def _annotate_posted_event(
    written_event: dict[str, object],
    *,
    outcome_event: dict[str, object] | None,
    binding_event: dict[str, object] | None,
    auto_transition_events: list[dict[str, object]],
) -> dict[str, object]:
    if outcome_event is None and binding_event is None and not auto_transition_events:
        return written_event
    annotated = dict(written_event)
    if outcome_event is not None:
        annotated["agent_session_outcome_event_id"] = outcome_event.get("event_id")
    if binding_event is not None:
        annotated["packet_creation_binding_event_id"] = binding_event.get("event_id")
    if auto_transition_events:
        annotated["safe_auto_apply_event_ids"] = [
            event.get("event_id") for event in auto_transition_events
        ]
    return annotated


__all__ = ["finalize_post_packet"]
