#!/usr/bin/env python3
"""Require verified GitMutationProofReceipt rows for commits in a range."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, emit_runtime_error

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.runtime.git_mutation_proof_receipt import (
    GitMutationProofReceipt,
    read_git_mutation_proof_receipts,
)
try:
    from dev.scripts.checks.git_support.range import git_commit_range
except ModuleNotFoundError:  # pragma: no cover - direct script fallback
    from git_support.range import git_commit_range

COMMAND = "check_commit_complete_proof"
DEFAULT_BASE_REF = "@{u}"


@dataclass(frozen=True, slots=True)
class CommitCompleteProofViolation:
    commit_sha: str
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CommitCompleteProofReport:
    command: str
    ok: bool
    base_ref: str
    head_ref: str
    commit_count: int
    verified_receipt_count: int
    violation_count: int
    violations: tuple[dict[str, str], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = "CommitCompleteProofGuard"


def evaluate_commit_complete_proof(
    *,
    repo_root: Path = REPO_ROOT,
    base_ref: str = DEFAULT_BASE_REF,
    head_ref: str = "HEAD",
    commit_shas: tuple[str, ...] | None = None,
    require_non_empty_range: bool = False,
) -> CommitCompleteProofReport:
    warnings: list[str] = []
    if commit_shas is None:
        commit_shas, range_warnings = git_commit_range(
            repo_root=repo_root,
            base_ref=base_ref,
            head_ref=head_ref,
        )
        warnings.extend(range_warnings)
    receipts: tuple[GitMutationProofReceipt, ...] = read_git_mutation_proof_receipts(
        repo_root
    )
    verified_commits = {
        receipt.expected_sha
        for receipt in receipts
        if receipt.mutation_kind == "commit" and receipt.verified
    }
    violations: list[CommitCompleteProofViolation] = []
    if not commit_shas and require_non_empty_range:
        violations.append(
            CommitCompleteProofViolation(
                commit_sha="",
                reason="empty_commit_range",
                detail="Strict proof mode requires at least one commit to inspect.",
            )
        )
    for commit_sha in commit_shas:
        if commit_sha not in verified_commits:
            violations.append(
                CommitCompleteProofViolation(
                    commit_sha=commit_sha,
                    reason="missing_verified_commit_proof",
                    detail=(
                        "No verified GitMutationProofReceipt(commit) row exists "
                        "for this commit SHA."
                    ),
                )
            )
    return CommitCompleteProofReport(
        command=COMMAND,
        ok=not violations,
        base_ref=base_ref,
        head_ref=head_ref,
        commit_count=len(commit_shas),
        verified_receipt_count=len(verified_commits),
        violation_count=len(violations),
        violations=tuple(violation.to_dict() for violation in violations),
        warnings=tuple(warnings),
    )


def _render_md(report: CommitCompleteProofReport) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- base_ref: `{report.base_ref}`")
    lines.append(f"- head_ref: `{report.head_ref}`")
    lines.append(f"- commit_count: {report.commit_count}")
    lines.append(f"- verified_receipt_count: {report.verified_receipt_count}")
    lines.append(f"- violation_count: {report.violation_count}")
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
                f"- {violation.get('commit_sha')} {violation.get('reason')}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-ref", default=DEFAULT_BASE_REF)
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--require-non-empty-range", action="store_true")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    try:
        report = evaluate_commit_complete_proof(
            base_ref=args.since_ref,
            head_ref=args.head_ref,
            require_non_empty_range=args.require_non_empty_range,
        )
    # broad-except: allow reason=guard entrypoints must emit structured reports instead of tracebacks fallback=typed runtime error
    except Exception as exc:
        return emit_runtime_error(
            COMMAND,
            args.format,
            f"{exc.__class__.__name__}: {exc}",
        )
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print(_render_md(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
