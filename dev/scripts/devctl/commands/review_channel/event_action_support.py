"""Shared support for event-backed review-channel command actions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .event_watch_support import EventWatchContext, load_target_packets


@dataclass(frozen=True)
class EventActionContext:
    args: object
    repo_root: Path
    review_channel_path: Path
    artifact_paths: object
    build_event_report_fn: object


def run_inbox_like_action(
    *,
    context: EventActionContext,
    bundle,
    target_override: str | None = None,
    status_override: str | None = None,
    observe_action_requests: bool = True,
) -> tuple[dict, int]:
    """Run one inbox-like event query with optional target/status overrides."""
    if target_override is not None:
        context.args.target = target_override
    if status_override is not None and not getattr(context.args, "status", None):
        context.args.status = status_override
    bundle, packets = load_target_packets(
        context=EventWatchContext(
            args=context.args,
            bundle=bundle,
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            artifact_paths=context.artifact_paths,
        ),
        observe_action_requests=observe_action_requests,
    )
    return context.build_event_report_fn(
        args=context.args,
        bundle=bundle,
        packets=packets,
    )
