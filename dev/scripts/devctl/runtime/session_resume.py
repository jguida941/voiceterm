"""Typed Session Resume parsing helpers for governed plan docs."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
from collections.abc import Sequence
from typing import Any

from ..markdown_sections import parse_markdown_sections
from ..text_utils import normalize_inline_markdown

_ITEM_RE = re.compile(r"^(?:[-*+]|\d+\.)\s+(?P<value>.+)$")
_HEADING_RE = re.compile(r"^###\s+(?P<value>.+?)\s*$")
_DATE_RE = re.compile(r"^(?P<value>\d{4}-\d{2}-\d{2})\b")
_LABEL_RE = re.compile(r"^(?P<label>[A-Za-z][A-Za-z0-9 /_-]{1,80}):\s*(?P<body>.+)$")
# Matched in order; longer tokens must come before their prefixes so `**`
# wins over `*` and `__` wins over `_`.
_LEADING_EMPHASIS_TOKENS: tuple[str, ...] = ("**", "__", "*", "_")


@dataclass(frozen=True, slots=True)
class SessionResumeEntry:
    """One typed item parsed from a plan's Session Resume section."""

    text: str
    item_kind: str = "bullet"
    subsection: str = ""
    label: str = ""
    date_hint: str = ""

    def to_dict(self) -> dict[str, object]:
        return dict(
            text=self.text,
            item_kind=self.item_kind,
            subsection=self.subsection,
            label=self.label,
            date_hint=self.date_hint,
        )


