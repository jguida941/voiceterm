"""Slice-counted continuation-anchor release helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from .session_termination_time import parse_utc

SLICE_COUNTED_RELEASE_MODES: frozenset[str] = frozenset(
    {"commit_count", "slice_counted"}
)
_COMMIT_SHA_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{7,40}(?![0-9a-fA-F])")


@dataclass(frozen=True, slots=True)
class SliceCountedAnchorStatus:
    configured: bool = False
    released: bool = False
    invalid: bool = False
    observed_count: int = 0
    required_count: int = 0

    @property
    def pending(self) -> bool:
        return self.configured and not self.invalid and not self.released


def slice_counted_anchor_status(
    anchor: Mapping[str, object],
    rows: tuple[Mapping[str, object], ...],
) -> SliceCountedAnchorStatus:
    release_mode = _anchor_release_text(anchor, "release_mode")
    if release_mode not in SLICE_COUNTED_RELEASE_MODES:
        return SliceCountedAnchorStatus()
    required_count = _anchor_release_int(anchor, "release_commit_count")
    posted_at = _text(anchor.get("posted_at"))
    if required_count <= 0 or parse_utc(posted_at) is None:
        return SliceCountedAnchorStatus(
            configured=True,
            invalid=True,
            required_count=required_count,
        )
    observed_count = _count_distinct_typed_commits_after(rows, posted_at)
    return SliceCountedAnchorStatus(
        configured=True,
        released=observed_count >= required_count,
        observed_count=observed_count,
        required_count=required_count,
    )


def _count_distinct_typed_commits_after(
    rows: tuple[Mapping[str, object], ...],
    since_utc: str,
) -> int:
    since_stamp = parse_utc(since_utc)
    if since_stamp is None:
        return 0
    seen_shas: set[str] = set()
    for row in rows:
        posted_at = parse_utc(row.get("posted_at"))
        if posted_at is None or posted_at <= since_stamp:
            continue
        for value in _typed_commit_values(row):
            seen_shas.update(_commit_sha_tokens(value))
    return len(seen_shas)


def _typed_commit_values(row: Mapping[str, object]) -> Iterable[object]:
    yield row.get("target_revision")
    yield row.get("evidence_ref")
    yield row.get("evidence_refs")
    yield row.get("commit_sha")
    source_identity = row.get("source_identity")
    if isinstance(source_identity, Mapping):
        yield source_identity.get("head_sha")
        yield source_identity.get("commit_sha")
        yield source_identity.get("target_revision")


def _commit_sha_tokens(value: object) -> Iterable[str]:
    if isinstance(value, Mapping):
        for nested in value.values():
            yield from _commit_sha_tokens(nested)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for nested in value:
            yield from _commit_sha_tokens(nested)
        return
    for match in _COMMIT_SHA_RE.finditer(_text(value)):
        yield match.group(0).lower()


def _anchor_release_text(anchor: Mapping[str, object], field: str) -> str:
    return _text(_anchor_release_field(anchor, field))


def _anchor_release_int(anchor: Mapping[str, object], field: str) -> int:
    try:
        return int(_anchor_release_field(anchor, field) or 0)
    except (TypeError, ValueError):
        return 0


def _anchor_release_field(anchor: Mapping[str, object], field: str) -> object:
    value = anchor.get(field)
    if value not in (None, ""):
        return value
    metadata = anchor.get("metadata")
    if isinstance(metadata, Mapping):
        return metadata.get(field)
    return None


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()

