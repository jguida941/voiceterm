"""Runtime checks for the startup-authority contract."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        import_repo_module,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        import_repo_module,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )

_detect_reviewer_gate = import_repo_module(
    "dev.scripts.devctl.runtime.startup_context",
    repo_root=REPO_ROOT,
)._detect_reviewer_gate
_derive_push_decision = import_repo_module(
    "dev.scripts.devctl.runtime.startup_push_decision",
    repo_root=REPO_ROOT,
).derive_push_decision

_REVIEW_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)
_DEVCTL_PUSH_EXECUTE_COMMAND = "python3 dev/scripts/devctl.py push --execute"
_VALID_PUSH_ACTIONS = {
    "await_checkpoint",
    "await_review",
    "run_devctl_push",
    "no_push_needed",
}


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


def collect_reviewer_loop_block_errors(repo_root: Path, gov) -> list[str]:
    """Return fail-closed errors when the active reviewer loop blocks implementation."""
    try:
        gate = _detect_reviewer_gate(repo_root, governance=gov)
    except AttributeError:
        gate = _detect_reviewer_gate(repo_root)
    if not gate.implementation_blocked:
        return []
    reason = gate.implementation_block_reason or "reviewer_loop_blocked"
    return [
        "Reviewer loop blocks a new implementation slice: "
        f"reviewer_mode={gate.reviewer_mode}, "
        f"review_accepted={gate.review_accepted}, "
        f"reason={reason}."
    ]


def collect_push_decision_contract_errors(repo_root: Path, gov) -> list[str]:
    """Return startup-contract errors when push next-step guidance is inconsistent."""
    try:
        gate = _detect_reviewer_gate(repo_root, governance=gov)
    except AttributeError:
        gate = _detect_reviewer_gate(repo_root)
    decision = _derive_push_decision(
        gov.push_enforcement,
        review_gate_allows_push=gate.review_gate_allows_push,
        implementation_blocked=gate.implementation_blocked,
        implementation_block_reason=gate.implementation_block_reason,
    )
    errors: list[str] = []

    if decision.action not in _VALID_PUSH_ACTIONS:
        errors.append(
            "Push decision contract emitted an unknown action: "
            f"{decision.action or '(empty)'}."
        )
        return errors

    if decision.action == "await_checkpoint":
        if decision.push_eligible_now:
            errors.append(
                "Push decision contract marked `await_checkpoint` as push-eligible."
            )
        if "checkpoint" not in decision.next_step_summary.lower():
            errors.append(
                "Push decision contract is missing checkpoint guidance for `await_checkpoint`."
            )
        return errors

    if decision.action == "await_review":
        if decision.push_eligible_now:
            errors.append(
                "Push decision contract marked `await_review` as push-eligible."
            )
        if decision.next_step_command != _REVIEW_STATUS_COMMAND:
            errors.append(
                "Push decision contract must point `await_review` to the canonical "
                "review-channel status command."
            )
        if "review" not in decision.next_step_summary.lower():
            errors.append(
                "Push decision contract is missing review guidance for `await_review`."
            )
        return errors

    if decision.action == "run_devctl_push":
        if not decision.push_eligible_now:
            errors.append(
                "Push decision contract emitted `run_devctl_push` without "
                "`push_eligible_now=true`."
            )
        if decision.next_step_command != _DEVCTL_PUSH_EXECUTE_COMMAND:
            errors.append(
                "Push decision contract must point `run_devctl_push` to the canonical "
                "`devctl push --execute` command."
            )
        if "governed push" not in decision.next_step_summary.lower():
            errors.append(
                "Push decision contract is missing governed-push guidance for "
                "`run_devctl_push`."
            )
        return errors

    if decision.push_eligible_now:
        errors.append("Push decision contract marked `no_push_needed` as push-eligible.")
    if not decision.next_step_summary:
        errors.append(
            "Push decision contract is missing operator guidance for `no_push_needed`."
        )
    if decision.next_step_command:
        errors.append(
            "Push decision contract should not emit a follow-up command for `no_push_needed`."
        )
    return errors


def collect_import_index_atomicity_findings(
    repo_root: Path,
) -> tuple[list[str], list[str]]:
    """Return repo-local import atomicity errors plus non-fatal warnings.

    Two layers of validation at their correct boundaries:

    - **Staged layer**: scan working-tree content of indexed/tracked files, check
      imports resolve in the staging area. Catches "exists on disk but
      never git-added."
    - **Committed layer**: scan HEAD content of committed files, check
      imports resolve in HEAD. Proves the committed tree itself is internally
      coherent.

    Each layer is self-contained: staged checks staged, committed checks
    committed. A legitimate atomic stage (importer + target both staged
    but not yet committed) passes the staged layer and the committed layer
    only checks what HEAD already contains.
    """
    staged_paths, staged_warning = _list_staged_python_paths(repo_root)
    committed_paths, committed_warning = _list_committed_python_paths(repo_root)
    warnings: list[str] = []
    if staged_warning:
        warnings.append(staged_warning)
    if committed_warning:
        warnings.append(committed_warning)

    target_roots = resolve_quality_scope_roots("python_guard", repo_root=repo_root)
    errors: list[str] = []

    # --- Staged layer: working-tree content vs index ---
    if staged_paths:
        staged_top_packages = {
            Path(p).parts[0] for p in staged_paths if Path(p).parts
        }
        for relative in sorted(staged_paths):
            importer = Path(relative)
            if not is_under_target_roots(importer, repo_root=repo_root, target_roots=target_roots):
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
                    repo_root=repo_root,
                    index_python_paths=staged_paths,
                    top_level_packages=staged_top_packages,
                    layer="staged",
                )
            )

    # --- Committed layer: HEAD content vs HEAD paths ---
    if committed_paths:
        committed_top_packages = {
            Path(p).parts[0] for p in committed_paths if Path(p).parts
        }
        for relative in sorted(committed_paths):
            importer = Path(relative)
            if not is_under_target_roots(importer, repo_root=repo_root, target_roots=target_roots):
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
                    repo_root=repo_root,
                    index_python_paths=committed_paths,
                    top_level_packages=committed_top_packages,
                    layer="committed",
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
    layer: str = "staged",
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
                    layer=layer,
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
                            layer=layer,
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
    layer: str = "staged",
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
            layer=layer,
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
        layer=layer,
    )


def _relative_import_errors(
    *,
    importer: Path,
    module_name: str,
    imported_names: list[str],
    level: int,
    repo_root: Path,
    index_python_paths: set[str],
    layer: str = "staged",
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
        layer=layer,
    )


def _module_and_alias_errors(
    *,
    importer: Path,
    import_ref: str,
    module_base: Path,
    imported_names: list[str],
    repo_root: Path,
    index_python_paths: set[str],
    layer: str = "staged",
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
                    layer=layer,
                )
            )
    if alias_checked or module_base == Path():
        return errors
    return _require_module_in_index(
        importer=importer,
        import_ref=import_ref,
        module_base=module_base,
        index_python_paths=index_python_paths,
        layer=layer,
    )


def _require_module_in_index(
    *,
    importer: Path,
    import_ref: str,
    module_base: Path,
    index_python_paths: set[str],
    layer: str = "staged",
) -> list[str]:
    candidates = _module_candidates(module_base)
    if any(candidate in index_python_paths for candidate in candidates):
        return []
    layer_label = "committed tree (HEAD)" if layer == "committed" else "git index (staged)"
    return [
        f"{importer.as_posix()}: `{import_ref}` resolves to module "
        f"candidates {', '.join(f'`{candidate}`' for candidate in candidates)} "
        f"missing from {layer_label}."
    ]


def _read_committed_file(
    repo_root: Path,
    relative: Path,
) -> tuple[str | None, str | None]:
    """Read a file's content from HEAD (the committed tree), not the working tree."""
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{relative.as_posix()}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, (
            f"{relative.as_posix()}: unable to read committed importer source ({exc})"
        )
    if result.returncode != 0:
        stderr = str(getattr(result, "stderr", "") or "").strip() or "git show HEAD:<path> failed"
        return None, (
            f"{relative.as_posix()}: unable to read committed importer source ({stderr})"
        )
    return result.stdout, None


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


