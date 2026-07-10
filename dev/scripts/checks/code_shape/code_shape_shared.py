"""Shared shape-policy dataclasses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShapePolicy:
    soft_limit: int
    hard_limit: int
    oversize_growth_limit: int
    hard_lock_growth_limit: int


@dataclass(frozen=True)
class FunctionShapePolicy:
    max_lines: int


@dataclass(frozen=True)
class FunctionShapeException:
    max_lines: int
    owner: str
    expires_on: str
    follow_up_mp: str
    reason: str
