"""Typed records, defaults, and constants for the ingestion-churn guard."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT


COMMAND = "check_no_ingestion_churn_without_advancement"
CONTRACT_ID = "NoIngestionChurnWithoutAdvancementGuard"
DEFAULT_SNAPSHOTS_PATH = REPO_ROOT / "dev/state/plan_source_snapshots.jsonl"
DEFAULT_PLAN_INDEX_PATH = REPO_ROOT / "dev/state/plan_index.jsonl"
DEFAULT_CLOSURE_RECEIPTS_PATH = REPO_ROOT / "dev/state/plan_row_closure_receipts.jsonl"
DEFAULT_LIFECYCLE_RECEIPTS_PATH = REPO_ROOT / "dev/state/slice_lifecycle_receipts.jsonl"
DEFAULT_FEATURE_PROOF_DIR = REPO_ROOT / "dev/reports/feature_proof_receipts"
DEFAULT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
DEFAULT_WINDOW_HOURS = 24
DEFAULT_MAX_SNAPSHOTS = 2

INGESTION_CHURN_REASON = "ingestion_churn_without_advancement"
DISPLAY_TEXT = (
    "AI DUMBASS ALERT: repeated plan ingestion without advancement. "
    "Stop re-snapshotting and either close, block, or produce proof."
)


@dataclass(frozen=True, slots=True)
class IngestionChurnViolation:
    source_ref: str
    row_id: str
    reason: str
    snapshot_count: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SnapshotGroup:
    source_ref: str
    row_id: str
    snapshots: tuple[Mapping[str, object], ...]


def repo_relative(path: Path) -> Path:
    try:
        return path.resolve().relative_to(REPO_ROOT)
    except (OSError, ValueError):
        return path
