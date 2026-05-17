"""Report models for the governed transition verifier."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GovernedTransitionPathCheck:
    """One graph-walk verification for a governed transition."""

    transition_id: str
    check_kind: str
    from_ref: str
    to_ref: str
    ok: bool
    confidence: str
    path_length: int
    edge_kinds: tuple[str, ...]
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "transition_id": self.transition_id,
            "check_kind": self.check_kind,
            "from_ref": self.from_ref,
            "to_ref": self.to_ref,
            "ok": self.ok,
            "confidence": self.confidence,
            "path_length": self.path_length,
            "edge_kinds": list(self.edge_kinds),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class GovernedTransitionReport:
    """CI report for governed transition metadata and graph reachability."""

    ok: bool
    transition_count: int
    checked_path_count: int
    manifest_modules: tuple[str, ...]
    path_checks: tuple[GovernedTransitionPathCheck, ...]

    @property
    def failure_count(self) -> int:
        return sum(1 for check in self.path_checks if not check.ok)

    @property
    def edge_kind_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for check in self.path_checks:
            for edge_kind in check.edge_kinds:
                counts[edge_kind] = counts.get(edge_kind, 0) + 1
        return dict(sorted(counts.items()))

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "transition_count": self.transition_count,
            "checked_path_count": self.checked_path_count,
            "failure_count": self.failure_count,
            "manifest_modules": list(self.manifest_modules),
            "edge_kind_counts": self.edge_kind_counts,
            "path_checks": [check.to_dict() for check in self.path_checks],
        }
