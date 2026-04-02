"""Import/index atomicity checks for the startup-authority contract."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

try:
    from check_bootstrap import is_under_target_roots, resolve_quality_scope_roots
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        is_under_target_roots,
        resolve_quality_scope_roots,
    )

from .runtime_import_git import (
    _list_committed_python_paths,
    _list_staged_python_paths,
    _read_committed_file,
)


@dataclass(frozen=True)
class ImportAtomicityContext:
    repo_root: Path
    index_python_paths: set[str]
    top_level_packages: set[str]
    layer: str


def collect_import_index_atomicity_findings(
    repo_root: Path,
) -> tuple[list[str], list[str]]:
    """Return repo-local import atomicity errors plus non-fatal warnings."""
    staged_paths, staged_warning = _list_staged_python_paths(repo_root)
    committed_paths, committed_warning = _list_committed_python_paths(repo_root)
    warnings: list[str] = []
    if staged_warning:
        warnings.append(staged_warning)
    if committed_warning:
        warnings.append(committed_warning)

    target_roots = resolve_quality_scope_roots("python_guard", repo_root=repo_root)
    errors: list[str] = []

    if staged_paths:
        staged_top_packages = {Path(path).parts[0] for path in staged_paths if Path(path).parts}
        for relative in sorted(staged_paths):
            importer = Path(relative)
            if not is_under_target_roots(
                importer,
                repo_root=repo_root,
                target_roots=target_roots,
            ):
                continue
            importer_path = repo_root / importer
            if not importer_path.is_file():
                continue
            try:
                text = importer_path.read_text(encoding="utf-8")
                tree = ast.parse(text, filename=relative)
            except (OSError, SyntaxError) as exc:
                warnings.append(f"{relative}: skipped staged import scan ({exc})")
                continue
            errors.extend(
                _collect_file_atomicity_errors(
                    tree=tree,
                    importer=importer,
                    context=ImportAtomicityContext(
                        repo_root=repo_root,
                        index_python_paths=staged_paths,
                        top_level_packages=staged_top_packages,
                        layer="staged",
                    ),
                )
            )

    if committed_paths:
        committed_top_packages = {
            Path(path).parts[0] for path in committed_paths if Path(path).parts
        }
        for relative in sorted(committed_paths):
            importer = Path(relative)
            if not is_under_target_roots(
                importer,
                repo_root=repo_root,
                target_roots=target_roots,
            ):
                continue
            text, warning = _read_committed_file(repo_root, importer)
            if warning:
                warnings.append(warning)
                continue
            if text is None:
                continue
            try:
                tree = ast.parse(text, filename=f"HEAD:{relative}")
            except SyntaxError as exc:
                warnings.append(f"{relative}: skipped committed import scan ({exc})")
                continue
            errors.extend(
                _collect_file_atomicity_errors(
                    tree=tree,
                    importer=importer,
                    context=ImportAtomicityContext(
                        repo_root=repo_root,
                        index_python_paths=committed_paths,
                        top_level_packages=committed_top_packages,
                        layer="committed",
                    ),
                )
            )

    return sorted(set(errors)), warnings


def _collect_file_atomicity_errors(
    *,
    tree: ast.AST,
    importer: Path,
    context: ImportAtomicityContext,
) -> list[str]:
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            errors.extend(
                _import_from_errors(
                    node=node,
                    importer=importer,
                    context=context,
                )
            )
            continue
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = str(alias.name or "").strip()
                if not module_name:
                    continue
                if _absolute_module_in_repo(module_name, context.top_level_packages):
                    errors.extend(
                        _require_module_in_index(
                            importer=importer,
                            import_ref=f"import {module_name}",
                            module_base=Path(*module_name.split(".")),
                            context=context,
                        )
                    )
    return errors


def _import_from_errors(
    *,
    node: ast.ImportFrom,
    importer: Path,
    context: ImportAtomicityContext,
) -> list[str]:
    names = [
        str(alias.name or "").strip()
        for alias in node.names
        if str(alias.name or "").strip() and str(alias.name or "").strip() != "*"
    ]
    if node.level > 0:
        return _relative_import_errors(
            importer=importer,
            module_name=str(node.module or "").strip(),
            imported_names=names,
            level=node.level,
            context=context,
        )

    module_name = str(node.module or "").strip()
    if not _absolute_module_in_repo(module_name, context.top_level_packages):
        return []
    return _module_and_alias_errors(
        importer=importer,
        import_ref=_render_import_from(module_name, names),
        module_base=Path(*module_name.split(".")) if module_name else Path(),
        imported_names=names,
        context=context,
    )


def _relative_import_errors(
    *,
    importer: Path,
    module_name: str,
    imported_names: list[str],
    level: int,
    context: ImportAtomicityContext,
) -> list[str]:
    base_dir = importer.parent
    for _ in range(max(level - 1, 0)):
        if base_dir == Path("."):
            return []
        base_dir = base_dir.parent
    module_base = base_dir.joinpath(*module_name.split(".")) if module_name else Path()
    return _module_and_alias_errors(
        importer=importer,
        import_ref=_render_import_from(("." * level) + module_name, imported_names),
        module_base=module_base,
        imported_names=imported_names,
        context=context,
    )


def _module_and_alias_errors(
    *,
    importer: Path,
    import_ref: str,
    module_base: Path,
    imported_names: list[str],
    context: ImportAtomicityContext,
) -> list[str]:
    errors: list[str] = []
    alias_checked = False
    alias_base_root = module_base if module_base != Path() else importer.parent
    for name in imported_names:
        alias_base = alias_base_root / name
        if _module_exists_on_disk_or_index(
            alias_base,
            context=context,
        ):
            alias_checked = True
            errors.extend(
                _require_module_in_index(
                    importer=importer,
                    import_ref=import_ref,
                    module_base=alias_base,
                    context=context,
                )
            )
    if alias_checked or module_base == Path():
        return errors
    return _require_module_in_index(
        importer=importer,
        import_ref=import_ref,
        module_base=module_base,
        context=context,
    )


def _require_module_in_index(
    *,
    importer: Path,
    import_ref: str,
    module_base: Path,
    context: ImportAtomicityContext,
) -> list[str]:
    candidates = _module_candidates(module_base)
    if any(candidate in context.index_python_paths for candidate in candidates):
        return []
    layer_label = (
        "committed tree (HEAD)"
        if context.layer == "committed"
        else "git index (staged)"
    )
    return [
        f"{importer.as_posix()}: `{import_ref}` resolves to module "
        f"candidates {', '.join(f'`{candidate}`' for candidate in candidates)} "
        f"missing from {layer_label}."
    ]


def _absolute_module_in_repo(module_name: str, top_level_packages: set[str]) -> bool:
    if not module_name:
        return False
    return module_name.split(".", 1)[0] in top_level_packages


def _module_exists_on_disk_or_index(
    module_base: Path,
    *,
    context: ImportAtomicityContext,
) -> bool:
    for candidate in _module_candidates(module_base):
        if candidate in context.index_python_paths:
            return True
        if (context.repo_root / candidate).is_file():
            return True
    return False


def _module_candidates(module_base: Path) -> tuple[str, str]:
    file_candidate = module_base.with_suffix(".py").as_posix()
    package_candidate = (module_base / "__init__.py").as_posix()
    return file_candidate, package_candidate


def _render_import_from(module_name: str, imported_names: list[str]) -> str:
    names = ", ".join(imported_names) if imported_names else "*"
    if module_name:
        return f"from {module_name} import {names}"
    return f"from . import {names}"
