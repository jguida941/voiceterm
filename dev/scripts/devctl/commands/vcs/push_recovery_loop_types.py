"""Typed helpers shared by governed push recovery-loop phases."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class RecoveryContext:
    state: object
    policy: object
    repo_root: Path
    runner: object
    max_steps: int
    time_budget_seconds: int
    deadline: float


@dataclass(slots=True)
class RecoveryProgress:
    steps: list[dict[str, object]] = field(default_factory=list)
    latest_payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RecoveryResultStatus:
    status: str
    ok: bool
    reason: str
    retryable: bool


__all__ = [
    "RecoveryContext",
    "RecoveryProgress",
    "RecoveryResultStatus",
]
