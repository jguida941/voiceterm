"""Finding identity helpers for governed push reports."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from ...runtime.finding_contracts import (
    FINDING_CONTRACT_ID,
    FINDING_SCHEMA_VERSION,
    FindingIdentitySeed,
    FindingRecord,
    build_finding_id,
    finding_correlation_context,
)

PUSH_FINDING_SIGNAL_TYPE = "guard"
PUSH_FINDING_CHECK_ID = "vcs.push.execution_truth"
PUSH_FINDING_FILE_PATH = "dev/scripts/devctl/commands/vcs/push.py"
PUSH_FINDING_SOURCE_COMMAND = "python3 dev/scripts/devctl.py push"


@dataclass(frozen=True, slots=True)
class PushFindingRule:
    """Canonical rule metadata for one governed-push finding."""

    finding_type: str
    rule_id: str
    symbol: str
    risk_type: str = "authority_boundary"
    review_lens: str = "governed_push"
    finding_class: str = "authority_boundary"
    recurrence_risk: str = "systemic"
    prevention_surface: str = "authority_rule"


BRANCH_IDENTITY_VIOLATION = PushFindingRule(
    finding_type="BranchIdentityViolation",
    rule_id="vcs.push.branch_identity",
    symbol="branch_identity",
)
APPROVED_TARGET_IDENTITY_VIOLATION = PushFindingRule(
    finding_type="ApprovedTargetIdentityViolation",
    rule_id="vcs.push.approved_target_identity",
    symbol="approved_target_identity",
)
APPROVED_TARGET_IDENTITY_MAX_AGE_SECONDS = 3600
FINDING_RECORD_TEMPLATE = FindingRecord(
    schema_version=FINDING_SCHEMA_VERSION,
    contract_id=FINDING_CONTRACT_ID,
    finding_id="",
    signal_type=PUSH_FINDING_SIGNAL_TYPE,
    check_id=PUSH_FINDING_CHECK_ID,
    rule_id="",
    rule_version=1,
    repo_name="",
    repo_path="",
    file_path=PUSH_FINDING_FILE_PATH,
    symbol="",
    severity="critical",
    risk_type="",
    review_lens="",
    ai_instruction="",
    signals=(),
    source_command=PUSH_FINDING_SOURCE_COMMAND,
    source_artifact=PUSH_FINDING_FILE_PATH,
)


def push_finding_record(
    rule: PushFindingRule,
    *,
    message: str,
    repo_root: Path | None,
) -> FindingRecord:
    repo_name = repo_root.name if repo_root is not None else ""
    repo_path = "" if repo_root is None else str(repo_root)
    finding_id = push_finding_id(rule, repo_name=repo_name)
    context = finding_correlation_context(
        finding_id,
        check_id=PUSH_FINDING_CHECK_ID,
        source_artifact=PUSH_FINDING_FILE_PATH,
    )

    return replace(
        FINDING_RECORD_TEMPLATE,
        finding_id=finding_id,
        rule_id=rule.rule_id,
        repo_name=repo_name,
        repo_path=repo_path,
        symbol=rule.symbol,
        risk_type=rule.risk_type,
        review_lens=rule.review_lens,
        ai_instruction=message,
        signals=(rule.finding_type,),
        correlation_id=context.correlation_id,
        causation_id=context.causation_id,
        run_id=context.run_id,
    )


def push_finding_id(rule: PushFindingRule, *, repo_name: str) -> str:
    seed = FindingIdentitySeed(
        repo_name=repo_name,
        repo_path="",
        signal_type=PUSH_FINDING_SIGNAL_TYPE,
        check_id=PUSH_FINDING_CHECK_ID,
        file_path=PUSH_FINDING_FILE_PATH,
        symbol=rule.symbol,
        risk_type=rule.risk_type,
        review_lens=rule.review_lens,
        signals=(rule.finding_type,),
    )

    return build_finding_id(seed)


def coerce_push_finding_rule(finding_rule: PushFindingRule | str) -> PushFindingRule:
    if isinstance(finding_rule, PushFindingRule):
        return finding_rule

    text = str(finding_rule or "PushFinding").strip() or "PushFinding"
    symbol = "".join(
        f"_{char.lower()}" if char.isupper() else char for char in text
    ).strip("_")

    return PushFindingRule(
        finding_type=text,
        rule_id=f"vcs.push.{symbol or 'push_finding'}",
        symbol=symbol or "push_finding",
    )


__all__ = [
    "APPROVED_TARGET_IDENTITY_MAX_AGE_SECONDS",
    "APPROVED_TARGET_IDENTITY_VIOLATION",
    "BRANCH_IDENTITY_VIOLATION",
    "FINDING_RECORD_TEMPLATE",
    "PUSH_FINDING_CHECK_ID",
    "PUSH_FINDING_FILE_PATH",
    "PUSH_FINDING_SIGNAL_TYPE",
    "PUSH_FINDING_SOURCE_COMMAND",
    "PushFindingRule",
    "coerce_push_finding_rule",
    "push_finding_id",
    "push_finding_record",
]
