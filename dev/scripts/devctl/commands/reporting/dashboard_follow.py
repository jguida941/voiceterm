"""Follow-mode helpers for reporting dashboard commands."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


def run_follow(
    args,
    *,
    snapshot_builder: Callable[[], dict[str, Any]],
    snapshot_renderer: Callable[[dict[str, Any]], str],
) -> int:
    """Poll and render dashboard snapshots until interrupted."""
    interval_seconds = parse_interval_seconds(getattr(args, "interval", "5"))
    max_snapshots = getattr(args, "max_follow_snapshots", None)
    output_path = getattr(args, "output", None)
    snapshot_count = 0
    try:
        while True:
            snapshot_count += 1
            snapshot = snapshot_builder()
            snapshot["follow"] = dict(
                enabled=True,
                snapshot_seq=snapshot_count,
                interval_seconds=interval_seconds,
            )
            _write_follow_output(
                snapshot_renderer(snapshot),
                output_path=output_path,
                append=snapshot_count > 1,
            )
            if max_snapshots is not None and snapshot_count >= int(max_snapshots):
                return 0
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        return 0


def parse_interval_seconds(raw: object) -> float:
    """Parse a compact polling interval like ``1``, ``500ms``, or ``2s``."""
    text = str(raw or "5").strip().lower()
    multiplier = 1.0
    if text.endswith("ms"):
        multiplier = 0.001
        text = text[:-2]
    elif text.endswith("s"):
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 60.0
        text = text[:-1]
    try:
        value = float(text)
    except ValueError:
        value = 5.0
    return max(0.1, value * multiplier)


def _write_follow_output(output: str, *, output_path: object, append: bool) -> None:
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with path.open(mode, encoding="utf-8") as stream:
            stream.write(output + "\n")
        return
    print(output)
    print("", flush=True)


__all__ = ["parse_interval_seconds", "run_follow"]
