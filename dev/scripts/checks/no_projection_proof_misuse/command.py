#!/usr/bin/env python3
"""Reject progress projections that claim git success without proof receipts."""

from __future__ import annotations

import argparse
import json
import re
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
from dev.scripts.devctl.runtime.repo_portability import resolve_guard_mandate
from dev.scripts.devctl.runtime.stage_progress import DEFAULT_PROGRESS_ROOT_REL
from dev.scripts.devctl.runtime.value_coercion import coerce_int

COMMAND = "check_no_projection_proof_misuse"
_SHA_RE = re.compile(r"\b[0-9a-fA-F]{7,40}\b")
_POLICY_BASELINE_KEYS = (
    "legacy_progress_baseline_line",
    "ignore_before_line",
)


@dataclass(frozen=True, slots=True)
class ProjectionProofMisuseViolation:
    path: str
    line_no: int
    phase: str
    detail: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProjectionProofMisuseReport:
    command: str
    ok: bool
    progress_path: str
    ignore_before_line: int
    ignore_before_line_source: str
    projection_success_claims: int
    verified_commit_proof_count: int
    verified_push_proof_count: int
    violation_count: int
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = "NoProjectionProofMisuseGuard"


def evaluate_no_projection_proof_misuse(
    *,
    repo_root: Path = REPO_ROOT,
    progress_path: Path | None = None,
    ignore_before_line: int | None = None,
) -> ProjectionProofMisuseReport:
    path = progress_path or repo_root / DEFAULT_PROGRESS_ROOT_REL / "events.jsonl"
    baseline_line, baseline_source = _resolve_ignore_before_line(
        repo_root=repo_root,
        ignore_before_line=ignore_before_line,
    )
    receipts: tuple[GitMutationProofReceipt, ...] = read_git_mutation_proof_receipts(
        repo_root
    )
    verified_commits = {
        receipt.expected_sha
        for receipt in receipts
        if receipt.mutation_kind == "commit" and receipt.verified
    }
    verified_push_shas = {
        receipt.expected_sha
        for receipt in receipts
        if receipt.mutation_kind == "push" and receipt.verified
    }
    violations: list[ProjectionProofMisuseViolation] = []
    claims = 0
    warnings: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    for line_no, raw in enumerate(lines, start=1):
        if line_no <= baseline_line:
            continue
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            warnings.append(f"invalid_progress_json:{line_no}")
            continue
        if not isinstance(payload, dict):
            continue
        phase = str(payload.get("phase") or "")
        detail = str(payload.get("detail") or "")
        if phase != "commit.complete":
            continue
        claims += 1
        sha = _first_sha(detail)
        if sha not in verified_commits:
            violations.append(
                ProjectionProofMisuseViolation(
                    path=_display_path(path, repo_root),
                    line_no=line_no,
                    phase=phase,
                    detail=detail,
                    reason="commit_success_projection_without_git_mutation_proof",
                )
            )
    return ProjectionProofMisuseReport(
        command=COMMAND,
        ok=not violations,
        progress_path=_display_path(path, repo_root),
        ignore_before_line=baseline_line,
        ignore_before_line_source=baseline_source,
        projection_success_claims=claims,
        verified_commit_proof_count=len(verified_commits),
        verified_push_proof_count=len(verified_push_shas),
        violation_count=len(violations),
        violations=tuple(violation.to_dict() for violation in violations),
        warnings=tuple(warnings),
    )


def _first_sha(text: str) -> str:
    match = _SHA_RE.search(text)
    return match.group(0) if match else ""


def _resolve_ignore_before_line(
    *,
    repo_root: Path,
    ignore_before_line: int | None,
) -> tuple[int, str]:
    if ignore_before_line is not None:
        return max(0, int(ignore_before_line)), "cli"
    mandate = resolve_guard_mandate(COMMAND, repo_root=repo_root)
    for key in _POLICY_BASELINE_KEYS:
        line = coerce_int(mandate.settings.get(key))
        if line > 0:
            return line, f"repo_policy:{key}"
    return 0, "default_zero"


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _render_md(report: ProjectionProofMisuseReport) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- progress_path: `{report.progress_path}`")
    lines.append(f"- ignore_before_line: {report.ignore_before_line}")
    lines.append(f"- ignore_before_line_source: {report.ignore_before_line_source}")
    lines.append(f"- projection_success_claims: {report.projection_success_claims}")
    lines.append(f"- verified_commit_proof_count: {report.verified_commit_proof_count}")
    lines.append(f"- verified_push_proof_count: {report.verified_push_proof_count}")
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
                f"{violation.get('path')}:{violation.get('line_no')} "
                f"{violation.get('reason')}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progress-path", default="")
    parser.add_argument(
        "--ignore-before-line",
        type=int,
        default=None,
        help=(
            "Treat existing progress rows through this 1-based line as a legacy "
            "baseline and scan only later rows. If omitted, the repo-policy "
            "baseline for this guard is used."
        ),
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    progress_path = Path(args.progress_path) if args.progress_path else None
    try:
        report = evaluate_no_projection_proof_misuse(
            progress_path=progress_path,
            ignore_before_line=args.ignore_before_line,
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
