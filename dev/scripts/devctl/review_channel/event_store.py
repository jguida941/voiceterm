"""Artifact and event-log helpers for the review-channel packet flow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .state import DEFAULT_REVIEW_STATUS_DIR_REL, write_projection_bundle

DEFAULT_REVIEW_ARTIFACT_ROOT_REL = "dev/reports/review_channel"
DEFAULT_REVIEW_EVENT_LOG_REL = "dev/reports/review_channel/events/trace.ndjson"
DEFAULT_REVIEW_STATE_JSON_REL = "dev/reports/review_channel/state/latest.json"
DEFAULT_REVIEW_PROJECTIONS_DIR_REL = "dev/reports/review_channel/projections/latest"
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
    """Return True when event-backed review-channel artifacts already exist."""
    return Path(artifact_paths.event_log_path).exists() or Path(
        artifact_paths.state_path
    ).exists()


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
) -> None:
    """Append one event after duplicate idempotency protection."""
    idempotency_key = str(event.get("idempotency_key") or "").strip()
    if any(
        str(existing_event.get("idempotency_key") or "").strip() == idempotency_key
        for existing_event in existing_events
    ):
        raise ValueError(
            "Duplicate review-channel idempotency_key rejected: "
            f"{idempotency_key or '(missing)'}"
        )
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True))
        handle.write("\n")


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
    """Generate the next sequential event id."""
    return f"rev_evt_{len(events) + 1:04d}"


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