def _list_staged_python_paths(repo_root: Path) -> tuple[set[str], str | None]:
    """Return Python paths present in the git index.

    Catches modules that exist on disk but were never git-added.
    """
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
        return set(), f"git index unavailable for import atomicity check ({exc})"
    if result.returncode != 0:
        stderr = str(getattr(result, "stderr", "") or "").strip() or "git ls-files failed"
        return set(), f"git index unavailable for import atomicity check ({stderr})"
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().endswith(".py")
    }, None


def _list_committed_python_paths(repo_root: Path) -> tuple[set[str], str | None]:
    """Return Python paths in the committed tree (HEAD), not the staging area.

    Fresh repos without a first commit should silently skip this layer.
    """
    try:
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return set(), f"git HEAD tree unavailable for import/index atomicity check ({exc})"
    if result.returncode != 0:
        stderr = str(getattr(result, "stderr", "") or "").strip() or "git ls-tree HEAD failed"
        if _head_missing(stderr):
            return set(), None
        return set(), f"git HEAD tree unavailable for import/index atomicity check ({stderr})"
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().endswith(".py")
    }, None


def _head_missing(stderr: str) -> bool:
    text = stderr.lower()
    return (
        "not a valid object name head" in text
        or "ambiguous argument 'head'" in text
        or "bad revision 'head'" in text
    )


def _render_import_from(module_name: str, imported_names: list[str]) -> str:
    names = ", ".join(imported_names) if imported_names else "*"
    if module_name:
        return f"from {module_name} import {names}"
    return f"from . import {names}"
