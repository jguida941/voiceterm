"""Shared JSONL iterator for the ingestion-churn guard."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path


def iter_jsonl(path: Path) -> Iterable[Mapping[str, object]]:
    if not path.exists():
        return ()

    def _rows() -> Iterable[Mapping[str, object]]:
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, Mapping):
                yield payload

    return _rows()
