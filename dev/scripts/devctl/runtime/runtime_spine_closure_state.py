"""Typed read model for runtime-spine closure continuity."""

from __future__ import annotations

from dataclasses import asdict, dataclass


RUNTIME_SPINE_CLOSURE_CONTRACT_ID = "RuntimeSpineClosureState"
RUNTIME_SPINE_CLOSURE_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class RuntimeSpineItem:
    """One object in the documented runtime spine."""

    name: str
    marker: str
    status: str
    detail: str
    owner_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["owner_refs"] = list(self.owner_refs)
        return payload


@dataclass(frozen=True, slots=True)
class RuntimeSpineClosureRow:
    """One closure-matrix row for a risky runtime-spine object."""

    runtime_object: str
    active_owner: str
    typed_contract: str
    producer: str
    consumer: str
    regression_proof: str
    graph_context_visibility: str
    carry_forward_compaction_path: str
    priority: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RuntimeSpineClosureState:
    """Machine-readable closure state for agents, guards, and handoff packs."""

    risky_items: tuple[RuntimeSpineItem, ...]
    closure_matrix: tuple[RuntimeSpineClosureRow, ...]
    violations: tuple[dict[str, str], ...]
    closure_rule_present: bool
    registered_guard_present: bool
    section_present: bool
    schema_version: int = RUNTIME_SPINE_CLOSURE_SCHEMA_VERSION
    contract_id: str = RUNTIME_SPINE_CLOSURE_CONTRACT_ID

    @property
    def ok(self) -> bool:
        """Return whether the closure state is structurally connected."""
        return not self.violations

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_id": self.contract_id,
            "schema_version": self.schema_version,
            "ok": self.ok,
            "section_present": self.section_present,
            "closure_rule_present": self.closure_rule_present,
            "registered_guard_present": self.registered_guard_present,
            "risky_item_count": len(self.risky_items),
            "closure_matrix_present": bool(self.closure_matrix),
            "closure_matrix_row_count": len(self.closure_matrix),
            "violations": list(self.violations),
            "items": [item.to_dict() for item in self.risky_items],
            "closure_matrix": [row.to_dict() for row in self.closure_matrix],
        }


__all__ = [
    "RUNTIME_SPINE_CLOSURE_CONTRACT_ID",
    "RUNTIME_SPINE_CLOSURE_SCHEMA_VERSION",
    "RuntimeSpineClosureRow",
    "RuntimeSpineClosureState",
    "RuntimeSpineItem",
]

