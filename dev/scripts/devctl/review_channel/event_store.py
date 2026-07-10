"""Artifact and event-log helpers for the review-channel packet flow."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..repo_packs import active_path_config
from ..runtime.correlation_spine import (
    causation_id_for_ref,
    correlation_id_for_ref,
    run_id_for_ref,
)
from .packet_post_idempotency import (
    is_idempotency_consumed_by_statuses,
    packet_posted_idempotency_key,
)

DEFAULT_REVIEW_ARTIFACT_ROOT_REL = active_path_config().review_artifact_root_rel
DEFAULT_REVIEW_EVENT_LOG_REL = active_path_config().review_event_log_rel
DEFAULT_REVIEW_STATE_JSON_REL = active_path_config().review_state_json_rel
DEFAULT_REVIEW_PROJECTIONS_DIR_REL = active_path_config().review_projections_dir_rel
DEFAULT_REVIEW_CHANNEL_SESSION_ID = "local-review"
DEFAULT_REVIEW_CHANNEL_PLAN_ID = "MP-355"
DEFAULT_PACKET_TTL_MINUTES = 30
PUSH_WINDOW_WRITE_SUSPENSION_FILENAME = "vcs_window_write_suspension.json"
DEFAULT_PUSH_WINDOW_TTL_SECONDS = 900


@dataclass
class _LockedEventLogSummary:
    row_count: int = 0
    max_event_index: int = 0
    max_packet_index: int = 0
    packet_posted_ids: set[str] = field(default_factory=set)
    packet_status_by_id: dict[str, str] = field(default_factory=dict)
    idempotency_non_packet_keys: set[str] = field(default_factory=set)
    idempotency_packet_ids_by_key: dict[str, list[str]] = field(default_factory=dict)
    target_packet_lineage: dict[str, str] = field(default_factory=dict)

    def next_event_id(self) -> str:
        return f"rev_evt_{self.max_event_index + 1:04d}"

    def next_packet_id(self) -> str:
        return f"rev_pkt_{self.max_packet_index + 1:04d}"


@dataclass(frozen=True)
class ReviewChannelArtifactPaths:
    """Resolved filesystem paths for the event-backed review-channel state."""

    artifact_root: str
    event_log_path: str
    state_path: str
    projections_root: str


@dataclass(frozen=True, slots=True)
class PushWindowWriteSuspension:
    """One active or recently released publisher-write suspension window."""

    window_id: str
    window_kind: str
    requested_by: str
    reason: str
    head_sha: str
    branch: str
    status: str
    started_at_utc: str
    expires_at_utc: str
    pid: int
    released_at_utc: str = ""
    contract_id: str = "PushWindowWriteSuspension"
    schema_version: int = 1


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


@contextmanager
def push_window_write_suspension(
    *,
    repo_root: Path,
    window_kind: str,
    requested_by: str,
    reason: str,
    head_sha: str = "",
    branch: str = "",
    ttl_seconds: int = DEFAULT_PUSH_WINDOW_TTL_SECONDS,
) -> Iterator[PushWindowWriteSuspension]:
    """Record a bounded VCS write window that publisher ticks must not refresh."""
    started = _utc_now()
    ttl = max(1, int(ttl_seconds or DEFAULT_PUSH_WINDOW_TTL_SECONDS))
    record = PushWindowWriteSuspension(
        window_id=f"{window_kind}:{started}:{os.getpid()}",
        window_kind=window_kind,
        requested_by=requested_by,
        reason=reason,
        head_sha=head_sha,
        branch=branch,
        status="active",
        started_at_utc=started,
        expires_at_utc=_format_utc(_parse_utc_required(started) + timedelta(seconds=ttl)),
        pid=os.getpid(),
    )
    _write_push_window_write_suspension(repo_root=repo_root, record=record)
    try:
        yield record
    finally:
        _write_push_window_write_suspension(
            repo_root=repo_root,
            record=replace(record, status="released", released_at_utc=_utc_now()),
        )


def active_push_window_write_suspension(
    *,
    repo_root: Path,
    now_utc: datetime | None = None,
) -> dict[str, object] | None:
    """Return the active suspension payload, if a live VCS window owns writes."""
    record = load_push_window_write_suspension(repo_root=repo_root)
    if record is None or record.status != "active":
        return None
    now = now_utc or datetime.now(timezone.utc)
    if _parse_utc_required(record.expires_at_utc) <= now:
        return None
    if record.pid and not _pid_is_alive(record.pid):
        return None
    return asdict(record)


def load_push_window_write_suspension(
    *,
    repo_root: Path,
) -> PushWindowWriteSuspension | None:
    """Load the latest publisher-write suspension record."""
    path = push_window_write_suspension_path(repo_root=repo_root)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return PushWindowWriteSuspension(
        window_id=_string(payload.get("window_id")),
        window_kind=_string(payload.get("window_kind")),
        requested_by=_string(payload.get("requested_by")),
        reason=_string(payload.get("reason")),
        head_sha=_string(payload.get("head_sha")),
        branch=_string(payload.get("branch")),
        status=_string(payload.get("status")),
        started_at_utc=_string(payload.get("started_at_utc")),
        expires_at_utc=_string(payload.get("expires_at_utc")),
        pid=_int(payload.get("pid")),
        released_at_utc=_string(payload.get("released_at_utc")),
        contract_id=_string(payload.get("contract_id")) or "PushWindowWriteSuspension",
        schema_version=_int(payload.get("schema_version")) or 1,
    )


def push_window_write_suspension_path(*, repo_root: Path) -> Path:
    """Return the state-side path for the publisher-write suspension record."""
    state_path = Path(resolve_artifact_paths(repo_root=repo_root).state_path)
    return state_path.parent / PUSH_WINDOW_WRITE_SUSPENSION_FILENAME


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
    return list(
        _iter_event_rows(
            events_path,
            fail_as_corrupt_log=False,
        )
    )


def append_event(
    events_path: Path,
    event: dict[str, object],
    *,
    existing_events: list[dict[str, object]],
) -> dict[str, object]:
    """Append one event with serialized event/packet allocation. Returns the written event.

    Acquires an exclusive file lock, re-reads the on-disk log to get the
    true latest state, allocates the event_id from that fresh state, and
    canonicalizes packet-posted identifiers from that same locked view before
    rechecking idempotency_key against the fresh log. This prevents duplicate
    event_id or auto-generated packet_id values when concurrent writers hold
    stale snapshots.
    """
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            event = dict(event)
            packet_id = str(event.get("packet_id") or "").strip()
            fresh_state = _summarize_events_under_lock(
                events_path,
                target_packet_id=packet_id,
            )

            # Allocate ids from fresh on-disk state, not stale caller snapshots.
            event["event_id"] = fresh_state.next_event_id()
            _finalize_packet_posted_identity(event, fresh_state)
            _finalize_packet_event_lineage(event, fresh_state)

            # Recheck idempotency_key against fresh state. Lifecycle-aware
            # for packet_posted retries; symmetric-strict for non-packet
            # events (the current event_type matters per rev_pkt_2255).
            idempotency_key = str(event.get("idempotency_key") or "").strip()
            if idempotency_key and _summary_consumes_idempotency_key(
                fresh_state,
                idempotency_key,
                current_event_type=str(event.get("event_type") or ""),
            ):
                raise ValueError(
                    "Duplicate review-channel idempotency_key rejected: "
                    f"{idempotency_key}"
                )

            handle.write(json.dumps(event, sort_keys=True) + "\n")
            handle.flush()
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
    return event


def _finalize_packet_posted_identity(
    event: dict[str, object],
    fresh_state: _LockedEventLogSummary,
) -> None:
    """Allocate packet-posted ids from the locked on-disk view."""
    if str(event.get("event_type") or "").strip() != "packet_posted":
        return

    packet_id = str(event.get("packet_id") or "").strip()
    if not packet_id:
        packet_id = fresh_state.next_packet_id()
        event["packet_id"] = packet_id
    elif packet_id in fresh_state.packet_posted_ids:
        raise ValueError(
            f"Duplicate review-channel packet_id rejected: {packet_id}"
        )
    if not str(event.get("semantic_zref") or "").strip():
        event["semantic_zref"] = f"packet:{packet_id}"

    trace_id = str(event.get("trace_id") or "").strip()
    if not trace_id:
        event["trace_id"] = _trace_id_from_event_count(
            fresh_state.row_count,
            from_agent=str(event.get("from_agent") or "").strip(),
        )
        trace_id = str(event.get("trace_id") or "").strip()

    if not str(event.get("correlation_id") or "").strip():
        event["correlation_id"] = correlation_id_for_ref("packet", packet_id)
    if not str(event.get("causation_id") or "").strip():
        event["causation_id"] = causation_id_for_ref("trace", trace_id)
    if not str(event.get("run_id") or "").strip():
        run_seed = str(event.get("controller_run_id") or "").strip() or str(
            event.get("session_id") or ""
        ).strip()
        if not run_seed:
            run_seed = packet_id
        event["run_id"] = run_id_for_ref("session", run_seed)

    event["idempotency_key"] = packet_posted_idempotency_key(
        event,
        idempotency_key,
    )


def _finalize_packet_event_lineage(
    event: dict[str, object],
    fresh_state: _LockedEventLogSummary,
) -> None:
    """Thread packet lineage through all packet-scoped event families."""
    packet_id = str(event.get("packet_id") or "").strip()
    if not packet_id:
        return
    source_event_id = str(event.get("source_packet_event_id") or "").strip()
    packet_lineage = fresh_state.target_packet_lineage
    if not str(event.get("correlation_id") or "").strip():
        event["correlation_id"] = packet_lineage.get(
            "correlation_id"
        ) or correlation_id_for_ref("packet", packet_id)
    if not str(event.get("causation_id") or "").strip():
        if source_event_id:
            event["causation_id"] = causation_id_for_ref("event", source_event_id)
        else:
            event["causation_id"] = packet_lineage.get(
                "causation_id"
            ) or causation_id_for_ref(
                "packet_event",
                f"{packet_id}:{event.get('event_type') or ''}",
            )
    if not str(event.get("run_id") or "").strip():
        run_seed = str(
            event.get("controller_run_id")
            or event.get("session_id")
            or packet_id
        ).strip()
        event["run_id"] = packet_lineage.get("run_id") or run_id_for_ref(
            "session",
            run_seed,
        )


def _read_events_under_lock(events_path: Path) -> list[dict[str, object]]:
    """Read all events from the NDJSON log (caller must hold the lock).

    Fails closed on malformed rows: raises ValueError instead of silently
    skipping, because the serialized append path must not allocate event_ids
    based on a partial/corrupt view of the log.
    """
    if not events_path.exists():
        return []
    return list(_iter_event_rows(events_path, fail_as_corrupt_log=True))


def _summarize_events_under_lock(
    events_path: Path,
    *,
    target_packet_id: str,
) -> _LockedEventLogSummary:
    """Summarize the event log without keeping every parsed event in memory."""
    if not events_path.exists():
        return _LockedEventLogSummary()

    summary = _LockedEventLogSummary()
    for row in _iter_event_rows(events_path, fail_as_corrupt_log=True):
        summary.row_count += 1
        _update_max_event_index(summary, row)

        event_type = str(row.get("event_type") or "").strip()
        packet_id = str(row.get("packet_id") or "").strip()
        if event_type == "packet_posted":
            _record_packet_posted(summary, packet_id)
        _record_packet_status(summary, event_type, packet_id)
        _record_idempotency(summary, row, event_type, packet_id)
        if target_packet_id and packet_id == target_packet_id:
            _record_target_lineage(summary, row)

    return summary


def _update_max_event_index(
    summary: _LockedEventLogSummary,
    row: dict[str, object],
) -> None:
    event_id = str(row.get("event_id") or "")
    if not event_id.startswith("rev_evt_"):
        return
    try:
        index = int(event_id[len("rev_evt_"):])
    except ValueError:
        return
    if index > summary.max_event_index:
        summary.max_event_index = index


def _record_packet_posted(
    summary: _LockedEventLogSummary,
    packet_id: str,
) -> None:
    if not packet_id:
        return
    summary.packet_posted_ids.add(packet_id)
    if not packet_id.startswith("rev_pkt_"):
        return
    try:
        index = int(packet_id[len("rev_pkt_"):])
    except ValueError:
        return
    if index > summary.max_packet_index:
        summary.max_packet_index = index


def _record_packet_status(
    summary: _LockedEventLogSummary,
    event_type: str,
    packet_id: str,
) -> None:
    if not packet_id:
        return
    status = _packet_status_for_event_type(event_type)
    if status:
        summary.packet_status_by_id[packet_id] = status


def _packet_status_for_event_type(event_type: str) -> str:
    if event_type == "packet_posted":
        return "pending"
    if event_type == "packet_acked":
        return "acked"
    if event_type == "packet_dismissed":
        return "dismissed"
    if event_type == "packet_applied":
        return "applied"
    if event_type == "packet_expired":
        return "archived"
    if event_type == "action_request_execution_failed":
        return "failed"
    if event_type == "action_request_apply_pending_after_execution":
        return "apply_pending_after_execution"
    return ""


def _record_idempotency(
    summary: _LockedEventLogSummary,
    row: dict[str, object],
    event_type: str,
    packet_id: str,
) -> None:
    key = str(row.get("idempotency_key") or "").strip()
    if not key:
        return
    if event_type == "packet_posted" and packet_id:
        summary.idempotency_packet_ids_by_key.setdefault(key, []).append(packet_id)
    else:
        summary.idempotency_non_packet_keys.add(key)


def _record_target_lineage(
    summary: _LockedEventLogSummary,
    row: dict[str, object],
) -> None:
    for field_name in ("correlation_id", "causation_id", "run_id"):
        value = str(row.get(field_name) or "").strip()
        if value:
            summary.target_packet_lineage[field_name] = value


def _summary_consumes_idempotency_key(
    summary: _LockedEventLogSummary,
    idempotency_key: str,
    *,
    current_event_type: str,
) -> bool:
    matched_packet_ids = summary.idempotency_packet_ids_by_key.get(
        idempotency_key,
        [],
    )
    return is_idempotency_consumed_by_statuses(
        non_packet_match=idempotency_key in summary.idempotency_non_packet_keys,
        matched_packet_statuses=(
            summary.packet_status_by_id.get(packet_id, "")
            for packet_id in matched_packet_ids
        ),
        current_event_type=current_event_type,
    )


def _iter_event_rows(
    events_path: Path,
    *,
    fail_as_corrupt_log: bool,
) -> Iterable[dict[str, object]]:
    """Yield event rows without materializing the raw trace text."""
    with events_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                if fail_as_corrupt_log:
                    raise ValueError(
                        f"Malformed event log at {events_path}:{line_number} — "
                        f"cannot allocate event_id from corrupt trace: {exc}"
                    ) from exc
                raise ValueError(
                    f"Invalid review-channel trace event at line {line_number}: {exc}"
                ) from exc
            if not isinstance(row, dict):
                if fail_as_corrupt_log:
                    raise ValueError(
                        f"Non-object row at {events_path}:{line_number} — "
                        f"event log rows must be JSON objects"
                    )
                raise ValueError(
                    f"Invalid review-channel trace event at line {line_number}: "
                    "expected top-level object"
                )
            yield row


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
    max_index = 0
    for event in events:
        if str(event.get("event_type") or "").strip() != "packet_posted":
            continue
        packet_id = str(event.get("packet_id") or "")
        if not packet_id.startswith("rev_pkt_"):
            continue
        try:
            index = int(packet_id[len("rev_pkt_"):])
        except ValueError:
            continue
        if index > max_index:
            max_index = index
    return f"rev_pkt_{max_index + 1:04d}"


def next_trace_id(
    events: list[dict[str, object]],
    *,
    from_agent: str,
) -> str:
    """Generate a readable trace id for one new packet."""
    return _trace_id_from_event_count(len(events), from_agent=from_agent)


def _trace_id_from_event_count(event_count: int, *, from_agent: str) -> str:
    next_index = event_count + 1
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


def _write_push_window_write_suspension(
    *,
    repo_root: Path,
    record: PushWindowWriteSuspension,
) -> Path:
    path = push_window_write_suspension_path(repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(
        json.dumps(asdict(record), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    os.replace(tmp_path, path)
    return path


def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _utc_now() -> str:
    return _format_utc(datetime.now(timezone.utc))


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _parse_utc_required(value: str) -> datetime:
    parsed = parse_utc(value)
    if parsed is None:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    return parsed


def _string(value: object) -> str:
    return str(value or "").strip()


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
