"""Delta section builder for ReviewSnapshot.

Split out of ``review_snapshot_sections`` so each module stays under the
code-shape soft limit. Owns only the commit-range aggregation that produces
a ``SnapshotDelta`` — file classification, bundle routing, risk tagging,
and authority-surface detection.
"""

from __future__ import annotations

from pathlib import Path

from .review_snapshot_git import (
    RawCommit,
    extract_checkpoint_markers,
    extract_mp_refs,
    file_stats_for_commit,
    first_body_excerpt,
)
from .review_snapshot_hints import (
    classify_bundle_lane,
    detect_authority_surfaces,
    detect_contract_mutations,
    detect_risk_addons,
)
from .review_snapshot_models import (
    CommitRow,
    FileStatRow,
    SnapshotDelta,
    SnapshotIdentity,
)


def build_delta(
    *,
    repo_root: Path,
    raw_commits: tuple[RawCommit, ...],
    identity: SnapshotIdentity,
    previous_head_sha: str,
) -> SnapshotDelta:
    """Return the aggregated delta section from raw commits + file stats."""
    commits: list[CommitRow] = []
    all_files: list[FileStatRow] = []
    bundle_classes_seen: list[str] = []
    risk_seen: list[str] = []
    authority_seen: list[str] = []

    for raw in raw_commits:
        commit_files = _classify_commit_files(repo_root, raw, bundle_classes_seen)
        commit_paths = tuple(row.path for row in commit_files)
        risk_addons = detect_risk_addons(commit_paths)
        authority = detect_authority_surfaces(commit_paths)
        contracts = detect_contract_mutations(commit_paths)
        for label in risk_addons:
            if label not in risk_seen:
                risk_seen.append(label)
        for path in authority:
            if path not in authority_seen:
                authority_seen.append(path)
        commits.append(
            _build_commit_row(raw, commit_files, risk_addons, authority, contracts)
        )
        all_files.extend(commit_files)

    files_agg = _aggregate_files(all_files)
    total_ins = sum(f.insertions for f in files_agg)
    total_del = sum(f.deletions for f in files_agg)
    return SnapshotDelta(
        from_sha=previous_head_sha,
        to_sha=identity.head_sha,
        commit_count=len(commits),
        files_changed_count=len(files_agg),
        total_insertions=total_ins,
        total_deletions=total_del,
        commits=tuple(commits),
        files=tuple(files_agg),
        bundle_classes_touched=tuple(bundle_classes_seen),
        risk_addons_triggered=tuple(risk_seen),
        authority_surfaces_touched=tuple(authority_seen),
    )


def _classify_commit_files(
    repo_root: Path,
    raw: RawCommit,
    bundle_classes_seen: list[str],
) -> list[FileStatRow]:
    rows: list[FileStatRow] = []
    for stat in file_stats_for_commit(repo_root, sha=raw.sha):
        classified = classify_bundle_lane(stat.path)
        rows.append(
            FileStatRow(
                path=stat.path,
                insertions=stat.insertions,
                deletions=stat.deletions,
                change_kind=stat.change_kind,
                bundle_class=classified,
            )
        )
        if classified not in bundle_classes_seen:
            bundle_classes_seen.append(classified)
    return rows


def _build_commit_row(
    raw: RawCommit,
    files: list[FileStatRow],
    risk_addons: tuple[str, ...],
    authority: tuple[str, ...],
    contracts: tuple[str, ...],
) -> CommitRow:
    return CommitRow(
        sha=raw.sha,
        sha_short=raw.sha_short,
        subject=raw.subject,
        author=raw.author,
        timestamp_utc=raw.timestamp_utc,
        files_changed=len(files),
        insertions=sum(f.insertions for f in files),
        deletions=sum(f.deletions for f in files),
        bundle_class=_primary_bundle(files),
        mp_refs=extract_mp_refs(f"{raw.subject}\n{raw.body}"),
        checkpoint_markers=extract_checkpoint_markers(raw.subject),
        risk_addons=risk_addons,
        authority_surfaces_touched=authority,
        contracts_mutated=contracts,
        body_excerpt=first_body_excerpt(raw.body),
    )


def _primary_bundle(files: list[FileStatRow]) -> str:
    if not files:
        return "unknown"
    counts: dict[str, int] = {}
    for row in files:
        counts[row.bundle_class] = counts.get(row.bundle_class, 0) + 1
    return max(counts.items(), key=lambda pair: pair[1])[0]


def _aggregate_files(all_files: list[FileStatRow]) -> list[FileStatRow]:
    aggregated: dict[str, list[int]] = {}
    kinds: dict[str, str] = {}
    classes: dict[str, str] = {}
    for row in all_files:
        bucket = aggregated.setdefault(row.path, [0, 0])
        bucket[0] += row.insertions
        bucket[1] += row.deletions
        kinds[row.path] = row.change_kind
        classes[row.path] = row.bundle_class
    return [
        FileStatRow(
            path=path,
            insertions=ins,
            deletions=dels,
            change_kind=kinds[path],
            bundle_class=classes[path],
        )
        for path, (ins, dels) in sorted(aggregated.items())
    ]


__all__ = ["build_delta"]
