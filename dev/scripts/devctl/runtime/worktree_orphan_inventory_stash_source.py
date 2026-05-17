"""Stash orphan source builders for inventory scans."""

from __future__ import annotations

from typing import NamedTuple, TypedDict

from .worktree_orphan_snapshot import OrphanSource, OrphanSourceClassification

MAX_STASH_FILES = 200


class StashEntry(NamedTuple):
    """Parsed `git stash list` row."""

    stash_ref: str
    commit_sha: str
    subject: str


class StashMetadata(TypedDict):
    stash_ref: str
    subject: str
    stash_sections: list[str]
    file_paths: list[str]
    truncated_file_paths: bool


def stash_entry_from_line(line: str) -> StashEntry | None:
    parts = line.split("\x1f", 2)
    if len(parts) != 3:
        return None

    return StashEntry(
        stash_ref=parts[0],
        commit_sha=parts[1],
        subject=parts[2],
    )


def build_stash_source(
    *,
    index: int,
    entry: StashEntry,
    sections: tuple[str, ...],
    files: tuple[str, ...],
) -> OrphanSource:
    return OrphanSource(
        source_id=f"source-stash-{index}",
        source_kind="stash_orphan",
        source_ref=f"stash:{entry.stash_ref}",
        head_sha=entry.commit_sha,
        dirty_path_count=len(files),
        status="unresolved",
        classification=stash_classification(),
        evidence_refs=("git stash list", "git rev-list --parents"),
        metadata=stash_metadata(
            stash_ref=entry.stash_ref,
            subject=entry.subject,
            sections=sections,
            files=files,
        ),
    )


def stash_classification() -> OrphanSourceClassification:
    return OrphanSourceClassification(
        state="stashed_work",
        load_bearing=True,
        governance_owner="git_stash",
        risk="hidden_unpublished_work",
        notes=("stash carries work outside current checkout/index",),
    )


def stash_metadata(
    *,
    stash_ref: str,
    subject: str,
    sections: tuple[str, ...],
    files: tuple[str, ...],
) -> StashMetadata:
    return StashMetadata(
        stash_ref=stash_ref,
        subject=subject,
        stash_sections=list(sections),
        file_paths=list(files[:MAX_STASH_FILES]),
        truncated_file_paths=len(files) > MAX_STASH_FILES,
    )


__all__ = ["build_stash_source", "stash_entry_from_line"]
