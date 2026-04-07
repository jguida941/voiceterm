"""Why/reasoning extraction for ReviewSnapshot commits.

Deterministically stitches commit messages, MP references, active plan docs,
and engineering-evolution entries into one ``WhyRecord`` per commit. Every
source is a repo-owned typed/markdown artifact — no chat memory, no prose
guessing.

The extractor answers the reviewer's core question: *why did this land?* —
by linking a commit SHA to its MP scope, the owning plan document, and the
post-hoc rationale from ``dev/history/ENGINEERING_EVOLUTION.md``.
"""

from __future__ import annotations

import re
from pathlib import Path

from .review_snapshot_git import RawCommit, extract_checkpoint_markers, extract_mp_refs
from .review_snapshot_models import WhyRecord


_MASTER_PLAN_REL = "dev/active/MASTER_PLAN.md"
_INDEX_REL = "dev/active/INDEX.md"
_EVOLUTION_REL = "dev/history/ENGINEERING_EVOLUTION.md"
_ACTIVE_PLAN_DIR_REL = "dev/active"
_INDEX_ROW_PATTERN = re.compile(r"^\|\s*`([^`]+)`", re.MULTILINE)
_EVOLUTION_HEADING_PATTERN = re.compile(
    r"^###\s+(\d{4}-\d{2}-\d{2})\s*[-–]\s*(.+)$", re.MULTILINE
)


def build_why_record(
    commit: RawCommit,
    *,
    repo_root: Path,
    plan_index: dict[str, tuple[str, ...]],
    evolution_entries: tuple[tuple[str, str, str], ...],
) -> WhyRecord:
    """Return a typed WhyRecord stitching commit → MP → plan → evolution."""
    mp_refs = extract_mp_refs(f"{commit.subject}\n{commit.body}")
    checkpoint_markers = extract_checkpoint_markers(commit.subject)
    linked_docs = _linked_plan_docs(mp_refs, plan_index)
    rationale = _match_evolution_entry(mp_refs, commit.timestamp_utc, evolution_entries)
    summary = _build_summary(
        subject=commit.subject,
        mp_refs=mp_refs,
        linked_docs=linked_docs,
        has_rationale=bool(rationale),
    )
    body_excerpt = _first_body_paragraph(commit.body)
    return WhyRecord(
        commit_sha=commit.sha,
        commit_sha_short=commit.sha_short,
        subject=commit.subject,
        mp_refs=mp_refs,
        checkpoint_markers=checkpoint_markers,
        body_excerpt=body_excerpt,
        linked_plan_docs=linked_docs,
        evolution_rationale=rationale,
        summary=summary,
    )


def load_plan_index(repo_root: Path) -> dict[str, tuple[str, ...]]:
    """Return ``{MP-id: (plan_doc_path, ...)}`` parsed from INDEX.md.

    The INDEX.md file is a markdown table with a ``MP scope`` column. We scan
    each row, extract the first backtick path (the plan doc), and associate
    it with each MP-NNN mentioned in the row.
    """
    index_path = repo_root / _INDEX_REL
    if not index_path.is_file():
        return {}
    try:
        text = index_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    mapping: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        match = _INDEX_ROW_PATTERN.search(line)
        if not match:
            continue
        plan_path = match.group(1).strip()
        if not plan_path or not plan_path.startswith(_ACTIVE_PLAN_DIR_REL):
            continue
        mp_ids = extract_mp_refs(line)
        for mp_id in mp_ids:
            bucket = mapping.setdefault(mp_id, [])
            if plan_path not in bucket:
                bucket.append(plan_path)
    return {mp_id: tuple(paths) for mp_id, paths in mapping.items()}


