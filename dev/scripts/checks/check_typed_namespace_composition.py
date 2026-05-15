#!/usr/bin/env python3
"""Require typed namespace files to compose with their canonical authority."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


COMMAND = "check_typed_namespace_composition"
TYPED_NAMESPACE_COMPOSITION_GUARD_ID = "TypedNamespaceComposition"
TYPED_NAMESPACE_COMPOSITION_CONTRACT_ID = "TypedNamespaceCompositionGuard"
NON_COMPOSITION_RATIONALE_MARKER = "typed-namespace-non-composition-rationale:"


@dataclass(frozen=True, slots=True)
class TypedNamespaceRule:
    family_id: str
    glob_pattern: str
    canonical_path: str
    canonical_import_module: str


DEFAULT_RULES: tuple[TypedNamespaceRule, ...] = (
    TypedNamespaceRule(
        family_id="session_liveness",
        glob_pattern="dev/scripts/devctl/runtime/session_liveness_*.py",
        canonical_path="dev/scripts/devctl/runtime/session_liveness_signal.py",
        canonical_import_module="session_liveness_signal",
    ),
    TypedNamespaceRule(
        family_id="bypass_lifecycle",
        glob_pattern="dev/scripts/devctl/runtime/bypass_lifecycle_*.py",
        canonical_path="dev/scripts/devctl/runtime/bypass_lifecycle_models.py",
        canonical_import_module="bypass_lifecycle_models",
    ),
)


@dataclass(frozen=True, slots=True)
class TypedNamespaceCompositionGuard:
    """Registry-facing contract for typed namespace composition checks."""

    guard_id: str
    ok: bool
    report_only: bool
    would_fail: bool
    scanned_file_count: int = 0
    canonical_file_count: int = 0
    composed_file_count: int = 0
    rationale_file_count: int = 0
    violation_count: int = 0
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    schema_version: int = 1
    contract_id: str = TYPED_NAMESPACE_COMPOSITION_CONTRACT_ID
    command: str = COMMAND


@dataclass(frozen=True)
class TypedNamespaceViolation:
    path: str
    family_id: str
    canonical_path: str
    canonical_import_module: str
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FileComposition:
    path: str
    family_id: str
    canonical: bool
    imports_canonical: bool
    has_non_composition_rationale: bool


def evaluate_typed_namespace_composition(
    *,
    repo_root: Path = REPO_ROOT,
    rules: tuple[TypedNamespaceRule, ...] = DEFAULT_RULES,
) -> TypedNamespaceCompositionGuard:
    files: list[FileComposition] = []
    violations: list[TypedNamespaceViolation] = []
    errors: list[str] = []
    for rule in rules:
        for path in _rule_paths(repo_root=repo_root, rule=rule):
            composition, error = _file_composition(
                path=path,
                repo_root=repo_root,
                rule=rule,
            )
            if error:
                errors.append(error)
                continue
            if composition is None:
                continue
            files.append(composition)
            if (
                composition.canonical
                or composition.imports_canonical
                or composition.has_non_composition_rationale
            ):
                continue
            violations.append(
                TypedNamespaceViolation(
                    path=composition.path,
                    family_id=rule.family_id,
                    canonical_path=rule.canonical_path,
                    canonical_import_module=rule.canonical_import_module,
                    detail=(
                        "Typed namespace authority files must import their "
                        "canonical authority module or document an explicit "
                        f"{NON_COMPOSITION_RATIONALE_MARKER} marker."
                    ),
                )
            )

    ok = not violations and not errors
    return TypedNamespaceCompositionGuard(
        guard_id=TYPED_NAMESPACE_COMPOSITION_GUARD_ID,
        ok=ok,
        report_only=False,
        would_fail=not ok,
        scanned_file_count=len(files),
        canonical_file_count=sum(1 for file in files if file.canonical),
        composed_file_count=sum(1 for file in files if file.imports_canonical),
        rationale_file_count=sum(
            1 for file in files if file.has_non_composition_rationale
        ),
        violation_count=len(violations),
        violations=tuple(violation.to_dict() for violation in violations),
        errors=tuple(errors),
    )


def _rule_paths(*, repo_root: Path, rule: TypedNamespaceRule) -> tuple[Path, ...]:
    return tuple(sorted(path for path in repo_root.glob(rule.glob_pattern) if path.is_file()))


def _file_composition(
    *,
    path: Path,
    repo_root: Path,
    rule: TypedNamespaceRule,
) -> tuple[FileComposition | None, str]:
    relative = _display_path(path, repo_root=repo_root)
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=relative)
    except OSError as exc:
        return None, f"read-failed:{relative}:{exc.__class__.__name__}"
    except SyntaxError as exc:
        return None, f"parse-failed:{relative}:{exc.lineno}:{exc.msg}"
    return (
        FileComposition(
            path=relative,
            family_id=rule.family_id,
            canonical=relative == rule.canonical_path,
            imports_canonical=_imports_module(tree, rule.canonical_import_module),
            has_non_composition_rationale=NON_COMPOSITION_RATIONALE_MARKER in text,
        ),
        "",
    )


def _imports_module(tree: ast.AST, module_name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[-1] == module_name for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            imported_module = node.module or ""
            if imported_module.split(".")[-1] == module_name:
                return True
    return False


def _display_path(path: Path, *, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _render_md(report: TypedNamespaceCompositionGuard) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- report_only: {report.report_only}")
    lines.append(f"- would_fail: {report.would_fail}")
    lines.append(f"- scanned_file_count: {report.scanned_file_count}")
    lines.append(f"- canonical_file_count: {report.canonical_file_count}")
    lines.append(f"- composed_file_count: {report.composed_file_count}")
    lines.append(f"- rationale_file_count: {report.rationale_file_count}")
    lines.append(f"- violation_count: {report.violation_count}")
    if report.errors:
        lines.append("")
        lines.append("## Errors")
        lines.extend(f"- {error}" for error in report.errors)
    if report.violations:
        lines.append("")
        lines.append("## Violations")
        for violation in report.violations:
            if not isinstance(violation, dict):
                continue
            lines.append(
                "- "
                f"`{violation.get('path')}` "
                f"[{violation.get('family_id')}]: "
                f"{violation.get('detail')}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = evaluate_typed_namespace_composition()
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print(_render_md(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
