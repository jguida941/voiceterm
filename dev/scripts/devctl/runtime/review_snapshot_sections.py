"""Compatibility facade for ReviewSnapshot section builders.

The concrete builders now live in narrower sibling modules so this module
stays under the code-shape soft limit while preserving the existing import
surface.
"""

from __future__ import annotations

from .review_snapshot_delta import build_delta
from .review_snapshot_sections_architecture import build_architecture
from .review_snapshot_sections_quality import build_quality
from .review_snapshot_sections_review import (
    build_known_gaps,
    build_reasoning,
    build_reviewer_hints,
)

__all__ = [
    "build_architecture",
    "build_delta",
    "build_known_gaps",
    "build_quality",
    "build_reasoning",
    "build_reviewer_hints",
]
