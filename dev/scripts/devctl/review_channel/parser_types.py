"""Shared parser argument definitions for review-channel CLI wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ArgumentDef:
    flags: tuple[str, ...]
    kwargs: dict[str, Any]


__all__ = ["ArgumentDef"]
