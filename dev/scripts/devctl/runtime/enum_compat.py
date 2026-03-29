"""Compatibility helpers for stdlib enum features across supported Pythons."""

from __future__ import annotations

from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python < 3.11 fallback
    class StrEnum(str, Enum):
        """Backport-compatible subset of `enum.StrEnum` for Python 3.10."""

        def __str__(self) -> str:
            return self.value

