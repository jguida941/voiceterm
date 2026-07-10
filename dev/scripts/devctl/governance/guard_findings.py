"""Helpers for projecting guard violations into canonical findings."""

from __future__ import annotations

from typing import Any

from ..runtime import GuardFindingPolicy, finding_from_guard_violation


def build_guard_findings(
    guard_reports: dict[str, dict[str, Any]],
    *,
    repo_name: str,
    source_artifact: str,
) -> list[dict[str, Any]]:
    """Normalize report-backed guard violations into canonical finding rows."""
    findings: list[dict[str, Any]] = []
    for guard_key, report in guard_reports.items():
        if not isinstance(report, dict):
            continue
        violations = report.get("violations")
        if not isinstance(violations, list):
            continue
        policy = GuardFindingPolicy(
            guard_command=guard_key,
            risk_type=guard_key,
            review_lens="maintainability",
            source_artifact=source_artifact,
        )
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            path = str(violation.get("path") or violation.get("file_path") or "").strip()
            if not path:
                continue
            findings.append(
                finding_from_guard_violation(
                    violation,
                    repo_name=repo_name,
                    repo_path="",
                    policy=policy,
                ).to_dict()
            )
    return findings
