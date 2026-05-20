"""Markdown rendering for substrate commit checks."""

from __future__ import annotations

from typing import Protocol


class SubstrateCommitReport(Protocol):
    ok: bool
    base_ref: str
    head_ref: str
    plan_index_path: str
    policy_path: str
    mandate_packet_id: str
    mandate_observed_at_utc: str
    scanned_commit_count: int
    substrate_commit_count: int
    covered_commit_count: int
    violation_count: int
    legacy_gap_count: int
    warnings: tuple[str, ...]
    violations: tuple[dict[str, object], ...]
    legacy_gaps: tuple[dict[str, object], ...]


def render_markdown(report: SubstrateCommitReport, *, command: str) -> str:
    lines = [f"# {command}", ""]
    for key, value in (
        ("ok", report.ok),
        ("base_ref", report.base_ref),
        ("head_ref", report.head_ref),
        ("plan_index_path", report.plan_index_path),
        ("policy_path", report.policy_path),
        ("mandate_packet_id", report.mandate_packet_id),
        ("mandate_observed_at_utc", report.mandate_observed_at_utc),
        ("scanned_commit_count", report.scanned_commit_count),
        ("substrate_commit_count", report.substrate_commit_count),
        ("covered_commit_count", report.covered_commit_count),
        ("violation_count", report.violation_count),
        ("legacy_gap_count", report.legacy_gap_count),
    ):
        lines.append(f"- {key}: {value}")
    if report.warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- {warning}" for warning in report.warnings)
    if report.violations:
        lines.extend(["", "## Violations"])
        lines.extend(render_gap(gap) for gap in report.violations)
    if report.legacy_gaps:
        lines.extend(["", "## Legacy Gaps"])
        lines.extend(render_gap(gap) for gap in report.legacy_gaps)
    return "\n".join(lines) + "\n"


def render_gap(gap: dict[str, object]) -> str:
    paths = ", ".join(str(path) for path in gap.get("changed_paths", ()))
    return (
        f"- `{gap.get('commit_sha')}` {gap.get('reason')} "
        f"scope={gap.get('scope')} paths={paths}"
    )
