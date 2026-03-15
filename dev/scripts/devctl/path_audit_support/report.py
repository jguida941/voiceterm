"""Typed report models for path-audit helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PathAuditAggregateReport:
    """Typed aggregate report for stale path and workspace-contract scans."""

    ok: bool
    error: str | None
    checked_file_count: int
    unique_checked_file_count: int
    legacy_checked_file_count: int
    workspace_checked_file_count: int
    excluded_prefixes: list[str]
    excluded_files: list[str]
    legacy_rules: dict[str, str]
    workspace_rules: list[dict]
    legacy_violation_count: int
    workspace_contract_violation_count: int
    violations: list[dict]

    def to_dict(self) -> dict:
        """Render the dataclass in the legacy dict shape expected by callers."""
        return asdict(self)
