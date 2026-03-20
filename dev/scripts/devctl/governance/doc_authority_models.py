"""Shared models and policy constants for doc-authority."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

# Budget limits: (soft_limit, hard_limit) by doc class.
# None means no enforced limit for that class.
BUDGET_LIMITS: dict[str, tuple[int | None, int | None]] = dict(
    spec=(1200, 2000),
    guide=(800, 1500),
    runbook=(200, 400),
    reference=(150, 300),
    tracker=(None, None),
    generated_report=(None, None),
    archive=(None, None),
)

PLAN_DOC_CLASSES = frozenset({"tracker", "spec", "runbook"})
ROLE_TO_DOC_CLASS = {
    "tracker": "tracker",
    "spec": "spec",
    "runbook": "runbook",
    "reference": "reference",
}
REQUIRED_SECTIONS = [
    "## Scope",
    "## Execution Checklist",
    "## Progress Log",
    "## Audit Evidence",
]


@dataclass(frozen=True, slots=True)
class GovernedDocLayout:
    """Repo-pack-derived governed markdown layout."""

    repo_root: Path
    active_docs_root: str
    guides_root: str
    index_path: str
    tracker_path: str
    docs_authority_path: str
    bridge_path: str
    root_files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DocRecord:
    """One governed markdown document with authority metadata."""

    path: str
    doc_class: str
    owner: str
    authority: str
    lifecycle: str
    scope: str
    canonical_consumer: str
    line_count: int
    budget_status: str
    budget_limit: int
    has_metadata_header: bool
    has_required_sections: bool
    missing_sections: tuple[str, ...]
    registry_managed: bool
    in_index: bool
    issues: tuple[str, ...]
    consolidation_signals: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["missing_sections"] = list(self.missing_sections)
        payload["issues"] = list(self.issues)
        payload["consolidation_signals"] = list(self.consolidation_signals)
        return payload


@dataclass(frozen=True, slots=True)
class DocRegistryReport:
    """Aggregated doc-authority report for the repo."""

    command: str
    timestamp_utc: str
    repo_root: str
    total_governed_docs: int
    total_lines: int
    by_class: dict[str, int]
    by_lifecycle: dict[str, int]
    registry_coverage: float
    registry_counts: dict[str, int]
    budget_violations: list[dict[str, object]]
    authority_overlaps: list[dict[str, object]]
    consolidation_candidates: list[dict[str, object]]
    records: list[DocRecord]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["records"] = [record.to_dict() for record in self.records]
        return payload
