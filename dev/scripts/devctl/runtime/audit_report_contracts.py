"""Typed report contracts for security and audit command output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SECURITY_REPORT_CONTRACT_ID = "SecurityReport"
SECURITY_REPORT_SCHEMA_VERSION = 1
RUST_AUDIT_REPORT_CONTRACT_ID = "RustAuditReport"
RUST_AUDIT_REPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class SecurityReport:
    """Top-level `devctl security` report payload."""

    timestamp: str
    ok: bool
    rustsec_output: str
    scanner_tier: str
    python_scope: str
    since_ref: str | None
    head_ref: str
    expensive_policy: str
    core_scanners: tuple[str, ...]
    expensive_scanners: tuple[str, ...]
    warnings: tuple[str, ...]
    steps: tuple[dict[str, Any], ...]
    schema_version: int = SECURITY_REPORT_SCHEMA_VERSION
    contract_id: str = SECURITY_REPORT_CONTRACT_ID
    command: str = "security"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "command": self.command,
            "timestamp": self.timestamp,
            "ok": self.ok,
            "rustsec_output": self.rustsec_output,
            "scanner_tier": self.scanner_tier,
            "python_scope": self.python_scope,
            "since_ref": self.since_ref,
            "head_ref": self.head_ref,
            "expensive_policy": self.expensive_policy,
            "core_scanners": list(self.core_scanners),
            "expensive_scanners": list(self.expensive_scanners),
            "warnings": list(self.warnings),
            "steps": list(self.steps),
        }


@dataclass(frozen=True)
class RustAuditReport:
    """Top-level Rust audit aggregation payload."""

    mode: str
    since_ref: str | None
    head_ref: str
    ok: bool
    collection_ok: bool
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    summary: dict[str, Any]
    guards: tuple[dict[str, Any], ...]
    guard_reports: dict[str, dict[str, Any]]
    categories: tuple[dict[str, Any], ...]
    hotspots: tuple[dict[str, Any], ...]
    charts: tuple[str, ...]
    schema_version: int = RUST_AUDIT_REPORT_SCHEMA_VERSION
    contract_id: str = RUST_AUDIT_REPORT_CONTRACT_ID
    command: str = "rust-audit"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "command": self.command,
            "mode": self.mode,
            "since_ref": self.since_ref,
            "head_ref": self.head_ref,
            "ok": self.ok,
            "collection_ok": self.collection_ok,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "summary": dict(self.summary),
            "guards": list(self.guards),
            "guard_reports": dict(self.guard_reports),
            "categories": list(self.categories),
            "hotspots": list(self.hotspots),
            "charts": list(self.charts),
        }


__all__ = [
    "RUST_AUDIT_REPORT_CONTRACT_ID",
    "RUST_AUDIT_REPORT_SCHEMA_VERSION",
    "SECURITY_REPORT_CONTRACT_ID",
    "SECURITY_REPORT_SCHEMA_VERSION",
    "RustAuditReport",
    "SecurityReport",
]
