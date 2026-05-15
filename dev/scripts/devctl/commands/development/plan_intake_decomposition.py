"""Packet-body decomposition helpers for plan-intent ingestion."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .plan_intake_titles import truncate
from .plan_intake_support import text

_MP_NEW_ROW_RE = re.compile(
    r"\b(?P<row_id>MP-NEW-P\d+(?:-[A-Z0-9][A-Z0-9._]*)*-S\d+)\b"
)
_MP_NEW_RANGE_RE = re.compile(
    r"\b(?P<prefix>MP-NEW-P\d+(?:-[A-Z0-9][A-Z0-9._]*)*-S)"
    r"(?P<start>\d+)\.\.S(?P<end>\d+)\b"
)
_JSON_TITLE_RE = re.compile(r'"title"\s*:\s*"(?P<title>[^"]+)"')


@dataclass(frozen=True, slots=True)
class DecomposedPlanRow:
    """One closure row inferred from a packet body."""

    row_id: str
    title: str
    source_line: int


def decomposed_packet_rows(body: str) -> tuple[DecomposedPlanRow, ...]:
    """Return MP-NEW closure rows named in a packet body.

    This is intentionally conservative: it only promotes packet text that
    already names an ``MP-NEW-*`` closure row or slice range. Packets without
    those refs keep the existing PKT-BIND fallback path.
    """
    lines = body.splitlines()
    rows: list[DecomposedPlanRow] = []
    seen: set[str] = set()
    for index, line in enumerate(lines, start=1):
        for row_id in _expanded_ranges(line):
            _append_row(
                rows,
                seen=seen,
                row_id=row_id,
                title=_title_for_line(row_id, line, lines, index),
                source_line=index,
            )
        line_without_ranges = _MP_NEW_RANGE_RE.sub("", line)
        for match in _MP_NEW_ROW_RE.finditer(line_without_ranges):
            row_id = match.group("row_id")
            if row_id in seen:
                continue
            _append_row(
                rows,
                seen=seen,
                row_id=row_id,
                title=_title_for_line(row_id, line, lines, index),
                source_line=index,
            )
    return tuple(rows)


def _append_row(
    rows: list[DecomposedPlanRow],
    *,
    seen: set[str],
    row_id: str,
    title: str,
    source_line: int,
) -> None:
    if row_id in seen:
        return
    seen.add(row_id)
    rows.append(
        DecomposedPlanRow(
            row_id=row_id,
            title=title or f"Materialize packet closure row {row_id}",
            source_line=source_line,
        )
    )


def _expanded_ranges(line: str) -> tuple[str, ...]:
    row_ids: list[str] = []
    for match in _MP_NEW_RANGE_RE.finditer(line):
        prefix = match.group("prefix")
        start = int(match.group("start"))
        end = int(match.group("end"))
        if end < start or end - start > 25:
            continue
        row_ids.extend(f"{prefix}{value}" for value in range(start, end + 1))
    return tuple(row_ids)


def _title_for_line(
    row_id: str,
    line: str,
    lines: list[str],
    one_based_index: int,
) -> str:
    json_title = _json_title_near(lines, one_based_index)
    if json_title:
        return truncate(json_title)
    after = line.split(row_id, 1)[-1]
    suffix = _suffix_title(after)
    if suffix:
        return truncate(suffix)
    before = line.split(row_id, 1)[0]
    prefix = _prefix_title(before)
    if prefix:
        return truncate(prefix)
    return f"Materialize packet closure row {row_id}"


def _json_title_near(lines: list[str], one_based_index: int) -> str:
    for line in lines[one_based_index : one_based_index + 4]:
        match = _JSON_TITLE_RE.search(line)
        if match is not None:
            return text(match.group("title"))
    return ""


def _suffix_title(value: str) -> str:
    suffix = text(value).strip("` ,")
    if suffix.startswith(")"):
        suffix = text(suffix[1:])
    if not suffix:
        return ""
    for delimiter in (" — ", " - ", ": "):
        if delimiter in suffix:
            return _clean_title(suffix.split(delimiter, 1)[1])
    if suffix.startswith(("→", "->")):
        return ""
    return _clean_title(suffix)


def _prefix_title(value: str) -> str:
    prefix = _clean_title(value)
    if not prefix:
        return ""
    if len(prefix) > 120:
        return ""
    return prefix


def _clean_title(value: str) -> str:
    return text(
        value.replace("**", "")
        .replace("`", "")
        .replace('"', "")
        .replace(",", "")
        .strip(" -*:()[]")
    )


__all__ = ["DecomposedPlanRow", "decomposed_packet_rows"]
