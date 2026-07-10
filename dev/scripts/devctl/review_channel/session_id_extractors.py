"""Shared positive-integer id extractors for session dictionaries/objects."""

from __future__ import annotations


def mapping_int_ids(
    rows: list[dict[str, object]],
    field_name: str,
) -> tuple[int, ...]:
    ids: list[int] = []
    for row in rows:
        raw = row.get(field_name) if isinstance(row, dict) else None
        try:
            value = int(raw or 0)
        except (TypeError, ValueError):
            continue
        if value > 0:
            ids.append(value)
    return tuple(dict.fromkeys(ids))


def object_int_ids(
    rows: tuple[object, ...],
    field_names: tuple[str, ...],
) -> tuple[int, ...]:
    ids: list[int] = []
    for row in rows:
        for field_name in field_names:
            raw = getattr(row, field_name, None)
            try:
                value = int(raw or 0)
            except (TypeError, ValueError):
                continue
            if value > 0:
                ids.append(value)
                break
    return tuple(dict.fromkeys(ids))
