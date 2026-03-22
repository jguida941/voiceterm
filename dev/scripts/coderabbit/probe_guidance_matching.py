"""Matching logic for attaching probe guidance to CodeRabbit backlog items."""

from __future__ import annotations


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
    for key in ("path", "file"):
        value = str(item.get(key) or "").strip()
        if value:
            candidates.add(value)
    summary_path, _line = parse_backlog_location(item.get("summary"))
    if summary_path:
        candidates.add(summary_path)
    return candidates


def item_candidate_line(item: dict) -> int | None:
    _summary_path, summary_line = parse_backlog_location(item.get("summary"))
    return summary_line


def line_matches(entry: dict[str, object], target_line: int | None) -> bool:
    if target_line is None:
        return True
    start = entry.get("line")
    end = entry.get("end_line")
    if not isinstance(start, int):
        return True
    if not isinstance(end, int):
        end = start
    return start <= target_line <= end


def select_item_probe_guidance(
    item: dict,
    entries: list[dict[str, object]],
) -> list[dict[str, object]]:
    candidate_paths = item_candidate_paths(item)
    if not candidate_paths:
        return []
    target_line = item_candidate_line(item)
    ordered = sorted(
        entries,
        key=lambda row: (
            {"high": 0, "medium": 1, "low": 2}.get(str(row.get("severity") or "medium"), 3),
            str(row.get("file_path") or ""),
            str(row.get("probe") or ""),
        ),
    )
    matched: list[dict[str, object]] = []
    seen: set[str] = set()
    for entry in ordered:
        file_path = str(entry.get("file_path") or "").strip()
        ai_instruction = str(entry.get("ai_instruction") or "").strip()
        if file_path not in candidate_paths or not ai_instruction:
            continue
        if not line_matches(entry, target_line) or ai_instruction in seen:
            continue
        seen.add(ai_instruction)
        matched.append(entry)
        if len(matched) >= 2:
            break
    return matched
