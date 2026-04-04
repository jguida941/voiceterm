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
