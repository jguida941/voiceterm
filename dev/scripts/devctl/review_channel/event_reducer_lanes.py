"""Small file-loading helpers for event-backed reducer inputs."""

from __future__ import annotations

import json
from pathlib import Path

from .core import load_text, parse_lane_assignments


def load_lane_assignments(review_channel_path: Path) -> list:
    """Load lane assignments from the active review-channel markdown."""
    if not review_channel_path.exists():
        return []
    return parse_lane_assignments(load_text(review_channel_path))


def load_prior_projection_review_state(
    projections_root: Path,
) -> dict[str, object] | None:
    """Read the latest projected review-state payload when it exists."""
    review_state_path = projections_root / "review_state.json"
    try:
        payload = json.loads(review_state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None
