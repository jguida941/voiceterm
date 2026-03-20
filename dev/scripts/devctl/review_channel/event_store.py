"""Artifact and event-log helpers for the review-channel packet flow."""

from __future__ import annotations

import fcntl
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..repo_packs import active_path_config
from .state import DEFAULT_REVIEW_STATUS_DIR_REL, write_projection_bundle

DEFAULT_REVIEW_ARTIFACT_ROOT_REL = active_path_config().review_artifact_root_rel
DEFAULT_REVIEW_EVENT_LOG_REL = active_path_config().review_event_log_rel
DEFAULT_REVIEW_STATE_JSON_REL = active_path_config().review_state_json_rel
DEFAULT_REVIEW_PROJECTIONS_DIR_REL = active_path_config().review_projections_dir_rel
DEFAULT_REVIEW_CHANNEL_SESSION_ID = "local-review"
DEFAULT_REVIEW_CHANNEL_PLAN_ID = "MP-355"
DEFAULT_PACKET_TTL_MINUTES = 30


@dataclass(frozen=True)
class ReviewChannelArtifactPaths:
    """Resolved filesystem paths for the event-backed review-channel state."""

    artifact_root: str
    event_log_path: str
    state_path: str
    projections_root: str


def resolve_artifact_paths(
    *,
    repo_root: Path,
    artifact_root_rel: str | None = None,
    state_json_rel: str | None = None,
    projections_dir_rel: str | None = None,
) -> ReviewChannelArtifactPaths:
    """Resolve the canonical event-backed review-channel artifact paths."""
    artifact_root = repo_root / (artifact_root_rel or DEFAULT_REVIEW_ARTIFACT_ROOT_REL)
    state_path = repo_root / (state_json_rel or DEFAULT_REVIEW_STATE_JSON_REL)
    projections_root = repo_root / (
        projections_dir_rel or DEFAULT_REVIEW_PROJECTIONS_DIR_REL
    )
    return ReviewChannelArtifactPaths(
        artifact_root=str(artifact_root.resolve()),
        event_log_path=str((artifact_root / "events/trace.ndjson").resolve()),
        state_path=str(state_path.resolve()),
        projections_root=str(projections_root.resolve()),
    )


def event_state_exists(artifact_paths: ReviewChannelArtifactPaths) -> bool:
    """Return True when canonical event-backed state has been materialized."""
    return Path(artifact_paths.state_path).exists()


def summarize_review_state_errors(review_state: dict[str, object]) -> str | None:
    """Collapse reduced-state errors into one fallback-friendly summary."""
    errors = review_state.get("errors")
    if isinstance(errors, list):
        messages = [str(error).strip() for error in errors if str(error).strip()]
        if messages:
            return "; ".join(messages)
    if review_state.get("ok") is False:
        return "event-backed review-channel state was not ok"
    return None


def build_bridge_status_fallback_warning(detail: str) -> str:
    """Render one warning when status reads must fall back to the bridge."""
    reason = detail.strip() or "event-backed review-channel state was not ok"
    return (
        "Event-backed review-channel artifacts were unavailable or invalid while "
        "the markdown bridge remains the active authority; falling back to "
        f"bridge-backed status. Detail: {reason}"
    )


