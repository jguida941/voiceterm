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

from dev.scripts.devctl.runtime.feature_proof_receipt import (  # noqa: E402
    feature_proof_receipt_artifact_relpath,
    feature_proof_receipt_from_mapping,
    validate_non_trivial_output_proof,
)

COMMAND = "check_feature_has_proof_receipt"
DEFAULT_BASE_REF = "@{u}"


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
) -> FeatureProofReceiptGuardReport:
    warnings: list[str] = []
    if commit_shas is None:
        commit_shas, range_warnings = _git_commit_range(
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
            if require_proven_passed:
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


def _git_commit_range(
    *,
    repo_root: Path,
    base_ref: str,
    head_ref: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not _git_ref_exists(repo_root, base_ref):
        return (), (f"base_ref_unavailable:{base_ref}",)
    result = subprocess.run(
        ("git", "rev-list", "--reverse", f"{base_ref}..{head_ref}"),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        warning = result.stderr.strip() or result.stdout.strip() or "git_rev_list_failed"
        return (), (warning,)
    commits = tuple(line.strip() for line in result.stdout.splitlines() if line.strip())
    return commits, ()


def _git_ref_exists(repo_root: Path, ref: str) -> bool:
    result = subprocess.run(
        ("git", "rev-parse", "--verify", ref),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


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
    except Exception as exc:  # pragma: no cover - top-level guard safety
        return emit_runtime_error(COMMAND, args.format, f"{exc.__class__.__name__}: {exc}")
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2))
    else:
        print(_render_md(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
