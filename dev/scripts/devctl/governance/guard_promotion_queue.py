"""Guard/probe promotion candidate queue derived from governance-review rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .ledger_helpers import (
    append_ledger_rows,
    optional_text,
    resolve_ledger_path,
)
from ..repo_packs import active_path_config
from ..repo_packs.voiceterm import voiceterm_repo_root
from ..time_utils import utc_timestamp

GUARD_PROMOTION_CANDIDATE_CONTRACT_ID = "GuardPromotionCandidate"
GUARD_PROMOTION_CANDIDATE_SCHEMA_VERSION = 1
PROMOTION_PREVENTION_SURFACES = frozenset({"guard", "probe"})
OPTIONAL_CANDIDATE_ROW_FIELDS = (
    "line",
    "severity",
    "risk_type",
    "source_command",
    "notes",
    "source_review_timestamp_utc",
)


@dataclass(frozen=True, slots=True)
class PromotionSource:
    surface: str
    finding_id: str
    check_id: str


@dataclass(frozen=True, slots=True)
class GuardPromotionCandidate:
    """Typed queue row for later guard/probe promotion work."""

    schema_version: int = field(
        default=GUARD_PROMOTION_CANDIDATE_SCHEMA_VERSION,
        init=False,
    )
    contract_id: str = field(
        default=GUARD_PROMOTION_CANDIDATE_CONTRACT_ID,
        init=False,
    )
    candidate_id: str
    created_at_utc: str
    status: str
    candidate_kind: str
    recommended_action: str
    source_finding_id: str
    source_check_id: str
    source_signal_type: str = ""
    source_verdict: str = ""
    finding_class: str = ""
    recurrence_risk: str = ""
    repo_name: str = ""
    repo_path: str = ""
    file_path: str = ""
    line: object | None = None
    severity: str = ""
    risk_type: str = ""
    source_command: str = ""
    notes: str = ""
    source_review_timestamp_utc: str = ""

    def to_row(self) -> dict[str, Any]:
        row = asdict(self)
        for field_name in OPTIONAL_CANDIDATE_ROW_FIELDS:
            if not row.get(field_name):
                row.pop(field_name, None)
        return row


def resolve_guard_promotion_queue_path(
    raw_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the guard/probe promotion queue path through repo-pack defaults."""
    return resolve_ledger_path(
        raw_path,
        default_rel=Path(active_path_config().guard_promotion_queue_rel),
        repo_root_fn=voiceterm_repo_root,
        repo_root=repo_root,
    )


def build_guard_promotion_candidate(
    review_row: dict[str, Any],
) -> dict[str, Any] | None:
    """Build a promotion candidate for guard/probe prevention rows."""
    source = _promotion_source(review_row)
    if source is None:
        return None

    return _candidate_from_review(source, review_row).to_row()


def append_guard_promotion_candidate_from_review(
    review_row: dict[str, Any],
    *,
    queue_path: Path,
) -> dict[str, Any] | None:
    """Append a guard/probe promotion candidate when the review row requests one."""
    candidate = build_guard_promotion_candidate(review_row)
    if candidate is None:
        return None
    append_ledger_rows([candidate], log_path=queue_path)
    return candidate


def _promotion_source(review_row: dict[str, Any]) -> PromotionSource | None:
    prevention_surface = optional_text(review_row.get("prevention_surface"))
    if prevention_surface not in PROMOTION_PREVENTION_SURFACES:
        return None

    finding_id = optional_text(review_row.get("finding_id"))
    check_id = optional_text(review_row.get("check_id"))
    if not finding_id or not check_id:
        return None

    return PromotionSource(
        surface=prevention_surface,
        finding_id=finding_id,
        check_id=check_id,
    )


def _candidate_from_review(
    source: PromotionSource,
    review_row: dict[str, Any],
) -> GuardPromotionCandidate:
    return GuardPromotionCandidate(
        candidate_id=f"{source.surface}:{source.finding_id}",
        created_at_utc=utc_timestamp(),
        status="queued",
        candidate_kind=source.surface,
        recommended_action=_recommended_action(source.surface),
        source_finding_id=source.finding_id,
        source_check_id=source.check_id,
        **_review_text_fields(review_row),
        **_review_optional_fields(review_row),
    )


def _recommended_action(prevention_surface: str) -> str:
    return "draft_guard" if prevention_surface == "guard" else "draft_probe"


def _review_text_fields(review_row: dict[str, Any]) -> dict[str, str]:
    return {
        target_key: optional_text(review_row.get(source_key)) or ""
        for source_key, target_key in (
            ("signal_type", "source_signal_type"),
            ("verdict", "source_verdict"),
            ("finding_class", "finding_class"),
            ("recurrence_risk", "recurrence_risk"),
            ("repo_name", "repo_name"),
            ("repo_path", "repo_path"),
            ("file_path", "file_path"),
        )
    }


def _review_optional_fields(review_row: dict[str, Any]) -> dict[str, object]:
    return {
        target_key: value
        for source_key, target_key in (
            ("line", "line"),
            ("severity", "severity"),
            ("risk_type", "risk_type"),
            ("source_command", "source_command"),
            ("notes", "notes"),
            ("timestamp_utc", "source_review_timestamp_utc"),
        )
        if (value := _optional_value(review_row, source_key))
    }


def _optional_value(source: dict[str, Any], source_key: str) -> object | None:
    value = source.get(source_key)
    if value is None or value == "":
        return None
    return value
