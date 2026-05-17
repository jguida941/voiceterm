"""Shared refusal payload helpers for pipeline actions."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def refused_pipeline_result(
    *,
    action: str,
    reason_refused: str,
    pipeline_artifact_path: Path,
    pipeline_id: str = "",
    recommended_next_action: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a consistent refusal payload for pipeline actions."""
    result: dict[str, Any] = {
        "ok": False,
        "action": action,
        "reason_refused": reason_refused,
        "errors": [reason_refused],
        "pipeline_artifact_path": str(pipeline_artifact_path),
    }
    if pipeline_id:
        result["pipeline_id"] = pipeline_id
    if recommended_next_action:
        result["recommended_next_action"] = recommended_next_action
    if extra:
        result.update(extra)
    return result


__all__ = ["refused_pipeline_result"]