@dataclass(frozen=True, slots=True)
class SessionResumeState:
    """Typed continuity payload parsed from `## Session Resume`."""

    section_hash: str
    summary: str = ""
    current_status: str = ""
    current_goal: str = ""
    next_action: str = ""
    entries: tuple[SessionResumeEntry, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = dict(
            section_hash=self.section_hash,
            summary=self.summary,
            current_status=self.current_status,
            current_goal=self.current_goal,
            next_action=self.next_action,
        )
        payload["entries"] = [entry.to_dict() for entry in self.entries]
        return payload


def extract_session_resume_state(markdown_text: str) -> SessionResumeState | None:
    """Parse `## Session Resume` into a small typed continuity contract."""
    sections = parse_markdown_sections(markdown_text)
    section_text = sections.get("Session Resume", "").strip()
    if not section_text:
        return None

    entries = tuple(_parse_entries(section_text))
    current_status = _pick_labeled_entry(entries, "Current status")
    current_goal = _pick_labeled_entry(entries, "Current goal")
    next_action = _pick_labeled_entry(entries, "Next action")
    summary = current_goal or next_action or current_status or _first_entry_text(entries)

    return SessionResumeState(
        section_hash=sha256(section_text.encode("utf-8")).hexdigest()[:16],
        summary=summary,
        current_status=current_status,
        current_goal=current_goal,
        next_action=next_action,
        entries=entries,
    )


def session_resume_from_mapping(payload: dict[str, object]) -> SessionResumeState | None:
    """Restore SessionResumeState from a JSON-like mapping."""
    if not payload:
        return None
    raw_entries = payload.get("entries")
    entries: list[SessionResumeEntry] = []
    if isinstance(raw_entries, Sequence) and not isinstance(raw_entries, (str, bytes)):
        for row in raw_entries:
            if not isinstance(row, dict):
                continue
            entries.append(
                SessionResumeEntry(
                    text=_text(row.get("text")),
                    item_kind=_text(row.get("item_kind")) or "bullet",
                    subsection=_text(row.get("subsection")),
                    label=_text(row.get("label")),
                    date_hint=_text(row.get("date_hint")),
                )
            )
    return SessionResumeState(
        section_hash=_text(payload.get("section_hash")),
        summary=_text(payload.get("summary")),
        current_status=_text(payload.get("current_status")),
        current_goal=_text(payload.get("current_goal")),
        next_action=_text(payload.get("next_action")),
        entries=tuple(entries),
    )


def _parse_entries(section_text: str) -> list[SessionResumeEntry]:
    entries: list[SessionResumeEntry] = []
    subsection = ""
    paragraph: list[str] = []
    item_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        text = _normalize_block(paragraph)
        if text:
            entries.append(_build_entry(text, item_kind="paragraph", subsection=subsection))
        paragraph = []

    def flush_item() -> None:
        nonlocal item_lines
        text = _normalize_block(item_lines)
        if text:
            entries.append(_build_entry(text, item_kind="bullet", subsection=subsection))
        item_lines = []

    for raw_line in section_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            flush_item()
            flush_paragraph()
            continue

        heading_match = _HEADING_RE.match(stripped)
        if heading_match is not None:
            flush_item()
            flush_paragraph()
            subsection = heading_match.group("value").strip()
            continue

        item_match = _ITEM_RE.match(stripped)
        if item_match is not None:
            flush_item()
            flush_paragraph()
            item_lines = [item_match.group("value").strip()]
            continue

        if item_lines:
            item_lines.append(stripped)
            continue
        paragraph.append(stripped)

    flush_item()
    flush_paragraph()
    return entries


def _build_entry(
    text: str,
    *,
    item_kind: str,
    subsection: str,
) -> SessionResumeEntry:
    normalized = normalize_inline_markdown(text)
    # Authors commonly wrap the label in emphasis (`**Current goal:** ...`).
    # The raw regex requires a bare alpha start, so peel a leading token,
    # try the label match against the unwrapped head, and drop the matching
    # closing token from the body so it does not leak into typed fields.
    label = ""
    body = normalized
    unwrapped, leading_token = _strip_leading_emphasis(normalized)
    label_match = _LABEL_RE.match(unwrapped)
    if label_match is not None:
        label = label_match.group("label").strip()
        candidate_body = label_match.group("body").strip()
        if leading_token and candidate_body.startswith(leading_token):
            # `**Current goal:** Land X.` — the closing `**` sits at the
            # start of the body because `:` terminated the label regex.
            candidate_body = candidate_body[len(leading_token) :].lstrip()
        elif leading_token and candidate_body.endswith(leading_token):
            # `**Current goal: Land X.**` — the closing `**` wraps the
            # whole entry instead of just the label.
            candidate_body = candidate_body[: -len(leading_token)].rstrip()
        body = normalize_inline_markdown(candidate_body)
    date_match = _DATE_RE.match(body)
    return SessionResumeEntry(
        text=body,
        item_kind=item_kind,
        subsection=subsection,
        label=label,
        date_hint=date_match.group("value") if date_match is not None else "",
    )


def _strip_leading_emphasis(value: str) -> tuple[str, str]:
    """Peel a single leading markdown emphasis token off a short fragment."""
    for token in _LEADING_EMPHASIS_TOKENS:
        if value.startswith(token) and len(value) > len(token):
            return value[len(token) :].lstrip(), token
    return value, ""


def _normalize_block(lines: list[str]) -> str:
    return normalize_inline_markdown(
        " ".join(line.strip() for line in lines if line.strip())
    )


def _pick_labeled_entry(
    entries: tuple[SessionResumeEntry, ...],
    label: str,
) -> str:
    # Label-bound bullets (`- Current goal: ...`) always win over subsection
    # context so an author-written label beats an inherited heading name.
    lowered = label.casefold()
    for entry in entries:
        if entry.label.casefold() == lowered:
            return entry.text
    # Fallback: `### Current goal\n\n- bullet text` carries the label on the
    # subsection heading instead of each bullet. Pick the first bullet under
    # a matching subsection so typed continuity still binds.
    for entry in entries:
        if entry.subsection.casefold() == lowered and entry.text:
            return entry.text
    return ""


def _first_entry_text(entries: tuple[SessionResumeEntry, ...]) -> str:
    return entries[0].text if entries else ""


def _text(value: Any) -> str:
    return str(value or "").strip()


__all__ = [
    "SessionResumeEntry",
    "SessionResumeState",
    "extract_session_resume_state",
    "session_resume_from_mapping",
]
