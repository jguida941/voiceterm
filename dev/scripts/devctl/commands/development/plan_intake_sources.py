"""Source loading for ``develop ingest-intent``."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...repo_packs import active_path_config
from ...review_channel.event_reducer import reduce_events
from ...review_channel.event_reducer_inbox import packet_by_id
from ...review_channel.event_reducer_lanes import load_lane_assignments
from ...review_channel.event_store import load_events, resolve_artifact_paths
from .plan_intake_support import text


@dataclass(frozen=True, slots=True)
class PlanIntentSource:
    """One packet, file, or inline body used as plan-intent evidence."""

    kind: str
    ref: str
    body: str
    packet: Mapping[str, object] | None = None
    reason: str = ""

    @property
    def packet_payload(self) -> Mapping[str, object]:
        """Return packet metadata without leaking mutable defaults."""
        return self.packet or {}


def source_from_args(args: Any, *, repo_root: Path) -> PlanIntentSource:
    """Resolve the requested packet/file/body source."""
    packet_id = text(getattr(args, "packet_id", ""))
    if packet_id:
        return _source_from_packet(repo_root=repo_root, packet_id=packet_id)

    source_file = text(getattr(args, "source", ""))
    if source_file:
        return _source_from_file_args(
            args,
            repo_root=repo_root,
            path_text=source_file,
            default_kind="markdown_plan_file",
        )

    body_file = text(getattr(args, "body_file", ""))
    if body_file:
        return _source_from_file_args(
            args,
            repo_root=repo_root,
            path_text=body_file,
            default_kind="file",
        )

    return _source_from_inline_body(args)


def _source_from_packet(*, repo_root: Path, packet_id: str) -> PlanIntentSource:
    packet = _packet_from_review_state(repo_root=repo_root, packet_id=packet_id)
    if not packet:
        return PlanIntentSource(
            kind="packet",
            ref=f"packet:{packet_id}",
            body="",
            reason="packet_not_found",
        )
    return PlanIntentSource(
        kind="packet",
        ref=f"packet:{packet_id}",
        body=_packet_text(packet),
        packet=packet,
    )


def _source_from_inline_body(args: Any) -> PlanIntentSource:
    source_kind = text(getattr(args, "source_kind", "")) or "chat"
    source_ref = text(getattr(args, "source_ref", "")) or f"{source_kind}://current-session"
    body = text(getattr(args, "body", ""))
    if not body:
        return PlanIntentSource(
            kind=source_kind,
            ref=source_ref,
            body="",
            reason="missing_plan_source_body",
        )
    return PlanIntentSource(kind=source_kind, ref=source_ref, body=body)


def _source_from_file_args(
    args: Any,
    *,
    repo_root: Path,
    path_text: str,
    default_kind: str,
) -> PlanIntentSource:
    path = Path(path_text).expanduser()
    try:
        body = path.read_text(encoding="utf-8")
    except OSError as exc:
        return PlanIntentSource(
            kind=text(getattr(args, "source_kind", "")) or default_kind,
            ref=str(path),
            body="",
            reason=f"source_file_read_failed:{exc.__class__.__name__}",
        )
    return PlanIntentSource(
        kind=text(getattr(args, "source_kind", "")) or default_kind,
        ref=text(getattr(args, "source_ref", "")) or _repo_relative(path, repo_root),
        body=body,
    )


def _packet_from_review_state(
    *,
    repo_root: Path,
    packet_id: str,
) -> Mapping[str, object]:
    packet = _packet_from_review_state_projection(
        repo_root=repo_root,
        packet_id=packet_id,
    )
    if packet:
        return packet
    return _packet_from_event_log(repo_root=repo_root, packet_id=packet_id)


def _packet_from_review_state_projection(
    *,
    repo_root: Path,
    packet_id: str,
) -> Mapping[str, object]:
    path = repo_root / "dev/reports/review_channel/projections/latest/review_state.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    packets = payload.get("packets") if isinstance(payload, Mapping) else None
    if not isinstance(packets, list):
        return {}
    for packet in packets:
        if isinstance(packet, Mapping) and text(packet.get("packet_id")) == packet_id:
            return packet
    return {}


def _packet_from_event_log(
    *,
    repo_root: Path,
    packet_id: str,
) -> Mapping[str, object]:
    try:
        artifact_paths = resolve_artifact_paths(repo_root=repo_root)
        events = load_events(Path(artifact_paths.event_log_path))
    except (OSError, ValueError):
        return {}
    if not events:
        return {}
    review_channel_path = repo_root / active_path_config().review_channel_rel
    try:
        lanes = load_lane_assignments(review_channel_path)
        review_state, _registry = reduce_events(
            events=events,
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            lanes=lanes,
        )
    except (OSError, ValueError):
        return {}
    return packet_by_id(review_state, packet_id) or {}


def _packet_text(packet: Mapping[str, object]) -> str:
    return "\n".join(
        text(packet.get(field))
        for field in ("summary", "body", "requested_action", "policy_hint")
        if text(packet.get(field))
    )


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


__all__ = ["PlanIntentSource", "source_from_args"]
