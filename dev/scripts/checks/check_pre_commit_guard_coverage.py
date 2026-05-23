#!/usr/bin/env python3
"""Verify the managed pre-commit hook runs the required guard gate."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        utc_timestamp,
    )


COMMAND = "check_pre_commit_guard_coverage"
CONTRACT_ID = "PreCommitGuardCoverage"
DEFAULT_HOOK_PATH = REPO_ROOT / ".git/hooks/pre-commit"


@dataclass(frozen=True, slots=True)
class HookGuardRequirement:
    guard_id: str
    required_text: str
    required_now: bool
    rationale: str


@dataclass(frozen=True, slots=True)
class HookGuardCheck:
    guard_id: str
    status: str
    required_text: str
    matched_text: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


REQUIRED_HOOK_GUARDS: tuple[HookGuardRequirement, ...] = (
    HookGuardRequirement(
        guard_id="check_role_lane_mutation_authority",
        required_text="check_role_lane_mutation_authority.py --mode pre_mutation",
        required_now=True,
        rationale="G1 pre-mutation role-lane gate must run before commit.",
    ),
    HookGuardRequirement(
        guard_id="check_current_plan_authority",
        required_text="check_current_plan_authority.py",
        required_now=True,
        rationale="G8 requires current-plan authority on the pre-commit path.",
    ),
    HookGuardRequirement(
        guard_id="check_orphan_files",
        required_text="check_orphan_files.py",
        required_now=True,
        rationale="G2 orphan-file guard must prevent half-wired files before commit.",
    ),
    HookGuardRequirement(
        guard_id="check_feature_completion",
        required_text="check_feature_completion.py",
        required_now=True,
        rationale="G3 feature-completion guard must prevent half-built guard features.",
    ),
    HookGuardRequirement(
        guard_id="check_plan_row_must_advance",
        required_text="check_plan_row_must_advance.py",
        required_now=True,
        rationale="G4 plan-row advancement guard must stop evidence churn before commit.",
    ),
    HookGuardRequirement(
        guard_id="check_no_ingestion_churn_without_advancement",
        required_text="check_no_ingestion_churn_without_advancement.py",
        required_now=True,
        rationale="G5 ingestion-churn guard must stop repeated snapshots before commit.",
    ),
    HookGuardRequirement(
        guard_id="check_receipt_schema_validation",
        required_text="check_receipt_schema_validation.py",
        required_now=True,
        rationale="G11 receipt-schema guard must validate receipt-store writes before commit.",
    ),
    HookGuardRequirement(
        guard_id="check_receipt_store_has_active_consumer",
        required_text="check_receipt_store_has_active_consumer.py",
        required_now=True,
        rationale="G12 receipt-store consumer guard must block orphan receipt stores.",
    ),
    HookGuardRequirement(
        guard_id="check_receipt_store_coverage_sweep",
        required_text="check_receipt_store_coverage_sweep.py",
        required_now=True,
        rationale="G15.1 receipt-store sweep must block stores without schema/provenance coverage.",
    ),
    HookGuardRequirement(
        guard_id="check_every_applied_row_has_closure_receipt",
        required_text="check_every_applied_row_has_closure_receipt.py",
        required_now=True,
        rationale="G13 terminal PlanRow closure guard must run before commit.",
    ),
    HookGuardRequirement(
        guard_id="check_receipt_commit_anchor_refs",
        required_text="check_receipt_commit_anchor_refs.py",
        required_now=True,
        rationale="G14 receipt commit-anchor guard must block orphan SHAs.",
    ),
)


def build_report(*, hook_path: Path = DEFAULT_HOOK_PATH) -> dict[str, object]:
    hook_text = ""
    warnings: list[str] = []
    if hook_path.exists():
        hook_text = hook_path.read_text(encoding="utf-8")
    else:
        warnings.append(f"pre-commit hook missing: {hook_path}")

    checks = tuple(_check_requirement(requirement, hook_text) for requirement in REQUIRED_HOOK_GUARDS)
    violations = tuple(
        check.to_dict()
        for check in checks
        if check.status == "missing_required"
    )
    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "hook_path": str(_repo_relative(hook_path)),
        "check_count": len(checks),
        "ok_count": sum(1 for check in checks if check.status == "ok"),
        "expected_pending_count": sum(
            1 for check in checks if check.status == "expected_pending"
        ),
        "violation_count": len(violations),
        "checks": [check.to_dict() for check in checks],
        "violations": list(violations),
        "warnings": warnings,
    }


def _check_requirement(
    requirement: HookGuardRequirement,
    hook_text: str,
) -> HookGuardCheck:
    if requirement.required_text in hook_text:
        return HookGuardCheck(
            guard_id=requirement.guard_id,
            status="ok",
            required_text=requirement.required_text,
            matched_text=requirement.required_text,
            detail="required hook invocation present",
        )
    if requirement.required_now:
        return HookGuardCheck(
            guard_id=requirement.guard_id,
            status="missing_required",
            required_text=requirement.required_text,
            matched_text="",
            detail=requirement.rationale,
        )
    return HookGuardCheck(
        guard_id=requirement.guard_id,
        status="expected_pending",
        required_text=requirement.required_text,
        matched_text="",
        detail=requirement.rationale,
    )


def _repo_relative(path: Path) -> Path:
    try:
        return path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return path


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- hook_path: `{report.get('hook_path')}`")
    lines.append(f"- check_count: {report.get('check_count')}")
    lines.append(f"- ok_count: {report.get('ok_count')}")
    lines.append(f"- expected_pending_count: {report.get('expected_pending_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    checks = report.get("checks")
    if isinstance(checks, Sequence) and not isinstance(checks, (str, bytes)):
        lines.extend(("", "## Checks", ""))
        for check in checks:
            if not isinstance(check, Mapping):
                continue
            lines.append(
                f"- {check.get('guard_id')}: {check.get('status')} "
                f"({check.get('detail')})"
            )
    warnings = report.get("warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)) and warnings:
        lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hook-path", type=Path, default=DEFAULT_HOOK_PATH)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(hook_path=args.hook_path)
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
