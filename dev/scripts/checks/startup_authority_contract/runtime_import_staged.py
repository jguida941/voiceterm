"""Staged-tree import/index atomicity checks for governed commits."""

from __future__ import annotations

import ast
from pathlib import Path

try:
    from check_bootstrap import is_under_target_roots, resolve_quality_scope_roots
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        is_under_target_roots,
        resolve_quality_scope_roots,
    )

from .runtime_import_atomicity import (
    ImportAtomicityContext,
    ImportIndexAtomicityFinding,
    _collect_file_atomicity_finding_records,
    _dedupe_finding_records,
)
from .runtime_import_git import _list_staged_python_paths, _read_index_file


def collect_staged_import_index_atomicity_findings(
    repo_root: Path,
) -> tuple[list[str], list[str]]:
    """Return import atomicity errors for the staged git index only."""
    records, warnings = collect_staged_import_index_atomicity_finding_records(repo_root)
    return [record.to_message() for record in records], warnings


def collect_staged_import_index_atomicity_finding_records(
    repo_root: Path,
) -> tuple[list[ImportIndexAtomicityFinding], list[str]]:
    """Return structured import atomicity findings for the staged git index only."""
    staged_paths, staged_warning = _list_staged_python_paths(repo_root)
    warnings: list[str] = []
    if staged_warning:
        warnings.append(staged_warning)
    if not staged_paths:
        return [], warnings

    target_roots = resolve_quality_scope_roots("python_guard", repo_root=repo_root)
    context = _staged_context(repo_root=repo_root, staged_paths=staged_paths)
    records: list[ImportIndexAtomicityFinding] = []
    for relative in sorted(staged_paths):
        records.extend(
            _staged_importer_finding_records(
                repo_root=repo_root,
                relative=relative,
                target_roots=target_roots,
                context=context,
                warnings=warnings,
            )
        )
    return _dedupe_finding_records(records), warnings


def _staged_context(
    *,
    repo_root: Path,
    staged_paths: set[str],
) -> ImportAtomicityContext:
    return ImportAtomicityContext(
        repo_root=repo_root,
        index_python_paths=staged_paths,
        top_level_packages={
            Path(path).parts[0] for path in staged_paths if Path(path).parts
        },
        layer="staged",
        allow_disk_modules=False,
    )


def _staged_importer_errors(
    *,
    repo_root: Path,
    relative: str,
    target_roots: tuple[Path, ...],
    context: ImportAtomicityContext,
    warnings: list[str],
) -> list[str]:
    return [
        record.to_message()
        for record in _staged_importer_finding_records(
            repo_root=repo_root,
            relative=relative,
            target_roots=target_roots,
            context=context,
            warnings=warnings,
        )
    ]


def _staged_importer_finding_records(
    *,
    repo_root: Path,
    relative: str,
    target_roots: tuple[Path, ...],
    context: ImportAtomicityContext,
    warnings: list[str],
) -> list[ImportIndexAtomicityFinding]:
    importer = Path(relative)
    if not is_under_target_roots(
        importer,
        repo_root=repo_root,
        target_roots=target_roots,
    ):
        return []
    text, warning = _read_index_file(repo_root, importer)
    if warning:
        warnings.append(warning)
        return []
    if text is None:
        return []
    try:
        tree = ast.parse(text, filename=f":{relative}")
    except SyntaxError as exc:
        warnings.append(f"{relative}: skipped staged import scan ({exc})")
        return []
    return _collect_file_atomicity_finding_records(
        tree=tree,
        importer=importer,
        context=context,
    )
