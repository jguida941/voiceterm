"""Formatting helpers for devctl step reports.

Delegates to the typed CheckResult contract for enrichment and rendering.
Legacy callers that import format_steps_md / format_steps_text /
enrich_steps_for_json continue to work; the underlying logic now routes
through CheckResult and its shared renderer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from .runtime.check_result_models import build_check_result
from .runtime.check_result_render import (
    render_check_result_md,
    render_check_result_text,
)


def _build_result_from_steps(steps: List[dict]):
    """Internal: build a CheckResult from raw step dicts."""
    return build_check_result(
        steps=steps,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def format_steps_md(steps: List[dict]) -> str:
    """Return a Markdown table of step results."""
    return render_check_result_md(_build_result_from_steps(steps))


def format_steps_text(steps: List[dict]) -> str:
    """Return a compact terminal-friendly summary with check names and status."""
    return render_check_result_text(_build_result_from_steps(steps))


def enrich_steps_for_json(steps: List[dict]) -> List[dict]:
    """Add status and violation_summary fields to step dicts for JSON output."""
    result = _build_result_from_steps(steps)
    return list(result.steps)
