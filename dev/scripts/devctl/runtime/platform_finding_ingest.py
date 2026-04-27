"""Canonical finding-ingest seam for platform dogfood signals."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from ..config import get_repo_root
from ..governance.guard_promotion_queue import (
    append_guard_promotion_candidate_from_review,
    resolve_guard_promotion_queue_path,
)
from ..governance.ledger_helpers import optional_text
from ..governance_review.log import (
    build_governance_review_report,
    resolve_governance_review_log_path,
    resolve_governance_review_summary_root,
)
from ..governance_review.models import GovernanceReviewInput
from ..governance_review.render import write_governance_review_summary
from .dogfood_governance import build_dogfood_governance_input
from .dogfood_log import build_dogfood_record
from .dogfood_models import DogfoodRecord, DogfoodRecordInput
from .dogfood_render import persist_dogfood_run
from .finding_backlog import FindingBacklogWriteResult, record_finding_backlog_row

PLATFORM_FINDING_INGEST_CONTRACT_ID = "PlatformFindingIngest"
PLATFORM_FINDING_INGEST_SCHEMA_VERSION = 1
AUTO_INGEST_ENV = "DEVCTL_PLATFORM_FINDING_INGEST_AUTO_RECORD"
AUTO_INGEST_DISABLE_ENV = "DEVCTL_PLATFORM_FINDING_INGEST_DISABLE"
AUTO_INGEST_FALSE_VALUES = frozenset({"0", "false", "no", "off"})
AUTO_INGEST_SKIPPED_COMMANDS = frozenset(
    {
        "data-science",
        "dogfood",
        "findings-priority",
        "governance-review",
        "review-snapshot",
    }
)


@dataclass(frozen=True, slots=True)
class PlatformFindingIngestResult:
    """Typed result for one platform finding-ingest attempt."""

    status: str
    reason: str
    contract_id: str = PLATFORM_FINDING_INGEST_CONTRACT_ID
    schema_version: int = PLATFORM_FINDING_INGEST_SCHEMA_VERSION
    log_path: str = ""
    row: dict[str, Any] | None = None
    finding: dict[str, Any] | None = None
    dogfood_log_path: str = ""
    dogfood_record: dict[str, Any] | None = None
    dogfood_summary_paths: dict[str, str] | None = None
    summary_paths: dict[str, str] | None = None
    promotion_candidate: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["dogfood_record"] = self.dogfood_record or {}
        payload["dogfood_summary_paths"] = self.dogfood_summary_paths or {}
        payload["summary_paths"] = self.summary_paths or {}
        return payload


@dataclass(frozen=True, slots=True)
class DogfoodFindingIngestOptions:
    """Optional FindingReview metadata for dogfood finding ingest."""

    finding_id: str | None = None
    check_id: str | None = None
    file_path: str | None = None
    line: int | None = None
    severity: str | None = None
    risk_type: str | None = None
    source_command: str | None = None
    notes: str | None = None
    finding_type: str | None = None
    finding_class: str | None = None
    recurrence_risk: str | None = None
    prevention_surface: str | None = None
    waiver_reason: str | None = None
    verdict: str | None = None


class PlatformFindingIngest:
    """Write platform findings through the canonical backlog seam."""

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        governance: object | None = None,
        governance_log_path: Path | None = None,
        governance_summary_root: Path | None = None,
        promotion_queue_path: Path | None = None,
    ) -> None:
        self.repo_root = repo_root or get_repo_root() or Path(".")
        self.governance = governance
        self.governance_log_path = governance_log_path
        self.governance_summary_root = governance_summary_root
        self.promotion_queue_path = promotion_queue_path

    def record_review_input(
        self,
        review_input: GovernanceReviewInput,
        *,
        refresh_summary: bool = True,
        promote_guard_candidate: bool = True,
    ) -> PlatformFindingIngestResult:
        """Record one FindingReview row and re-project it through FindingBacklog."""
        log_path = self.governance_log_path or resolve_governance_review_log_path(
            repo_root=self.repo_root,
        )
        write_result = record_finding_backlog_row(
            review_input=review_input,
            repo_root=self.repo_root,
            governance=self.governance,
            log_path=log_path,
        )
        promotion_candidate = None
        if promote_guard_candidate:
            queue_path = self.promotion_queue_path or resolve_guard_promotion_queue_path(None)
            promotion_candidate = append_guard_promotion_candidate_from_review(
                write_result.row,
                queue_path=queue_path,
            )
        summary_paths: dict[str, str] = {}
        if refresh_summary:
            summary_paths = _refresh_governance_summary(
                log_path=log_path,
                summary_root=(
                    self.governance_summary_root
                    or resolve_governance_review_summary_root(repo_root=self.repo_root)
                ),
            )
        return _result_from_write(
            write_result,
            status="recorded",
            reason="finding_recorded",
            summary_paths=summary_paths,
            promotion_candidate=promotion_candidate,
        )

    def record_dogfood_result(
        self,
        record: DogfoodRecord,
        *,
        options: DogfoodFindingIngestOptions | None = None,
        refresh_summary: bool = True,
        persist_run: bool = False,
        refresh_dogfood_summary: bool = False,
    ) -> PlatformFindingIngestResult:
        """Record one dogfood run outcome as a canonical FindingBacklog row."""
        resolved = options or DogfoodFindingIngestOptions()
        result = self.record_review_input(
            build_dogfood_governance_input(
                record,
                finding_id=resolved.finding_id,
                check_id=resolved.check_id,
                file_path=resolved.file_path,
                line=resolved.line,
                severity=resolved.severity,
                risk_type=resolved.risk_type,
                source_command=resolved.source_command,
                notes=resolved.notes,
                finding_type=resolved.finding_type,
                finding_class=resolved.finding_class,
                recurrence_risk=resolved.recurrence_risk,
                prevention_surface=resolved.prevention_surface,
                waiver_reason=resolved.waiver_reason,
                verdict=resolved.verdict,
                repo_root=self.repo_root,
            ),
            refresh_summary=refresh_summary,
        )
        if not persist_run:
            return result
        return self._persist_dogfood_run(
            record,
            result=result,
            refresh_dogfood_summary=refresh_dogfood_summary,
        )

    def _persist_dogfood_run(
        self,
        record: DogfoodRecord,
        *,
        result: PlatformFindingIngestResult,
        refresh_dogfood_summary: bool,
    ) -> PlatformFindingIngestResult:
        """Append the dogfood ledger row after the canonical finding is known."""
        persisted = persist_dogfood_run(
            record,
            governance_row=result.row,
            repo_root=self.repo_root,
            refresh_summary=refresh_dogfood_summary,
        )
        return replace(
            result,
            dogfood_log_path=persisted.log_path,
            dogfood_record=persisted.record,
            dogfood_summary_paths=persisted.summary_paths,
        )


def maybe_auto_ingest_devctl_result(
    *,
    command: str,
    returncode: int,
    argv: list[str],
    read_only: bool,
    repo_root: Path | None = None,
) -> PlatformFindingIngestResult:
    """Optionally ingest a failed devctl command as dogfood evidence.

    This is fail-open and default-on in report-only mode while Slice A gathers
    confidence. Operators can still suppress recording with
    ``DEVCTL_PLATFORM_FINDING_INGEST_DISABLE=1`` or a false-valued
    ``DEVCTL_PLATFORM_FINDING_INGEST_AUTO_RECORD`` compatibility override.
    """
    normalized_command = optional_text(command)
    if os.environ.get(AUTO_INGEST_DISABLE_ENV, "").strip():
        return PlatformFindingIngestResult("skipped", "disabled_by_env")
    if _auto_ingest_disabled_by_setting():
        return PlatformFindingIngestResult("skipped", "auto_record_disabled_by_env")
    if read_only:
        return PlatformFindingIngestResult("skipped", "read_only_command")
    if normalized_command in AUTO_INGEST_SKIPPED_COMMANDS:
        return PlatformFindingIngestResult("skipped", "excluded_command")
    if int(returncode) == 0:
        return PlatformFindingIngestResult("skipped", "command_succeeded")
    effective_root = repo_root or get_repo_root() or Path(".")
    status = "blocked" if int(returncode) in {2, 126, 127} else "failed"
    record = build_dogfood_record(
        record_input=DogfoodRecordInput(
            target_kind="command",
            target_id=normalized_command,
            status=status,
            actor=os.environ.get("DEVCTL_EXECUTION_ACTOR") or "script",
            provider=os.environ.get("DEVCTL_EXECUTION_SOURCE") or "script_only",
            run_label=os.environ.get("DEVCTL_AUDIT_CYCLE_ID") or "local",
            source_command=_source_command(argv),
            notes=f"Auto-ingested devctl finalization failure rc={int(returncode)}.",
        ),
        repo_root=effective_root,
    )
    try:
        return PlatformFindingIngest(repo_root=effective_root).record_dogfood_result(
            record,
            options=DogfoodFindingIngestOptions(source_command=record.source_command),
            persist_run=True,
            refresh_dogfood_summary=True,
        )
    except (OSError, ValueError) as exc:
        return PlatformFindingIngestResult("failed", f"ingest_failed: {exc}")


def _auto_ingest_disabled_by_setting() -> bool:
    value = os.environ.get(AUTO_INGEST_ENV)
    if value is None:
        return False
    normalized = value.strip().lower()
    return bool(normalized) and normalized in AUTO_INGEST_FALSE_VALUES


def _source_command(argv: list[str]) -> str:
    if not argv:
        return "python3 dev/scripts/devctl.py"
    return "python3 dev/scripts/devctl.py " + " ".join(str(part) for part in argv)


def _refresh_governance_summary(*, log_path: Path, summary_root: Path) -> dict[str, str]:
    report = build_governance_review_report(
        log_path=log_path,
        max_rows=5000,
    )
    return write_governance_review_summary(report, summary_root=summary_root)


def _result_from_write(
    write_result: FindingBacklogWriteResult,
    *,
    status: str,
    reason: str,
    summary_paths: dict[str, str],
    promotion_candidate: dict[str, Any] | None,
) -> PlatformFindingIngestResult:
    return PlatformFindingIngestResult(
        status=status,
        reason=reason,
        log_path=write_result.log_path,
        row=write_result.row,
        finding=(
            None if write_result.finding is None else write_result.finding.to_dict()
        ),
        summary_paths=summary_paths,
        promotion_candidate=promotion_candidate,
    )


__all__ = [
    "AUTO_INGEST_DISABLE_ENV",
    "AUTO_INGEST_ENV",
    "AUTO_INGEST_FALSE_VALUES",
    "DogfoodFindingIngestOptions",
    "PlatformFindingIngest",
    "PlatformFindingIngestResult",
    "maybe_auto_ingest_devctl_result",
]
