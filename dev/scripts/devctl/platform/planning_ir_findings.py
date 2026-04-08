"""Finding normalization helpers for PlanningIRSnapshot inputs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..runtime.finding_contracts import (
    FINDING_CONTRACT_ID,
    FINDING_SCHEMA_VERSION,
    FindingIdentitySeed,
    FindingRecord,
    build_finding_id,
)


def live_findings_from_governance_report(
    report: Mapping[str, Any],
    *,
    repo_name: str,
) -> tuple[FindingRecord, ...]:
    """Normalize recent confirmed governance findings into FindingRecord."""
    recent_findings = report.get("recent_findings")
    if not isinstance(recent_findings, list):
        return ()

    source_artifact = str(report.get("log_path") or "").strip()
    findings: list[FindingRecord] = []
    for row in recent_findings:
        if not isinstance(row, Mapping):
            continue
        finding = _finding_from_governance_row(
            row,
            repo_name=repo_name,
            source_artifact=source_artifact,
        )
        if finding is not None:
            findings.append(finding)
    return tuple(findings)


def _finding_from_governance_row(
    row: Mapping[str, Any],
    *,
    repo_name: str,
    source_artifact: str,
) -> FindingRecord | None:
    if _text(row.get("verdict")) != "confirmed_issue":
        return None

    file_path = _text(row.get("file_path"))
    check_id = _text(row.get("check_id"))
    if not file_path or not check_id:
        return None

    signal_type = _text(row.get("signal_type")) or "governance-review"
    line = _positive_int(row.get("line"))
    finding_id = _text(row.get("finding_id")) or build_finding_id(
        FindingIdentitySeed(
            repo_name=repo_name,
            repo_path=_text(row.get("repo_path")),
            signal_type=signal_type,
            check_id=check_id,
            file_path=file_path,
            symbol=_text(row.get("symbol")),
            line=line,
            risk_type=_text(row.get("risk_type")) or _text(row.get("finding_class")),
            review_lens=_text(row.get("prevention_surface")),
            signals=("confirmed_issue",),
        )
    )
    return FindingRecord(
        schema_version=FINDING_SCHEMA_VERSION,
        contract_id=FINDING_CONTRACT_ID,
        finding_id=finding_id,
        signal_type=signal_type,
        check_id=check_id,
        rule_id=check_id,
        rule_version=1,
        repo_name=repo_name,
        repo_path=_text(row.get("repo_path")),
        file_path=file_path,
        symbol=_text(row.get("symbol")),
        line=line,
        severity=_text(row.get("severity")) or "medium",
        risk_type=_text(row.get("risk_type")) or _text(row.get("finding_class")),
        review_lens=_text(row.get("prevention_surface")),
        ai_instruction=_text(row.get("notes")),
        signals=("confirmed_issue",),
        source_command=_text(row.get("source_command"))
        or "python3 dev/scripts/devctl.py governance-review --format md",
        source_artifact=source_artifact,
    )


def _text(value: object) -> str:
    return str(value or "").strip()


def _positive_int(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


__all__ = ["live_findings_from_governance_report"]
