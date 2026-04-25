"""Override parsing for ConnectivityRegistry missing-reader classifications."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

from ..config import REPO_ROOT

DEFAULT_READER_OVERRIDE_PATH = "dev/config/registry_reader_overrides.json"
MISSING_CONNECTION_CLASSIFICATIONS = frozenset(
    (
        "aspirational_gap",
        "mistakenly_declared",
        "deferred_consumer",
    )
)


class ReaderConnectionOverride(NamedTuple):
    """Explicit classification override for a missing reader connection."""

    contract_id: str
    reader_id: str
    classification: str
    justification: str
    override_ref: str


def load_reader_overrides(
    *,
    repo_root: Path = REPO_ROOT,
    override_path: str | Path | None = None,
) -> dict[tuple[str, str], ReaderConnectionOverride]:
    """Load committed missing-reader classifications from JSON, if present."""
    path = _resolve_override_path(repo_root=repo_root, override_path=override_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    overrides: dict[tuple[str, str], ReaderConnectionOverride] = {}
    for entry in _iter_override_entries(payload):
        override = _override_from_entry(entry, override_ref=path.as_posix())
        if override is None:
            continue
        overrides[(override.contract_id, override.reader_id)] = override
    return overrides


def override_is_usable(override: ReaderConnectionOverride) -> bool:
    if override.classification not in MISSING_CONNECTION_CLASSIFICATIONS:
        return False
    if override.classification == "aspirational_gap":
        return True
    return bool(override.justification.strip())


def _iter_override_entries(payload: object) -> tuple[dict[str, object], ...]:
    if isinstance(payload, list):
        return tuple(entry for entry in payload if isinstance(entry, dict))
    if not isinstance(payload, dict):
        return ()
    entries = payload.get("overrides")
    if isinstance(entries, list):
        return tuple(entry for entry in entries if isinstance(entry, dict))
    if isinstance(entries, dict):
        return _flatten_nested_overrides(entries)
    return ()


def _flatten_nested_overrides(
    entries: dict[object, object],
) -> tuple[dict[str, object], ...]:
    flattened: list[dict[str, object]] = []
    for contract_id, readers in entries.items():
        if isinstance(readers, dict):
            flattened.extend(
                _reader_override_entries(contract_id=contract_id, readers=readers)
            )
    return tuple(flattened)


def _reader_override_entries(
    *,
    contract_id: object,
    readers: dict[object, object],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for reader_id, entry in readers.items():
        if not isinstance(entry, dict):
            continue
        row = dict(entry)
        row["contract_id"] = str(contract_id)
        row["reader_id"] = str(reader_id)
        rows.append(row)
    return tuple(rows)


def _override_from_entry(
    entry: dict[str, object],
    *,
    override_ref: str,
) -> ReaderConnectionOverride | None:
    contract_id = str(entry.get("contract_id") or "").strip()
    reader_id = str(
        entry.get("reader_id") or entry.get("declared_reader_surface") or ""
    ).strip()
    classification = str(entry.get("classification") or "").strip()
    justification = str(entry.get("justification") or "").strip()
    if not contract_id or not reader_id or not classification:
        return None
    return ReaderConnectionOverride(
        contract_id=contract_id,
        reader_id=reader_id,
        classification=classification,
        justification=justification,
        override_ref=override_ref,
    )


def _resolve_override_path(
    *,
    repo_root: Path,
    override_path: str | Path | None,
) -> Path:
    path = Path(override_path or DEFAULT_READER_OVERRIDE_PATH)
    return path if path.is_absolute() else repo_root / path


__all__ = [
    "DEFAULT_READER_OVERRIDE_PATH",
    "MISSING_CONNECTION_CLASSIFICATIONS",
    "ReaderConnectionOverride",
    "load_reader_overrides",
    "override_is_usable",
]
