"""Typed build context for review-state agent registry projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentRegistryContext:
    """Shared timestamp/provenance stamp for one registry emission."""

    timestamp: str
    plan_id: str = ""
    snapshot_id: str = ""
    zref: str = ""
    source_identity: Mapping[str, str] | None = None
    source_contract: str = ""
    source_command: str = ""
    observed_fields: tuple[str, ...] = ()
    inferred_fields: tuple[str, ...] = ()

    def source_identity_dict(self) -> dict[str, str]:
        return dict(self.source_identity or {})
