"""Typed report models for review-surface convergence checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ConvergencePassViolation:
    """One typed convergence mismatch or degraded-surface violation."""

    category: str
    detail: str
    surface: str = ""
    field: str = ""
    expected: str = ""
    actual: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConvergencePassResult:
    """Typed result emitted by ``check_review_surface_consistency``."""

    schema_version: int = 1
    contract_id: str = "ConvergencePassResult"
    command: str = "check_review_surface_consistency"
    ok: bool = True
    snapshot_ids: dict[str, str] = field(default_factory=dict)
    zrefs: dict[str, str] = field(default_factory=dict)
    generation_ids: dict[str, str] = field(default_factory=dict)
    provenance: dict[str, dict[str, object]] = field(default_factory=dict)
    bridge_poll: dict[str, object] = field(default_factory=dict)
    turn_authority: dict[str, object] = field(default_factory=dict)
    disk_parity_warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    violations: tuple[ConvergencePassViolation, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["disk_parity_warnings"] = list(self.disk_parity_warnings)
        payload["errors"] = list(self.errors)
        payload["violations"] = [violation.to_dict() for violation in self.violations]
        return payload
