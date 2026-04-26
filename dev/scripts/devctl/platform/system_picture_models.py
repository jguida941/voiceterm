"""Typed system-picture snapshot contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SYSTEM_PICTURE_SCHEMA_VERSION = 1
SYSTEM_PICTURE_CONTRACT_ID = "SystemPicture"


@dataclass(frozen=True, slots=True)
class SystemPictureSection:
    """One bounded reducer section inside the system-picture artifact."""

    section_id: str
    title: str
    status: str
    summary: dict[str, object]
    source_path: str = ""
    source_command: str = ""
    generated_at_utc: str = ""
    section_hash: str = ""
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["notes"] = list(self.notes)
        return payload


@dataclass(frozen=True, slots=True)
class SystemPictureFreshnessContext:
    """HEAD identities that generated SystemPicture sections may accept."""

    current_head: str = ""
    accepted_head_shas: tuple[str, ...] = ()

    def matches(self, candidate: str) -> bool:
        """Return true when a surface was captured on HEAD or a managed ancestor."""
        clean_candidate = str(candidate or "").strip()
        if not clean_candidate:
            return False
        for accepted in self.fresh_heads:
            if _sha_prefix_matches(clean_candidate, accepted):
                return True
        return False

    @property
    def fresh_heads(self) -> tuple[str, ...]:
        """Return current HEAD plus deduped managed receipt-chain ancestors."""
        heads: list[str] = []
        for value in (self.current_head, *self.accepted_head_shas):
            clean = str(value or "").strip()
            if clean and clean not in heads:
                heads.append(clean)
        return tuple(heads)


@dataclass(frozen=True, slots=True)
class SystemPictureSnapshot:
    """Canonical machine-readable system-picture snapshot."""

    schema_version: int = SYSTEM_PICTURE_SCHEMA_VERSION
    contract_id: str = SYSTEM_PICTURE_CONTRACT_ID
    snapshot_id: str = ""
    generated_at_utc: str = ""
    repo_name: str = ""
    repo_root: str = ""
    current_branch: str = ""
    head_commit_sha: str = ""
    tree_hash: str = ""
    section_hashes: dict[str, str] = field(default_factory=dict)
    current_section_count: int = 0
    stale_section_count: int = 0
    missing_section_count: int = 0
    sections: tuple[SystemPictureSection, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sections"] = [section.to_dict() for section in self.sections]
        return payload


def _sha_prefix_matches(candidate: str, accepted: str) -> bool:
    left = str(candidate or "").strip()
    right = str(accepted or "").strip()
    return bool(
        left
        and right
        and (left.startswith(right) or right.startswith(left))
    )
