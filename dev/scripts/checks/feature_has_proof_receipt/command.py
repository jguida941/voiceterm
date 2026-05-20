#!/usr/bin/env python3
"""Require FeatureProofReceipt artifacts for commits in a git range."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, emit_runtime_error

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.runtime.feature_proof_receipt import (
    feature_proof_receipt_artifact_relpath,
    feature_proof_receipt_from_mapping,
    validate_non_trivial_output_proof,
)
try:
    from dev.scripts.checks.git_support.range import git_commit_range
except ModuleNotFoundError:  # pragma: no cover - direct script fallback
    from git_support.range import git_commit_range

COMMAND = "check_feature_has_proof_receipt"
DEFAULT_BASE_REF = "@{u}"

PROOF_LEDGER_EXACT_PATHS = frozenset(
    {
        "dev/audits/REVIEW_SNAPSHOT.md",
        "dev/state/ground_truth_probe_receipts.jsonl",
        "dev/state/plan_index.jsonl",
        "dev/state/plan_ingestion_receipts.jsonl",
        "dev/state/plan_row_closure_receipts.jsonl",
        "dev/state/plan_source_snapshots.jsonl",
    }
)
PROOF_LEDGER_PATH_PREFIXES = (
    "dev/reports/commit_receipts/",
    "dev/reports/feature_lifecycle_proofs/",
    "dev/reports/feature_proof_receipts/",
)


@dataclass(frozen=True)
class FeatureProofReceiptViolation:
    commit_sha: str
    reason: str
    path: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class FeatureProofReceiptGuardReport:
    command: str
    ok: bool
    base_ref: str
    head_ref: str
    commit_count: int
    receipt_count: int
    assertions_evaluated_count: int
    violation_count: int
    non_proven_count: int
    violations: tuple[dict[str, str], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = "FeatureProofReceiptGuard"


def evaluate_feature_has_proof_receipt(
    *,
    repo_root: Path = REPO_ROOT,
    base_ref: str = DEFAULT_BASE_REF,
    head_ref: str = "HEAD",
    commit_shas: tuple[str, ...] | None = None,
    require_proven_passed: bool = False,
    require_non_empty_range: bool = False,
    require_non_trivial_output_proof: bool = False,
    commit_paths_by_sha: dict[str, tuple[str, ...]] | None = None,
) -> FeatureProofReceiptGuardReport:
    warnings: list[str] = []
    if commit_shas is None:
        commit_shas, range_warnings = git_commit_range(
            repo_root=repo_root,
            base_ref=base_ref,
            head_ref=head_ref,
        )
        warnings.extend(range_warnings)
    violations: list[FeatureProofReceiptViolation] = []
    receipt_count = 0
    non_proven_count = 0
    assertions_evaluated_count = 0

    if not commit_shas and require_non_empty_range:
        violations.append(
            FeatureProofReceiptViolation(
                commit_sha="",
                reason="empty_commit_range",
                path="",
                detail=(
                    "Strict proof mode requires at least one commit to inspect; "
                    "zero checked commits is not proof."
                ),
            )
        )

    for commit_sha in commit_shas:
        changed_paths = _changed_paths_for_commit(
            repo_root,
            commit_sha,
            commit_paths_by_sha=commit_paths_by_sha,
        )
        proven_required = _commit_requires_proven_passed(changed_paths)
        relpath = feature_proof_receipt_artifact_relpath(commit_sha)
        path = repo_root / relpath
        if not path.exists():
            violations.append(
                FeatureProofReceiptViolation(
                    commit_sha=commit_sha,
                    reason="missing_feature_proof_receipt",
                    path=relpath,
                    detail="No FeatureProofReceipt artifact exists for this commit.",
                )
            )
            continue
        receipt_count += 1
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            receipt = feature_proof_receipt_from_mapping(payload)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            violations.append(
                FeatureProofReceiptViolation(
                    commit_sha=commit_sha,
                    reason="invalid_feature_proof_receipt",
                    path=relpath,
                    detail=f"{exc.__class__.__name__}: {exc}",
                )
            )
            continue
        if receipt.commit_sha != commit_sha:
            violations.append(
                FeatureProofReceiptViolation(
                    commit_sha=commit_sha,
                    reason="feature_proof_commit_sha_mismatch",
                    path=relpath,
                    detail=f"receipt commit_sha={receipt.commit_sha!r}",
                )
            )
        if not receipt.connectivity_guards_passed:
            violations.append(
                FeatureProofReceiptViolation(
                    commit_sha=commit_sha,
                    reason="connectivity_guards_not_passed",
                    path=relpath,
                    detail="FeatureProofReceipt.connectivity_guards_passed is false.",
                )
            )
        if receipt.real_life_test_status != "proven_passed":
            non_proven_count += 1
            if require_proven_passed and proven_required:
                violations.append(
                    FeatureProofReceiptViolation(
                        commit_sha=commit_sha,
                        reason="real_life_test_not_proven_passed",
                        path=relpath,
                        detail=(
                            "FeatureProofReceipt.real_life_test_status="
                            f"{receipt.real_life_test_status!r}"
                        ),
                )
            )
            if require_proven_passed and not proven_required:
                warnings.append(
                    "proven_passed_not_required_for_proof_ledger_commit:"
                    f"{commit_sha}"
                )
        if require_non_trivial_output_proof:
            proof = validate_non_trivial_output_proof(
                receipt,
                repo_root=repo_root,
                receipt_path=path,
            )
            assertions_evaluated_count += 4
            if not proof.ok:
                violations.append(
                    FeatureProofReceiptViolation(
                        commit_sha=commit_sha,
                        reason="non_trivial_output_proof_failed",
                        path=relpath,
                        detail=",".join(proof.failure_reasons),
                    )
                )

    return FeatureProofReceiptGuardReport(
        command=COMMAND,
        ok=not violations,
        base_ref=base_ref,
        head_ref=head_ref,
        commit_count=len(commit_shas),
        receipt_count=receipt_count,
        assertions_evaluated_count=assertions_evaluated_count,
        violation_count=len(violations),
        non_proven_count=non_proven_count,
        violations=tuple(violation.to_dict() for violation in violations),
        warnings=tuple(warnings),
    )


def _changed_paths_for_commit(
    repo_root: Path,
    commit_sha: str,
    *,
    commit_paths_by_sha: dict[str, tuple[str, ...]] | None,
) -> tuple[str, ...]:
    if commit_paths_by_sha is not None:
        return commit_paths_by_sha.get(commit_sha, ())
    result = subprocess.run(
        (
            "git",
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "--root",
            commit_sha,
        ),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ()
    return tuple(line.strip() for line in result.stdout.splitlines() if line.strip())


def _commit_requires_proven_passed(changed_paths: tuple[str, ...]) -> bool:
    if not changed_paths:
        return True
    return any(not _is_proof_ledger_path(path) for path in changed_paths)


def _is_proof_ledger_path(path: str) -> bool:
    if path in PROOF_LEDGER_EXACT_PATHS:
        return True
    return path.startswith(PROOF_LEDGER_PATH_PREFIXES)


def _render_md(report: FeatureProofReceiptGuardReport) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- base_ref: `{report.base_ref}`")
    lines.append(f"- head_ref: `{report.head_ref}`")
    lines.append(f"- commit_count: {report.commit_count}")
    lines.append(f"- receipt_count: {report.receipt_count}")
    lines.append(f"- assertions_evaluated_count: {report.assertions_evaluated_count}")
    lines.append(f"- violation_count: {report.violation_count}")
    lines.append(f"- non_proven_count: {report.non_proven_count}")
    if report.warnings:
        lines.append("")
        lines.append("## Warnings")
        for warning in report.warnings:
            lines.append(f"- {warning}")
    if report.violations:
        lines.append("")
        lines.append("## Violations")
        for violation in report.violations:
            lines.append(
                "- "
                f"{violation.get('commit_sha')} "
                f"{violation.get('reason')} "
                f"path={violation.get('path')}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-ref", default=DEFAULT_BASE_REF)
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--require-proven-passed", action="store_true")
    parser.add_argument(
        "--require-non-empty-range",
        action="store_true",
        help="Fail when the selected commit range is empty.",
    )
    parser.add_argument(
        "--require-non-trivial-output-proof",
        action="store_true",
        help=(
            "Validate each receipt with NonTrivialOutputProof: resolved refs, "
            "real pytest node evidence, non-circular evidence, and terminal "
            "role-review refs."
        ),
    )
    parser.add_argument(
        "--strict-proof",
        action="store_true",
        help=(
            "Publication/closure mode: require a non-empty range, "
            "proven_passed receipts, and NonTrivialOutputProof."
        ),
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        report = evaluate_feature_has_proof_receipt(
            base_ref=args.since_ref,
            head_ref=args.head_ref,
            require_proven_passed=args.require_proven_passed or args.strict_proof,
            require_non_empty_range=(
                args.require_non_empty_range or args.strict_proof
            ),
            require_non_trivial_output_proof=(
                args.require_non_trivial_output_proof or args.strict_proof
            ),
        )
    # broad-except: allow reason=guard entrypoints must emit structured reports instead of tracebacks fallback=typed runtime error
    except Exception as exc:  # pragma: no cover - top-level guard safety
        return emit_runtime_error(COMMAND, args.format, f"{exc.__class__.__name__}: {exc}")
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2))
    else:
        print(_render_md(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
