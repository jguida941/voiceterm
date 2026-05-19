"""Typed release metadata for continuation-anchor packets."""

from __future__ import annotations

from dataclasses import dataclass

from ..runtime.session_termination_anchor_release import (
    SLICE_COUNTED_RELEASE_MODES as VALID_ANCHOR_RELEASE_MODES,
)
from ..runtime.value_coercion import coerce_optional_int
from .packet_text_fields import clean_optional_text as _clean_optional_text


@dataclass(frozen=True, slots=True)
class PacketAnchorReleaseFields:
    """Typed release metadata for continuation anchors."""

    release_mode: str = ""
    release_commit_count: int | None = None

    @classmethod
    def from_values(
        cls,
        *,
        release_mode: object = None,
        release_commit_count: object = None,
    ) -> "PacketAnchorReleaseFields":
        return cls(
            release_mode=_clean_optional_text(release_mode) or "",
            release_commit_count=coerce_optional_int(release_commit_count),
        )

    def to_event_fields(self) -> dict[str, object]:
        return {
            "release_mode": self.release_mode or None,
            "release_commit_count": self.release_commit_count,
        }

    def has_values(self) -> bool:
        return bool(self.release_mode or self.release_commit_count is not None)


def validate_anchor_release_fields(request: object) -> None:
    release = getattr(request, "anchor_release", PacketAnchorReleaseFields())
    if not release.has_values():
        return
    if getattr(request, "kind", "") != "continuation_anchor":
        raise ValueError(
            "Anchor release fields are only valid on continuation_anchor packets."
        )
    if release.release_mode not in VALID_ANCHOR_RELEASE_MODES:
        raise ValueError(
            "Unsupported continuation_anchor release mode: "
            f"{release.release_mode}"
        )
    if release.release_commit_count is None or release.release_commit_count <= 0:
        raise ValueError(
            "--release-commit-count must be greater than zero when --release-mode "
            "is set."
        )

