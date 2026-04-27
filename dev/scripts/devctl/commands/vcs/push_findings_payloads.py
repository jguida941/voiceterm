"""Push finding payload builders for governed push reports."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, TypedDict

from ...governance_review.models import GovernanceReviewInput
from ...runtime.finding_contracts import FindingRecord
from ...runtime.finding_payload_contracts import FindingPayload
from ...runtime.platform_finding_ingest import PLATFORM_FINDING_INGEST_CONTRACT_ID
from .push_findings_identity import (
    PushFindingRule,
    coerce_push_finding_rule,
    push_finding_record,
)


class PushFindingIngestPayload(TypedDict):
    """Report-local pointer to the canonical finding-ingest seam."""

    contract_id: str
    review_input: dict[str, Any]


class PushFindingPayload(FindingPayload, total=False):
    """Push-report compatibility view over the canonical Finding contract."""

    type: str
    message: str
    evidence: dict[str, object]
    platform_finding_ingest: PushFindingIngestPayload


def append_finding(
    state: object,
    finding_rule: PushFindingRule | str,
    message: str,
    *,
    evidence: dict[str, object] | None = None,
) -> None:
    finding = build_push_finding(
        state,
        finding_rule,
        message,
        evidence=evidence,
    )

    findings = getattr(state, "findings", None)
    if not isinstance(findings, list):
        findings = []

        try:
            setattr(state, "findings", findings)
        except (AttributeError, TypeError):
            return

    if finding not in findings:
        findings.append(finding)

    errors = getattr(state, "errors", None)
    if isinstance(errors, list) and message not in errors:
        errors.append(message)


def build_push_finding(
    state: object,
    finding_rule: PushFindingRule | str,
    message: str,
    *,
    evidence: dict[str, object] | None = None,
) -> PushFindingPayload:
    """Build one report-compatible finding from the canonical finding contract."""
    rule = coerce_push_finding_rule(finding_rule)
    repo_root = state_repo_root(state)

    record = push_finding_record(
        rule,
        message=message,
        repo_root=repo_root,
    )

    finding = push_report_finding_payload(
        record,
        rule=rule,
        message=message,
    )

    if evidence:
        finding["evidence"] = evidence

    return finding


def push_report_finding_payload(
    record: FindingRecord,
    *,
    rule: PushFindingRule,
    message: str,
) -> PushFindingPayload:
    review_input = push_governance_review_input(
        record,
        rule=rule,
        message=message,
    )

    finding = PushFindingPayload(record.to_dict())
    finding["type"] = rule.finding_type
    finding["message"] = message
    finding["platform_finding_ingest"] = {
        "contract_id": PLATFORM_FINDING_INGEST_CONTRACT_ID,
        "review_input": asdict(review_input),
    }

    return finding


def push_governance_review_input(
    record: FindingRecord,
    *,
    rule: PushFindingRule,
    message: str,
) -> GovernanceReviewInput:
    review_input = GovernanceReviewInput(
        signal_type=record.signal_type,
        check_id=record.check_id,
        verdict="confirmed_issue",
        file_path=record.file_path,
        symbol=record.symbol,
        severity=record.severity,
        risk_type=record.risk_type,
        source_command=record.source_command,
        repo_name=record.repo_name or None,
        repo_path=record.repo_path or None,
        notes=message,
        finding_type=rule.finding_type,
        finding_id=record.finding_id,
        finding_class=rule.finding_class,
        recurrence_risk=rule.recurrence_risk,
        prevention_surface=rule.prevention_surface,
    )

    return review_input


def state_repo_root(state: object) -> Path | None:
    value = str(getattr(state, "repo_root", "") or "").strip()
    if not value:
        return None

    return Path(value)


__all__ = [
    "PushFindingIngestPayload",
    "PushFindingPayload",
    "append_finding",
    "build_push_finding",
    "push_governance_review_input",
    "push_report_finding_payload",
    "state_repo_root",
]
