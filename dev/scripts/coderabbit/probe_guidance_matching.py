"""Matching logic for attaching probe guidance to CodeRabbit backlog items."""

from __future__ import annotations


def _normalize_symbol(value: object) -> str:
    return str(value or "").strip()


def parse_backlog_location(summary: object) -> tuple[str, int | None]:
    text = str(summary or "").strip()
    location, separator, _rest = text.partition(" - ")
    if not separator:
        return "", None
    path, line_sep, line_text = location.rpartition(":")
    if line_sep and line_text.isdigit():
        return path, int(line_text)
    return location, None


def item_candidate_paths(item: dict) -> set[str]:
    candidates: set[str] = set()
    for key in ("path", "file", "file_path"):
        value = str(item.get(key) or "").strip()
        if value:
            candidates.add(value)
    summary_path, _line = parse_backlog_location(item.get("summary"))
    if summary_path:
        candidates.add(summary_path)
    return candidates


def item_candidate_symbols(item: dict) -> set[str]:
    candidates: set[str] = set()
    for key in ("symbol", "target", "module"):
        value = _normalize_symbol(item.get(key))
        if value:
            candidates.add(value)
    return candidates


def item_candidate_span(item: dict) -> tuple[int | None, int | None]:
    raw_line = item.get("line")
    if isinstance(raw_line, int) and raw_line > 0:
        start = raw_line
    elif isinstance(raw_line, str) and raw_line.isdigit():
        start = int(raw_line)
    else:
        _summary_path, summary_line = parse_backlog_location(item.get("summary"))
        start = summary_line
    raw_end_line = item.get("end_line")
    if isinstance(raw_end_line, int) and raw_end_line >= int(start or 0):
        return start, raw_end_line
    if isinstance(raw_end_line, str) and raw_end_line.isdigit():
        parsed_end = int(raw_end_line)
        if start is not None and parsed_end >= start:
            return start, parsed_end
    if start is not None:
        return start, start
    return None, None


def line_matches(
    entry: dict[str, object],
    item_start: int | None,
    item_end: int | None,
) -> bool:
    if item_start is None:
        return True
    target_end = item_end if item_end is not None else item_start
    start = entry.get("line")
    end = entry.get("end_line")
    if not isinstance(start, int):
        return True
    if not isinstance(end, int):
        end = start
    return not (end < item_start or start > target_end)


def symbol_matches(entry: dict[str, object], candidate_symbols: set[str]) -> bool:
    if not candidate_symbols:
        return True
    entry_symbol = _normalize_symbol(entry.get("symbol"))
    if not entry_symbol:
        return True
    return entry_symbol in candidate_symbols


def _sort_key(
    row: dict[str, object],
    *,
    candidate_symbols: set[str],
    item_start: int | None,
) -> tuple[int, int, str, str]:
    severity_rank = {"high": 0, "medium": 1, "low": 2}.get(
        str(row.get("severity") or "medium"),
        3,
    )
    entry_symbol = _normalize_symbol(row.get("symbol"))
    symbol_rank = 0 if entry_symbol and entry_symbol in candidate_symbols else 1
    row_line = row.get("line")
    if item_start is None or not isinstance(row_line, int):
        line_distance = 0
    else:
        line_distance = abs(row_line - item_start)
    return (
        severity_rank,
        symbol_rank,
        line_distance,
        str(row.get("file_path") or ""),
        str(row.get("probe") or ""),
    )


def select_item_probe_guidance(
    item: dict,
    entries: list[dict[str, object]],
) -> list[dict[str, object]]:
    candidate_paths = item_candidate_paths(item)
    if not candidate_paths:
        return []
    candidate_symbols = item_candidate_symbols(item)
    item_start, item_end = item_candidate_span(item)
    ordered = sorted(
        entries,
        key=lambda row: _sort_key(
            row,
            candidate_symbols=candidate_symbols,
            item_start=item_start,
        ),
    )
    matched: list[dict[str, object]] = []
    seen: set[str] = set()
    for entry in ordered:
        file_path = str(entry.get("file_path") or "").strip()
        ai_instruction = str(entry.get("ai_instruction") or "").strip()
        if file_path not in candidate_paths or not ai_instruction:
            continue
        if not symbol_matches(entry, candidate_symbols):
            continue
        if not line_matches(entry, item_start, item_end) or ai_instruction in seen:
            continue
        seen.add(ai_instruction)
        matched.append(entry)
        if len(matched) >= 2:
            break
    return matched
