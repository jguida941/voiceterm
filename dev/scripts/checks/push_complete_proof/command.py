#!/usr/bin/env python3
"""Require verified GitMutationProofReceipt evidence for pushed refs."""

from __future__ import annotations

import argparse
import json
import subprocess
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

COMMAND = "check_push_complete_proof"


@dataclass(frozen=True, slots=True)
class PushCompleteProofViolation:
    expected_sha: str
    remote: str
    branch: str
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PushCompleteProofReport:
    command: str
    ok: bool
    remote: str
    branch: str
    expected_sha: str
    claim_supplied: bool
    verified_receipt_count: int
    violation_count: int
    violations: tuple[dict[str, str], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = "PushCompleteProofGuard"


def evaluate_push_complete_proof(
    *,
    repo_root: Path = REPO_ROOT,
    remote: str = "",
    branch: str = "",
    expected_sha: str = "",
    allow_live_head_default: bool = False,
) -> PushCompleteProofReport:
    resolved_remote = remote or _first_line(_git_stdout(repo_root, "remote"))
    resolved_branch = branch or _git_stdout(
        repo_root,
        "rev-parse",
        "--abbrev-ref",
        "HEAD",
    )
    claim_supplied = bool(expected_sha)
    resolved_sha = expected_sha
    if not resolved_sha and allow_live_head_default:
        resolved_sha = _git_stdout(repo_root, "rev-parse", "HEAD")
        claim_supplied = bool(resolved_sha)
    receipts: tuple[GitMutationProofReceipt, ...] = read_git_mutation_proof_receipts(
        repo_root
    )
    if not resolved_sha:
        return PushCompleteProofReport(
            command=COMMAND,
            ok=True,
            remote=resolved_remote,
            branch=resolved_branch,
            expected_sha="",
            claim_supplied=False,
            verified_receipt_count=0,
            violation_count=0,
            warnings=("no_expected_push_sha_claim",),
        )
    verified = [
        receipt
        for receipt in receipts
        if receipt.mutation_kind == "push"
        and receipt.verified
        and receipt.remote_name == resolved_remote
        and receipt.branch_name == resolved_branch
        and receipt.expected_sha == resolved_sha
        and receipt.observed_remote_sha == resolved_sha
    ]
    violations: list[PushCompleteProofViolation] = []
    if not verified:
        violations.append(
            PushCompleteProofViolation(
                expected_sha=resolved_sha,
                remote=resolved_remote,
                branch=resolved_branch,
                reason="missing_verified_push_proof",
                detail=(
                    "No verified GitMutationProofReceipt(push) row proves the "
                    "remote branch equals the expected commit SHA."
                ),
            )
        )
    return PushCompleteProofReport(
        command=COMMAND,
        ok=not violations,
        remote=resolved_remote,
        branch=resolved_branch,
        expected_sha=resolved_sha,
        claim_supplied=claim_supplied,
        verified_receipt_count=len(verified),
        violation_count=len(violations),
        violations=tuple(violation.to_dict() for violation in violations),
    )


def _git_stdout(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _first_line(text: str) -> str:
    return text.splitlines()[0].strip() if text.splitlines() else ""


def _render_md(report: PushCompleteProofReport) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- remote: `{report.remote}`")
    lines.append(f"- branch: `{report.branch}`")
    lines.append(f"- expected_sha: `{report.expected_sha}`")
    lines.append(f"- claim_supplied: {report.claim_supplied}")
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
                "- "
                f"{violation.get('remote')}/{violation.get('branch')} "
                f"{violation.get('reason')}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", default="")
    parser.add_argument("--branch", default="")
    parser.add_argument("--expected-sha", default="")
    parser.add_argument(
        "--allow-live-head-default",
        action="store_true",
        help=(
            "Use the live HEAD as the expected SHA when no explicit push-complete "
            "claim supplied one. Intended for manual debugging, not check-router."
        ),
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    try:
        report = evaluate_push_complete_proof(
            remote=args.remote,
            branch=args.branch,
            expected_sha=args.expected_sha,
            allow_live_head_default=args.allow_live_head_default,
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