def load_events(events_path: Path) -> list[dict[str, object]]:
    """Load the append-only event log."""
    if not events_path.exists():
        return []
    events: list[dict[str, object]] = []
    for line_number, raw_line in enumerate(
        events_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid review-channel trace event at line {line_number}: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise ValueError(
                f"Invalid review-channel trace event at line {line_number}: "
                "expected top-level object"
            )
        events.append(payload)
    return events


def append_event(
    events_path: Path,
    event: dict[str, object],
    *,
    existing_events: list[dict[str, object]],
) -> dict[str, object]:
    """Append one event with serialized event-id allocation. Returns the written event.

    Acquires an exclusive file lock, re-reads the on-disk log to get the
    true latest state, allocates the event_id from that fresh state, and
    rechecks idempotency_key against the fresh log. This prevents duplicate
    event_id values when concurrent writers hold stale snapshots.
    """
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            # Re-read the on-disk log while holding the lock to get fresh state.
            fresh_events = _read_events_under_lock(events_path)

            # Allocate event_id from fresh on-disk state, not stale caller snapshot.
            event = dict(event)
            event["event_id"] = next_event_id(fresh_events)

            # Recheck idempotency_key against fresh state.
            idempotency_key = str(event.get("idempotency_key") or "").strip()
            if idempotency_key and any(
                str(e.get("idempotency_key") or "").strip() == idempotency_key
                for e in fresh_events
            ):
                raise ValueError(
                    "Duplicate review-channel idempotency_key rejected: "
                    f"{idempotency_key}"
                )

            # Recheck event_id uniqueness against fresh state.
            new_event_id = str(event.get("event_id") or "")
            if any(str(e.get("event_id") or "") == new_event_id for e in fresh_events):
                raise ValueError(
                    f"Duplicate review-channel event_id rejected: {new_event_id}"
                )

            handle.write(json.dumps(event, sort_keys=True) + "\n")
            handle.flush()
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
    return event


def _read_events_under_lock(events_path: Path) -> list[dict[str, object]]:
    """Read all events from the NDJSON log (caller must hold the lock).

    Fails closed on malformed rows: raises ValueError instead of silently
    skipping, because the serialized append path must not allocate event_ids
    based on a partial/corrupt view of the log.
    """
    if not events_path.exists():
        return []
    events: list[dict[str, object]] = []
    for line_num, line in enumerate(events_path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Malformed event log at {events_path}:{line_num} — "
                f"cannot allocate event_id from corrupt trace: {exc}"
            ) from exc
        if not isinstance(row, dict):
            raise ValueError(
                f"Non-object row at {events_path}:{line_num} — "
                f"event log rows must be JSON objects"
            )
        events.append(row)
    return events


def artifact_paths_to_dict(
    artifact_paths: ReviewChannelArtifactPaths,
) -> dict[str, str]:
    """Convert artifact paths into report-friendly JSON."""
    return asdict(artifact_paths)


def load_agent_registry(projections_root: Path) -> dict[str, object]:
    """Load the most recent registry snapshot when only state JSON exists."""
    registry_path = projections_root / "registry/agents.json"
    if not registry_path.exists():
        return {"schema_version": 1, "command": "review-channel", "agents": []}
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"schema_version": 1, "command": "review-channel", "agents": []}
    return payload if isinstance(payload, dict) else {
        "schema_version": 1,
        "command": "review-channel",
        "agents": [],
    }


def write_legacy_projection_mirror(
    *,
    repo_root: Path,
    canonical_projections_root: Path,
    review_state: dict[str, object],
    agent_registry: dict[str, object],
    trace_events: list[dict[str, object]],
) -> None:
    """Keep legacy `dev/reports/review_channel/latest` consumers alive."""
    legacy_root = (repo_root / DEFAULT_REVIEW_STATUS_DIR_REL).resolve()
    if legacy_root == canonical_projections_root.resolve():
        return
    write_projection_bundle(
        output_root=legacy_root,
        review_state=review_state,
        agent_registry=agent_registry,
        action="status",
        trace_events=trace_events,
    )


def next_event_id(events: list[dict[str, object]]) -> str:
    """Generate the next sequential event id.

    Reads the highest existing event_id from the list rather than using
    len(events) to avoid collisions when concurrent writers hold stale
    snapshots with different event counts.
    """
    max_index = 0
    for event in events:
        eid = str(event.get("event_id") or "")
        if eid.startswith("rev_evt_"):
            try:
                index = int(eid[len("rev_evt_"):])
                if index > max_index:
                    max_index = index
            except ValueError:
                pass
    return f"rev_evt_{max_index + 1:04d}"


def next_packet_id(events: list[dict[str, object]]) -> str:
    """Generate the next sequential packet id."""
    next_index = (
        sum(1 for event in events if event.get("event_type") == "packet_posted") + 1
    )
    return f"rev_pkt_{next_index:04d}"


def next_trace_id(
    events: list[dict[str, object]],
    *,
    from_agent: str,
) -> str:
    """Generate a readable trace id for one new packet."""
    next_index = len(events) + 1
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"trace_{stamp}_{from_agent}_{next_index:03d}"


def idempotency_key(*parts: object) -> str:
    """Generate a stable duplicate-suppression key."""
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def future_utc_timestamp(*, minutes: int) -> str:
    """Return one UTC expiry timestamp offset from now."""
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat().replace(
        "+00:00",
        "Z",
    )


def parse_utc(raw: object) -> datetime | None:
    """Parse one UTC ISO timestamp used in review artifacts."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
