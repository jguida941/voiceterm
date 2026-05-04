"""Small progress-line helpers for governed VCS commands."""

from __future__ import annotations

import os
import sys
from typing import TextIO


def emit_vcs_progress(
    phase: str,
    detail: str = "",
    *,
    stream: TextIO | None = None,
) -> None:
    """Emit one flushed, grep-friendly progress line for long VCS phases."""
    if os.environ.get("DEVCTL_NO_PROGRESS") == "1":
        return
    target = stream or sys.stderr
    phase_text = str(phase or "").strip() or "unknown"
    detail_text = " ".join(str(detail or "").split())
    if detail_text:
        print(
            f"[devctl vcs] phase={phase_text} detail={detail_text}",
            file=target,
            flush=True,
        )
        return
    print(f"[devctl vcs] phase={phase_text}", file=target, flush=True)


__all__ = ["emit_vcs_progress"]
