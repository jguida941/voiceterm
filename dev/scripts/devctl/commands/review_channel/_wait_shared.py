"""Shared wait-loop helpers for both implementer and reviewer wait primitives."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class WaitOutcome:
    """Final outcome of a bounded wait loop."""

    stop_reason: str
    polls_observed: int
    wait_timeout_seconds: int
    wait_interval_seconds: int
    exit_code: int


@dataclass(frozen=True, slots=True)
class WaitDeps:
    """Injectable side effects for bounded wait loops."""

    run_status_action_fn: Callable[..., tuple[dict[str, object], int]]
    read_bridge_text_fn: Callable[..., str]
    monotonic_fn: Callable[[], float]
    sleep_fn: Callable[[float], None]


def resolve_wait_timeout(args, *, default_seconds: int) -> int:
    """Resolve wait timeout from CLI args or default."""
    timeout_minutes = int(getattr(args, "timeout_minutes", 0) or 0)
    if timeout_minutes > 0:
        return timeout_minutes * 60
    return default_seconds


def resolve_wait_interval(args, *, default_seconds: int = 150) -> int:
    """Resolve poll interval from CLI args or default."""
    return max(1, int(getattr(args, "follow_interval_seconds", default_seconds)))
