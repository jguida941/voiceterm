"""Small progress-line helpers for governed VCS commands."""

from __future__ import annotations

import os
import sys
from typing import TextIO

from ...runtime.stage_progress import (
    build_stage_progress_event,
    record_stage_progress_event,
)


def emit_vcs_progress(
    phase: str,
    detail: str = "",
    *,
    stream: TextIO | None = None,
) -> None:
    """Emit one flushed, grep-friendly progress line for long VCS phases."""
    phase_text = str(phase or "").strip() or "unknown"
    detail_text = " ".join(str(detail or "").split())
    _record_vcs_progress_event(phase_text, detail_text)
    if os.environ.get("DEVCTL_NO_PROGRESS") == "1":
        return
    target = stream or sys.stderr
    if detail_text:
        print(
            f"[devctl vcs] phase={phase_text} detail={detail_text}",
            file=target,
            flush=True,
        )
        return
    print(f"[devctl vcs] phase={phase_text}", file=target, flush=True)


def _record_vcs_progress_event(phase: str, detail: str) -> None:
    try:
        record_stage_progress_event(
            build_stage_progress_event(
                command_name="devctl.vcs",
                phase=phase,
                status="running",
                detail=detail,
            )
        )
    except (OSError, ValueError, TypeError):
        return


__all__ = ["emit_vcs_progress"]
