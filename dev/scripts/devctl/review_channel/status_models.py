"""Dataclasses for bridge-backed review-channel status refreshes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import LaneAssignment
    from .projection_bundle import ReviewChannelProjectionPaths


@dataclass(frozen=True)
class ReviewChannelStatusSnapshot:
    """Shared status-refresh result for read-only review consumers."""

    lanes: list[LaneAssignment]
    bridge_liveness: dict[str, object]
    attention: dict[str, object]
    warnings: list[str]
    errors: list[str]
    projection_paths: ReviewChannelProjectionPaths
    reviewer_worker: dict[str, object] | None = None
    service_identity: dict[str, object] | None = None
    attach_auth_policy: dict[str, object] | None = None
