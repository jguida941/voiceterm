"""Shared JSONL ledger readers for governance-ledger modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..jsonl_support import parse_json_line_dict
from .ledger_helpers import read_ledger_rows


def read_jsonl_ledger_rows(log_path: Path, *, max_rows: int) -> list[dict[str, Any]]:
    """Read JSONL ledger rows with the shared parser and bounded tail window."""
    return read_ledger_rows(log_path, max_rows=max_rows, parse_line_fn=parse_json_line_dict)
