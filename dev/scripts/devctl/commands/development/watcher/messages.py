"""Human-facing watcher commands and summaries."""

from __future__ import annotations


def watch_command(actor: str) -> str:
    return (
        "python3 dev/scripts/devctl.py review-channel --action watch "
        f"--target {actor} --status pending --follow --terminal none --format json "
        "--follow-inactivity-timeout-seconds 0"
    )


def watcher_summary(
    *,
    watched_actor: str,
    status: str,
    stale_seconds: int,
    runtime_observed: bool,
) -> str:
    if status == "live":
        if runtime_observed:
            return f"{watched_actor} pending-packet watcher is live via runtime rows."
        return f"{watched_actor} pending-packet watcher is live."
    return (
        f"{watched_actor} pending-packet watcher is {status}; "
        f"stale_seconds={stale_seconds}."
    )


__all__ = ["watch_command", "watcher_summary"]
