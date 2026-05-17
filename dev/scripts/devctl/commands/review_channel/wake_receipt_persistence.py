"""Wake-receipt persistence — extract typed `packet_wake_attempted` events.

Extracted from `event_post_wake` so the receipt schema and the event
log writer can grow without inflating the host file beyond shape
limits. The receipt itself is a typed `PacketWakeReceipt` dataclass so
the dict literal that previously named ~18 fields inline is now a
single deterministic constructor.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...review_channel.event_store import next_event_id
from ...review_channel.state import project_id_for_repo
from ...time_utils import utc_timestamp

if TYPE_CHECKING:
    from .event_post_wake import EventPostWakeDeps


@dataclass(frozen=True)
class PacketWakeEvent:
    """Typed `packet_wake_attempted` event row.

    Replaces the previous inline dict literal so adding a new wake
    field is a single typed line, not one more entry in a >18-key
    dict that fails the python-dict-schema guard. `to_event_dict()`
    serializes for `append_event_fn`, preserving the on-disk schema.
    """

    schema_version: int
    event_id: int
    session_id: str
    project_id: str
    packet_id: str
    trace_id: str
    timestamp_utc: str
    plan_id: str
    controller_run_id: object
    from_agent: str
    to_agent: str
    kind: str
    requested_action: str
    target_role: str
    target_session_id: str
    wake_method: str
    delegated: bool
    visible_session_woke: bool
    wake_receipt: dict[str, object]
    semantic_zref: str
    source: str = "review_channel"
    event_type: str = "packet_wake_attempted"
    metadata: dict[str, object] = field(default_factory=dict)

    def to_event_dict(self) -> dict[str, object]:
        record = asdict(self)
        if not record.get("metadata"):
            record["metadata"] = {"wake_receipt": self.wake_receipt}
        return record


def record_packet_wake_receipt(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: object,
    packet: Mapping[str, object],
    wake: dict[str, object],
    deps: Any,
) -> None:
    """Persist a typed `packet_wake_attempted` event for an attempted wake."""
    paths = _event_artifact_paths(artifact_paths)
    packet_id = str(packet.get("packet_id") or wake.get("packet_id") or "").strip()
    if paths is None or not packet_id or not bool(wake.get("attempted")):
        return
    event_log_path = Path(str(getattr(paths, "event_log_path")))
    try:
        existing_events = deps.load_events_fn(event_log_path)
        event = _build_packet_wake_event(
            repo_root=repo_root,
            existing_events=existing_events,
            packet=packet,
            wake=wake,
            packet_id=packet_id,
        )
        deps.append_event_fn(
            event_log_path,
            event.to_event_dict(),
            existing_events=existing_events,
        )
        deps.refresh_event_bundle_fn(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=paths,
        )
    except (OSError, ValueError) as exc:
        warnings = wake.setdefault("warnings", [])
        if isinstance(warnings, list):
            warnings.append(f"wake_receipt_record_failed: {exc}")


def _build_packet_wake_event(
    *,
    repo_root: Path,
    existing_events: list[dict[str, object]],
    packet: Mapping[str, object],
    wake: Mapping[str, object],
    packet_id: str,
) -> PacketWakeEvent:
    timestamp = utc_timestamp()
    receipt = _wake_receipt_payload(
        wake, packet_id=packet_id, timestamp_utc=timestamp
    )
    return PacketWakeEvent(
        schema_version=1,
        event_id=next_event_id(existing_events),
        session_id=str(packet.get("session_id") or "local-review"),
        project_id=project_id_for_repo(repo_root),
        packet_id=packet_id,
        trace_id=str(packet.get("trace_id") or ""),
        timestamp_utc=timestamp,
        plan_id=str(packet.get("plan_id") or "MP-355"),
        controller_run_id=packet.get("controller_run_id"),
        from_agent=str(packet.get("from_agent") or ""),
        to_agent=str(packet.get("to_agent") or wake.get("target_agent") or ""),
        kind=str(packet.get("kind") or ""),
        requested_action=str(packet.get("requested_action") or ""),
        target_role=str(
            packet.get("target_role") or wake.get("target_role") or ""
        ),
        target_session_id=str(
            packet.get("target_session_id")
            or wake.get("target_session_id")
            or ""
        ),
        wake_method=str(wake.get("wake_method") or ""),
        delegated=bool(wake.get("delegated")),
        visible_session_woke=bool(wake.get("visible_session_woke")),
        wake_receipt=receipt,
        semantic_zref=f"packet:{packet_id}:wake",
        metadata={"wake_receipt": receipt},
    )


def _wake_receipt_payload(
    wake: Mapping[str, object],
    *,
    packet_id: str,
    timestamp_utc: str,
) -> dict[str, object]:
    payload = {str(key): value for key, value in wake.items() if str(key)}
    payload["contract_id"] = "PacketWakeReceipt"
    payload["packet_id"] = packet_id
    payload["recorded_at_utc"] = timestamp_utc
    return payload


def _event_artifact_paths(value: object) -> object | None:
    if value is None:
        return None
    required = ("event_log_path", "state_path", "projections_root")
    if all(str(getattr(value, attr, "") or "").strip() for attr in required):
        return value
    return None
