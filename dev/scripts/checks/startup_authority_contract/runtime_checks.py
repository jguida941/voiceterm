"""Runtime checks for the startup-authority contract."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

try:
    from check_bootstrap import is_under_target_roots, resolve_quality_scope_roots
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        is_under_target_roots,
        resolve_quality_scope_roots,
    )


def collect_checkpoint_budget_errors(gov) -> list[str]:
    """Return fail-closed errors when the worktree is over the continuation budget."""
    push = gov.push_enforcement
    if push.checkpoint_required or not push.safe_to_continue_editing:
        return [
            "Startup authority is over budget: "
            f"checkpoint_required={push.checkpoint_required}, "
            f"safe_to_continue_editing={push.safe_to_continue_editing}, "
            f"reason={push.checkpoint_reason or 'worktree_budget_exceeded'}."
        ]
    return []


def collect_import_index_atomicity_findings(
    repo_root: Path,
) -> tuple[list[str], list[str]]:
    """Return repo-local import/index atomicity errors plus non-fatal warnings."""
    index_python_paths, git_warning = _list_index_python_paths(repo_root)
    warnings = [git_warning] if git_warning else []
    if not index_python_paths:
        return [], warnings

    target_roots = resolve_quality_scope_roots("python_guard", repo_root=repo_root)
    top_level_packages = {
        Path(path).parts[0] for path in index_python_paths if Path(path).parts
    }
    errors: list[str] = []

    for relative in sorted(index_python_paths):
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
            warnings.append(f"{relative}: skipped import/index atomicity scan ({exc})")
            continue
        errors.extend(
            _collect_file_atomicity_errors(
                tree=tree,
                importer=importer,
                repo_root=repo_root,
                index_python_paths=index_python_paths,
                top_level_packages=top_level_packages,
            )
        )

    return sorted(set(errors)), warnings


def _collect_file_atomicity_errors(
    *,
    tree: ast.AST,
    importer: Path,
    repo_root: Path,
    index_python_paths: set[str],
    top_level_packages: set[str],
) -> list[str]:
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            errors.extend(
                _import_from_errors(
                    node=node,
                    importer=importer,
                    repo_root=repo_root,
                    index_python_paths=index_python_paths,
                    top_level_packages=top_level_packages,
                )
            )
            continue
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = str(alias.name or "").strip()
                if not module_name:
                    continue
                if _absolute_module_in_repo(module_name, top_level_packages):
                    errors.extend(
                        _require_module_in_index(
                            importer=importer,
                            import_ref=f"import {module_name}",
                            module_base=Path(*module_name.split(".")),
                            index_python_paths=index_python_paths,
                        )
                    )
    return errors


def _import_from_errors(
    *,
    node: ast.ImportFrom,
    importer: Path,
    repo_root: Path,
    index_python_paths: set[str],
    top_level_packages: set[str],
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
            repo_root=repo_root,
            index_python_paths=index_python_paths,
        )

    module_name = str(node.module or "").strip()
    if not _absolute_module_in_repo(module_name, top_level_packages):
        return []
    return _module_and_alias_errors(
        importer=importer,
        import_ref=_render_import_from(module_name, names),
        module_base=Path(*module_name.split(".")) if module_name else Path(),
        imported_names=names,
        repo_root=repo_root,
        index_python_paths=index_python_paths,
    )


def _relative_import_errors(
    *,
    importer: Path,
    module_name: str,
    imported_names: list[str],
    level: int,
    repo_root: Path,
    index_python_paths: set[str],
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
        repo_root=repo_root,
        index_python_paths=index_python_paths,
    )


def _module_and_alias_errors(
    *,
    importer: Path,
    import_ref: str,
    module_base: Path,
    imported_names: list[str],
    repo_root: Path,
    index_python_paths: set[str],
) -> list[str]:
    errors: list[str] = []
    alias_checked = False
    alias_base_root = module_base if module_base != Path() else importer.parent
    for name in imported_names:
        alias_base = alias_base_root / name
        if _module_exists_on_disk_or_index(
            alias_base,
            repo_root=repo_root,
            index_python_paths=index_python_paths,
        ):
            alias_checked = True
            errors.extend(
                _require_module_in_index(
                    importer=importer,
                    import_ref=import_ref,
                    module_base=alias_base,
                    index_python_paths=index_python_paths,
                )
            )
    if alias_checked or module_base == Path():
        return errors
    return _require_module_in_index(
        importer=importer,
        import_ref=import_ref,
        module_base=module_base,
        index_python_paths=index_python_paths,
    )


def _require_module_in_index(
    *,
    importer: Path,
    import_ref: str,
    module_base: Path,
    index_python_paths: set[str],
) -> list[str]:
    candidates = _module_candidates(module_base)
    if any(candidate in index_python_paths for candidate in candidates):
        return []
    return [
        f"{importer.as_posix()}: `{import_ref}` resolves to worktree-only module "
        f"candidates {', '.join(f'`{candidate}`' for candidate in candidates)} "
        "that are missing from the git index."
    ]


def _absolute_module_in_repo(module_name: str, top_level_packages: set[str]) -> bool:
    if not module_name:
        return False
    return module_name.split(".", 1)[0] in top_level_packages


def _module_exists_on_disk_or_index(
    module_base: Path,
    *,
    repo_root: Path,
    index_python_paths: set[str],
) -> bool:
    for candidate in _module_candidates(module_base):
        if candidate in index_python_paths:
            return True
        if (repo_root / candidate).is_file():
            return True
    return False


def _module_candidates(module_base: Path) -> tuple[str, str]:
    file_candidate = module_base.with_suffix(".py").as_posix()
    package_candidate = (module_base / "__init__.py").as_posix()
    return file_candidate, package_candidate


def _list_index_python_paths(repo_root: Path) -> tuple[set[str], str | None]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--", "*.py"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return set(), f"git index unavailable for import/index atomicity check ({exc})"
    if result.returncode != 0:
        stderr = str(getattr(result, "stderr", "") or "").strip() or "git ls-files failed"
        return set(), f"git index unavailable for import/index atomicity check ({stderr})"
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().endswith(".py")
    }, None


def _render_import_from(module_name: str, imported_names: list[str]) -> str:
    names = ", ".join(imported_names) if imported_names else "*"
    if module_name:
        return f"from {module_name} import {names}"
    return f"from . import {names}"