def load_evolution_entries(
    repo_root: Path, *, limit: int = 12
) -> tuple[tuple[str, str, str], ...]:
    """Return the most recent entries from ENGINEERING_EVOLUTION.md.

    Each entry is ``(iso_date, heading_title, rationale_excerpt)``. The
    rationale excerpt is the first 400 characters of body text immediately
    following the heading. We cap the list so the parser stays bounded even
    as the evolution log grows.
    """
    evolution_path = repo_root / _EVOLUTION_REL
    if not evolution_path.is_file():
        return ()
    try:
        text = evolution_path.read_text(encoding="utf-8")
    except OSError:
        return ()
    headings = list(_EVOLUTION_HEADING_PATTERN.finditer(text))
    if not headings:
        return ()
    entries: list[tuple[str, str, str]] = []
    for index, match in enumerate(headings[:limit]):
        date_iso = match.group(1)
        title = match.group(2).strip()
        start = match.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body_slice = text[start:end].strip()
        rationale = _trim_to_length(body_slice, limit=400)
        entries.append((date_iso, title, rationale))
    return tuple(entries)


def active_mp_summaries_from_master_plan(
    repo_root: Path, *, max_entries: int = 10
) -> tuple[str, ...]:
    """Return short excerpts mentioning active MP IDs from MASTER_PLAN.md.

    MASTER_PLAN.md is large and prose-structured; we just scan for lines that
    mention ``MP-NNN`` and return the first ``max_entries`` distinct ones.
    This gives the external reviewer concrete anchors into the plan without
    shipping the entire tracker.
    """
    plan_path = repo_root / _MASTER_PLAN_REL
    if not plan_path.is_file():
        return ()
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError:
        return ()
    seen_mps: set[str] = set()
    summaries: list[str] = []
    for line in text.splitlines():
        mps = extract_mp_refs(line)
        if not mps:
            continue
        primary = mps[0]
        if primary in seen_mps:
            continue
        trimmed = line.strip().lstrip("-*# ").strip()
        if not trimmed:
            continue
        seen_mps.add(primary)
        summaries.append(_trim_to_length(trimmed, limit=220))
        if len(summaries) >= max_entries:
            break
    return tuple(summaries)


def _linked_plan_docs(
    mp_refs: tuple[str, ...],
    plan_index: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    if not mp_refs:
        return ()
    collected: list[str] = []
    for mp_id in mp_refs:
        for path in plan_index.get(mp_id, ()):
            if path not in collected:
                collected.append(path)
    return tuple(collected)


def _match_evolution_entry(
    mp_refs: tuple[str, ...],
    commit_iso: str,
    entries: tuple[tuple[str, str, str], ...],
) -> str:
    if not entries:
        return ""
    # 1. Prefer an entry whose title mentions one of the commit's MP refs.
    for _date, title, rationale in entries:
        if any(mp_id in title for mp_id in mp_refs):
            return rationale
    # 2. Otherwise fall back to the entry whose date matches the commit date.
    commit_date = commit_iso[:10] if commit_iso else ""
    if commit_date:
        for entry_date, _title, rationale in entries:
            if entry_date == commit_date:
                return rationale
    return ""


def _first_body_paragraph(body: str) -> str:
    if not body:
        return ""
    lines: list[str] = []
    for raw in body.splitlines():
        stripped = raw.rstrip()
        if not stripped:
            if lines:
                break
            continue
        lines.append(stripped)
        if len(lines) >= 6:
            break
    return "\n".join(lines)


def _build_summary(
    *,
    subject: str,
    mp_refs: tuple[str, ...],
    linked_docs: tuple[str, ...],
    has_rationale: bool,
) -> str:
    parts: list[str] = []
    if subject:
        parts.append(subject)
    if mp_refs:
        parts.append(f"MPs: {', '.join(mp_refs)}")
    if linked_docs:
        docs = ", ".join(Path(p).name for p in linked_docs)
        parts.append(f"plan: {docs}")
    if has_rationale:
        parts.append("evolution rationale linked")
    return " | ".join(parts)


def _trim_to_length(text: str, *, limit: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


__all__ = [
    "active_mp_summaries_from_master_plan",
    "build_why_record",
    "load_evolution_entries",
    "load_plan_index",
]
