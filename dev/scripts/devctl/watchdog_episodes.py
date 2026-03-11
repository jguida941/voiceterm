"""Backward-compat shim for watchdog episode helpers."""

from .watchdog.episode import (
    build_guarded_coding_episode,
    emit_guarded_coding_episode,
    read_guarded_coding_episodes,
)

__all__ = [
    "build_guarded_coding_episode",
    "emit_guarded_coding_episode",
    "read_guarded_coding_episodes",
]
