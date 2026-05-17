#!/usr/bin/env python3
"""Fail closed when a publication candidate is contaminated by dirty worktree state."""

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


COMMAND = "check_publication_scope_integrity"
CONTRACT_ID = "PublicationScopeIntegrityGuard"
DEFERRAL_CONTRACT_ID = "DirtyWorktreeDeferralReceipt"


@dataclass(frozen=True, slots=True)
class PublicationScopeIntegrityViolation:
    path: str
    reason: str
    classification: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PublicationScopeIntegrityReport:
    ok: bool
    staged_path_count: int
    unstaged_path_count: int
    untracked_path_count: int
    deferred_path_count: int
    violation_count: int
    staged_paths: tuple[str, ...] = ()
    unstaged_paths: tuple[str, ...] = ()
    untracked_paths: tuple[str, ...] = ()
    deferred_paths: tuple[str, ...] = ()
    violations: tuple[dict[str, str], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = CONTRACT_ID
    command: str = COMMAND

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_publication_scope_integrity(
    *,
    repo_root: Path = REPO_ROOT,
    staged_paths: tuple[str, ...] | None = None,
    unstaged_paths: tuple[str, ...] | None = None,
    untracked_paths: tuple[str, ...] | None = None,
    deferral_receipt_path: Path | None = None,
) -> PublicationScopeIntegrityReport:
    warnings: list[str] = []
    if staged_paths is None:
        staged_paths, staged_warnings = _git_paths(
            repo_root,
            ("git", "diff", "--cached", "--name-only"),
            "staged_paths",
        )
        warnings.extend(staged_warnings)
    if unstaged_paths is None:
        unstaged_paths, unstaged_warnings = _git_paths(
            repo_root,
            ("git", "diff", "--name-only"),
            "unstaged_paths",
        )
        warnings.extend(unstaged_warnings)
    if untracked_paths is None:
        untracked_paths, untracked_warnings = _git_paths(
            repo_root,
            ("git", "ls-files", "--others", "--exclude-standard"),
            "untracked_paths",
        )
        warnings.extend(untracked_warnings)

    staged = _normalize_paths(staged_paths)
    unstaged = _normalize_paths(unstaged_paths)
    untracked = _normalize_paths(untracked_paths)
    deferred_paths, deferral_warnings = _load_deferral_receipt(deferral_receipt_path)
    warnings.extend(deferral_warnings)
    deferred = set(deferred_paths)

    violations: list[PublicationScopeIntegrityViolation] = []
    for path in unstaged:
        if path in deferred:
            continue
        reason = "unstaged_path_not_classified"
        detail = (
            "Tracked dirty path is outside the staged publication candidate and "
            "has no valid DirtyWorktreeDeferralReceipt."
        )
        violations.append(
            PublicationScopeIntegrityViolation(
                path=path,
                reason=reason,
                classification=_path_classification(path),
                detail=detail,
            )
        )

    for path in untracked:
        if path in deferred:
            continue
        reason = (
            "untracked_importable_python_path"
            if _is_importable_python_path(path)
            else "untracked_path_not_classified"
        )
        detail = (
            "Untracked path may make local validation pass without existing in "
            "the published tree."
        )
        violations.append(
            PublicationScopeIntegrityViolation(
                path=path,
                reason=reason,
                classification=_path_classification(path),
                detail=detail,
            )
        )

    return PublicationScopeIntegrityReport(
        ok=not violations and not warnings,
        staged_path_count=len(staged),
        unstaged_path_count=len(unstaged),
        untracked_path_count=len(untracked),
        deferred_path_count=len(deferred),
        violation_count=len(violations),
        staged_paths=staged,
        unstaged_paths=unstaged,
        untracked_paths=untracked,
        deferred_paths=tuple(sorted(deferred)),
        violations=tuple(violation.to_dict() for violation in violations),
        warnings=tuple(warnings),
    )


def render_markdown(report: PublicationScopeIntegrityReport) -> str:
    lines = ["# check_publication_scope_integrity", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- staged_path_count: {report.staged_path_count}")
    lines.append(f"- unstaged_path_count: {report.unstaged_path_count}")
    lines.append(f"- untracked_path_count: {report.untracked_path_count}")
    lines.append(f"- deferred_path_count: {report.deferred_path_count}")
    lines.append(f"- violation_count: {report.violation_count}")
    if report.violations:
        lines.extend(["", "## Violations"])
        for violation in report.violations:
            lines.append(
                f"- `{violation['path']}` {violation['reason']} "
                f"classification={violation['classification']}"
            )
    if report.warnings:
        lines.extend(["", "## Warnings"])
        for warning in report.warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines)


def _git_paths(
    repo_root: Path,
    command: tuple[str, ...],
    label: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    result = subprocess.run(
        command,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        return (), (f"{label}_unavailable:{detail}",)
    return _normalize_paths(result.stdout.splitlines()), ()


def _load_deferral_receipt(path: Path | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if path is None:
        return (), ()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (), (f"dirty_deferral_receipt_invalid:{exc.__class__.__name__}:{path}",)
    if not isinstance(payload, dict):
        return (), (f"dirty_deferral_receipt_not_object:{path}",)
    if payload.get("contract_id") != DEFERRAL_CONTRACT_ID:
        return (), (f"dirty_deferral_receipt_wrong_contract:{path}",)
    if payload.get("not_part_of_publication_candidate") is not True:
        return (), (f"dirty_deferral_receipt_missing_candidate_exclusion:{path}",)
    if payload.get("import_graph_checked") is not True:
        return (), (f"dirty_deferral_receipt_missing_import_graph_check:{path}",)
    return _normalize_paths(payload.get("deferred_paths") or ()), ()


def _normalize_paths(values: Any) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        values = (values,)
    result: list[str] = []
    seen: set[str] = set()
    try:
        iterator = iter(values)
    except TypeError:
        return ()
    for value in iterator:
        text = str(value or "").strip().lstrip("./")
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return tuple(result)


def _is_importable_python_path(path: str) -> bool:
    if not path.endswith(".py"):
        return False
    return path.startswith(("dev/scripts/", "scripts/", "app/", "rust/"))


def _path_classification(path: str) -> str:
    if path.startswith("dev/state/") or path.startswith("dev/reports/"):
        return "typed_state_or_receipt"
    if path in {"AGENTS.md", "CLAUDE.md", "bridge.md"} or path.startswith("dev/guides/"):
        return "generated_or_projection_surface"
    if _is_importable_python_path(path):
        return "importable_python"
    if path.startswith(".github/workflows/"):
        return "workflow"
    return "unclassified_dirty_path"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deferral-receipt", default="")
    parser.add_argument("--format", choices=("json", "md"), default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        report = evaluate_publication_scope_integrity(
            deferral_receipt_path=(
                Path(args.deferral_receipt) if args.deferral_receipt else None
            )
        )
    except Exception as exc:  # pragma: no cover - CLI safety net
        emit_runtime_error(COMMAND, exc, format=getattr(args, "format", "json"))
        return 2
    if args.format == "md":
        print(render_markdown(report))
    else:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
