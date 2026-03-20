"""Guard-specific adapters for the shared finding contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .finding_contracts import (
    FINDING_CONTRACT_ID,
    FINDING_SCHEMA_VERSION,
    FindingIdentitySeed,
    FindingRecord,
    _positive_int,
    build_finding_id,
)
from .value_coercion import coerce_string

GUARD_RULE_VERSION = 1


@dataclass(frozen=True, slots=True)
class GuardFindingPolicy:
    """Policy inputs for projecting a guard violation into a finding."""

    guard_command: str
    severity: str = "high"
    risk_type: str = ""
    review_lens: str = "maintainability"
    source_artifact: str = "guard-report:violations"


def _guard_signals(violation: Mapping[str, object]) -> tuple[str, ...]:
    """Build human-readable signals from guard violation metadata."""
    signals: list[str] = []
    reason = coerce_string(violation.get("reason"))
    if reason:
        signals.append(reason)
    guidance = coerce_string(violation.get("guidance"))
    if guidance:
        signals.append(guidance)
    matches = violation.get("matches")
    if isinstance(matches, list):
        for match in matches[:3]:
            if isinstance(match, dict):
                signals.append(
                    "duplicate: "
                    f"{coerce_string(match.get('path'))}::{coerce_string(match.get('name'))}"
                )
    return tuple(signals)


def finding_from_guard_violation(
    violation: Mapping[str, object],
    *,
    repo_name: str,
    repo_path: str = "",
    policy: GuardFindingPolicy,
) -> FindingRecord:
    """Normalize one guard violation into the canonical finding contract."""
    file_path = coerce_string(violation.get("path") or violation.get("file_path"))
    symbol = coerce_string(
        violation.get("function_name") or violation.get("symbol") or violation.get("qualname")
    )
    line = _positive_int(violation.get("line") or violation.get("start_line"))
    end_line = _positive_int(violation.get("end_line"))
    signals = _guard_signals(violation)
    return FindingRecord(
        schema_version=FINDING_SCHEMA_VERSION,
        contract_id=FINDING_CONTRACT_ID,
        finding_id=build_finding_id(
            FindingIdentitySeed(
                repo_name=repo_name,
                repo_path=repo_path,
                signal_type="guard",
                check_id=policy.guard_command,
                file_path=file_path,
                symbol=symbol,
                line=line,
                end_line=end_line,
                risk_type=policy.risk_type,
                review_lens=policy.review_lens,
                signals=signals,
            )
        ),
        signal_type="guard",
        check_id=policy.guard_command,
        rule_id=policy.guard_command,
        rule_version=GUARD_RULE_VERSION,
        repo_name=repo_name,
        repo_path=repo_path,
        file_path=file_path,
        symbol=symbol,
        line=line,
        end_line=end_line,
        severity=policy.severity,
        risk_type=policy.risk_type,
        review_lens=policy.review_lens,
        ai_instruction=coerce_string(violation.get("guidance") or violation.get("ai_instruction")),
        signals=signals,
        source_command=policy.guard_command,
        source_artifact=policy.source_artifact,
    )
