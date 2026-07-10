"""Work publication ledger and baseline typed contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

from .value_coercion import (
    coerce_int,
    coerce_mapping,
    coerce_mapping_items,
    coerce_string,
    coerce_string_items,
)
from .worktree_orphan_types import WORK_PUBLICATION_EVENT_KINDS, enum_value


@dataclass(frozen=True, slots=True)
class WorkPublicationLedgerHeader:
    """Stable header for one checkout publication ledger."""

    ledger_id: str
    checkout_fingerprint: str
    checkout_path: str
    git_dir: str
    event_log_path: str
    state_path: str
    created_at_utc: str = ""
    updated_at_utc: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class WorkPublicationLedgerEvent:
    """Append-only event row for work publication state."""

    event_id: str
    event_kind: str
    timestamp_utc: str
    checkout_fingerprint: str
    commit_sha: str = ""
    pipeline_id: str = ""
    parent_event_id: str = ""
    payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["payload"] = dict(self.payload)
        return payload


@dataclass(frozen=True, slots=True)
class PublicationEpisode:
    """Publication episode keyed by commit SHA and pipeline id."""

    commit_sha: str
    pipeline_id: str
    status: str
    started_at_utc: str = ""
    updated_at_utc: str = ""
    carries_unpublished: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["carries_unpublished"] = list(self.carries_unpublished)
        return payload


@dataclass(frozen=True, slots=True)
class WorkPublicationLedger:
    """Derived publication-ledger state for one checkout."""

    header: WorkPublicationLedgerHeader
    episodes: tuple[PublicationEpisode, ...] = ()
    latest_event_id: str = ""
    unpublished_commits: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = "WorkPublicationLedger"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["header"] = self.header.to_dict()
        payload["episodes"] = [episode.to_dict() for episode in self.episodes]
        payload["unpublished_commits"] = list(self.unpublished_commits)
        return payload


@dataclass(frozen=True, slots=True)
class WorktreeBaseline:
    """Managed ledger record emitted by governed commit boundaries."""

    baseline_id: str
    checkout_fingerprint: str
    baseline_head_sha: str
    baseline_snapshot_id: str
    recorded_at_utc: str
    recording_lease_id: str
    schema_version: int = 1
    contract_id: str = "WorktreeBaseline"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def work_publication_ledger_header_from_mapping(
    value: object,
) -> WorkPublicationLedgerHeader | None:
    payload = coerce_mapping(value)
    if not payload:
        return None
    ledger_id = coerce_string(payload.get("ledger_id"))
    checkout_fingerprint = coerce_string(payload.get("checkout_fingerprint"))
    if not ledger_id or not checkout_fingerprint:
        return None
    return WorkPublicationLedgerHeader(
        ledger_id=ledger_id,
        checkout_fingerprint=checkout_fingerprint,
        checkout_path=coerce_string(payload.get("checkout_path")),
        git_dir=coerce_string(payload.get("git_dir")),
        event_log_path=coerce_string(payload.get("event_log_path")),
        state_path=coerce_string(payload.get("state_path")),
        created_at_utc=coerce_string(payload.get("created_at_utc")),
        updated_at_utc=coerce_string(payload.get("updated_at_utc")),
    )


def work_publication_event_from_mapping(
    value: object,
) -> WorkPublicationLedgerEvent | None:
    payload = coerce_mapping(value)
    if not payload:
        return None

    event_id = coerce_string(payload.get("event_id"))
    checkout_fingerprint = coerce_string(payload.get("checkout_fingerprint"))
    if not event_id or not checkout_fingerprint:
        return None

    event_kind = enum_value(
        coerce_string(payload.get("event_kind")),
        allowed=WORK_PUBLICATION_EVENT_KINDS,
        default="commit_recorded",
    )

    return WorkPublicationLedgerEvent(
        event_id=event_id,
        event_kind=event_kind,
        timestamp_utc=coerce_string(payload.get("timestamp_utc")),
        checkout_fingerprint=checkout_fingerprint,
        commit_sha=coerce_string(payload.get("commit_sha")),
        pipeline_id=coerce_string(payload.get("pipeline_id")),
        parent_event_id=coerce_string(payload.get("parent_event_id")),
        payload=dict(coerce_mapping(payload.get("payload"))),
    )


def publication_episode_from_mapping(value: object) -> PublicationEpisode | None:
    payload = coerce_mapping(value)
    if not payload:
        return None
    commit_sha = coerce_string(payload.get("commit_sha"))
    pipeline_id = coerce_string(payload.get("pipeline_id"))
    if not commit_sha or not pipeline_id:
        return None
    return PublicationEpisode(
        commit_sha=commit_sha,
        pipeline_id=pipeline_id,
        status=coerce_string(payload.get("status")) or "unknown",
        started_at_utc=coerce_string(payload.get("started_at_utc")),
        updated_at_utc=coerce_string(payload.get("updated_at_utc")),
        carries_unpublished=coerce_string_items(payload.get("carries_unpublished")),
    )


def work_publication_ledger_from_mapping(
    value: object,
) -> WorkPublicationLedger | None:
    payload = coerce_mapping(value)
    if not payload:
        return None
    header = work_publication_ledger_header_from_mapping(payload.get("header"))
    if header is None:
        return None
    return WorkPublicationLedger(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=(
            coerce_string(payload.get("contract_id")) or "WorkPublicationLedger"
        ),
        header=header,
        episodes=tuple(_parsed_episodes(payload)),
        latest_event_id=coerce_string(payload.get("latest_event_id")),
        unpublished_commits=coerce_string_items(payload.get("unpublished_commits")),
    )


def worktree_baseline_from_mapping(value: object) -> WorktreeBaseline | None:
    payload = coerce_mapping(value)
    if not payload:
        return None
    baseline_id = coerce_string(payload.get("baseline_id"))
    checkout_fingerprint = coerce_string(payload.get("checkout_fingerprint"))
    if not baseline_id or not checkout_fingerprint:
        return None
    return WorktreeBaseline(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=coerce_string(payload.get("contract_id")) or "WorktreeBaseline",
        baseline_id=baseline_id,
        checkout_fingerprint=checkout_fingerprint,
        baseline_head_sha=coerce_string(payload.get("baseline_head_sha")),
        baseline_snapshot_id=coerce_string(payload.get("baseline_snapshot_id")),
        recorded_at_utc=coerce_string(payload.get("recorded_at_utc")),
        recording_lease_id=coerce_string(payload.get("recording_lease_id")),
    )


def _parsed_episodes(payload: Mapping[str, object]) -> tuple[PublicationEpisode, ...]:
    episodes: list[PublicationEpisode] = []
    for item in coerce_mapping_items(payload.get("episodes")):
        episode = publication_episode_from_mapping(item)
        if episode is not None:
            episodes.append(episode)
    return tuple(episodes)


__all__ = [
    "PublicationEpisode",
    "WorkPublicationLedger",
    "WorkPublicationLedgerEvent",
    "WorkPublicationLedgerHeader",
    "WorktreeBaseline",
    "publication_episode_from_mapping",
    "work_publication_event_from_mapping",
    "work_publication_ledger_from_mapping",
    "worktree_baseline_from_mapping",
]
