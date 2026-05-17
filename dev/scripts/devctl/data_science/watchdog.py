"""Backward-compat shim for shared watchdog metric helpers."""

from ..watchdog.episode import read_guarded_coding_episodes as read_watchdog_rows
from ..watchdog.metrics import build_watchdog_metrics, load_watchdog_summary_artifact

__all__ = [
    "build_watchdog_metrics",
    "load_watchdog_summary_artifact",
    "read_watchdog_rows",
]
