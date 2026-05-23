"""Shared test helpers for JSONL-backed guard fixtures.

Extracted from per-test ``_write_jsonl`` duplicates that previously lived in
each ``test_check_*.py`` file. Tests should import :func:`write_jsonl`
instead of redefining the same body locally.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    """Write ``rows`` to ``path`` as canonical sorted-key JSONL."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
