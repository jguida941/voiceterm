"""Bounded Python codeshape scanning over selected files."""

from __future__ import annotations

import ast
from pathlib import Path

from ..config import get_repo_root
from ._codeshape_emit import assemble_codeshape_graph
from ._codeshape_models import (
    CallRecord,
    CodeShapeGraph,
    FunctionInfo,
    ModuleIndex,
    MutationCandidate,
)
from ._codeshape_support import (
    git_verb_from_expr,
    instance_alias_from_expr,
    module_name_for_rel_path,
    module_name_to_rel_path,
    mutation_candidate_for_call,
    resolve_call_target,
    resolve_import_target,
)

DEFAULT_CODESHAPE_SCOPE_PATHS = (
    "dev/scripts/devctl/commands/vcs/governed_executor.py",
    "dev/scripts/devctl/commands/vcs/governed_executor_actions.py",
    "dev/scripts/devctl/commands/vcs/governed_executor_git.py",
    "dev/scripts/devctl/commands/vcs/governed_executor_phases.py",
    "dev/scripts/devctl/commands/vcs/governed_executor_support.py",
    "dev/scripts/devctl/commands/vcs/commit.py",
    "dev/scripts/devctl/commands/vcs/push.py",
    "dev/scripts/devctl/commands/vcs/push_flow.py",
    "dev/scripts/devctl/runtime/review_snapshot_refresh.py",
    "dev/scripts/devctl/runtime/vcs.py",
)


class FunctionBodyScanner(ast.NodeVisitor):
    """Collect call edges and mutation callsites inside one function body."""

    def __init__(self, module: ModuleIndex, function: FunctionInfo) -> None:
        self._module = module
        self._function = function
        self._git_command_vars: dict[str, str] = {}
        self._instance_types: dict[str, str] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # pragma: no cover - nested defs skipped
        return None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # pragma: no cover - nested defs skipped
        return None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # pragma: no cover - nested defs skipped
        return None

    def visit_Assign(self, node: ast.Assign) -> None:
        git_verb = git_verb_from_expr(node.value, self._git_command_vars)
        class_alias = instance_alias_from_expr(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                if git_verb:
                    self._git_command_vars[target.id] = git_verb
                if class_alias:
                    self._instance_types[target.id] = class_alias
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        value = node.value
        if value is None or not isinstance(node.target, ast.Name):
            self.generic_visit(node)
            return
        git_verb = git_verb_from_expr(value, self._git_command_vars)
        class_alias = instance_alias_from_expr(value)
        if git_verb:
            self._git_command_vars[node.target.id] = git_verb
        if class_alias:
            self._instance_types[node.target.id] = class_alias
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        mutation = mutation_candidate_for_call(
            node,
            rel_path=self._module.rel_path,
            qualname=self._function.qualname,
            git_command_vars=self._git_command_vars,
        )
        if mutation is not None:
            self._module.mutation_candidates.append(
                MutationCandidate(
                    caller_id=self._function.node_id,
                    rel_path=self._module.rel_path,
                    qualname=self._function.qualname,
                    line=node.lineno,
                    column=node.col_offset,
                    git_verb=mutation["git_verb"],
                    command_source=mutation["command_source"],
                    command_literal=mutation["command_literal"],
                )
            )

        target_pointer = resolve_call_target(
            node.func,
            module=self._module,
            function=self._function,
            instance_types=self._instance_types,
        )
        if target_pointer:
            self._module.call_records.append(
                CallRecord(
                    caller_id=self._function.node_id,
                    target_pointer_ref=target_pointer,
                )
            )
        self.generic_visit(node)


def build_codeshape_subgraph(
    *,
    repo_root: Path | None = None,
    scope_paths: tuple[str, ...] | None = None,
) -> CodeShapeGraph:
    """Return codeshape nodes/edges for a bounded governance-relevant scope."""
    effective_repo_root = (repo_root or get_repo_root()).resolve()
    resolved_scope = tuple(scope_paths or DEFAULT_CODESHAPE_SCOPE_PATHS)
    module_indexes: list[ModuleIndex] = []
    parse_errors: list[dict[str, str]] = []

    for rel_path in iter_scope_paths(effective_repo_root, resolved_scope):
        path = effective_repo_root / rel_path
        try:
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=rel_path)
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            parse_errors.append({"path": rel_path, "error": str(exc)})
            continue

        module = ModuleIndex(
            rel_path=rel_path,
            module_name=module_name_for_rel_path(rel_path),
        )
        collect_imports(module, tree, repo_root=effective_repo_root)
        collect_function_definitions(module, tree)
        collect_callsites(module, tree)
        module_indexes.append(module)

    return assemble_codeshape_graph(module_indexes, parse_errors=parse_errors)


def iter_scope_paths(repo_root: Path, scope_paths: tuple[str, ...]) -> tuple[str, ...]:
    resolved: set[str] = set()
    for raw in scope_paths:
        rel = str(raw).replace("\\", "/").strip().strip("/")
        if not rel:
            continue
        target = repo_root / rel
        if target.is_file() and target.suffix == ".py":
            resolved.add(rel)
            continue
        if target.is_dir():
            for path in target.rglob("*.py"):
                resolved.add(path.relative_to(repo_root).as_posix())
    return tuple(sorted(resolved))


def collect_imports(
    module: ModuleIndex,
    tree: ast.Module,
    *,
    repo_root: Path,
) -> None:
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            target_rel = resolve_import_target(
                module.module_name,
                level=node.level,
                module_name=node.module,
                repo_root=repo_root,
            )
            if target_rel is None:
                continue
            for alias in node.names:
                local_name = alias.asname or alias.name
                if alias.name[:1].isupper():
                    module.imported_classes[local_name] = target_rel
                else:
                    module.imported_functions[local_name] = f"{target_rel}::{alias.name}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                target_rel = module_name_to_rel_path(alias.name, repo_root=repo_root)
                if target_rel is not None:
                    module.imported_modules[
                        alias.asname or alias.name.rsplit(".", 1)[-1]
                    ] = target_rel


def collect_function_definitions(module: ModuleIndex, tree: ast.Module) -> None:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function = FunctionInfo(
                rel_path=module.rel_path,
                qualname=node.name,
                local_name=node.name,
                class_name=None,
                line=node.lineno,
            )
            module.functions.append(function)
            module.top_level_by_name[node.name] = function
            continue
        if not isinstance(node, ast.ClassDef):
            continue
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function = FunctionInfo(
                    rel_path=module.rel_path,
                    qualname=f"{node.name}.{child.name}",
                    local_name=child.name,
                    class_name=node.name,
                    line=child.lineno,
                )
                module.functions.append(function)
                module.methods_by_name[(node.name, child.name)] = function


def collect_callsites(module: ModuleIndex, tree: ast.Module) -> None:
    top_level_by_line = {
        function.line: function for function in module.functions if function.class_name is None
    }
    methods_by_line = {
        function.line: function for function in module.functions if function.class_name is not None
    }
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function = top_level_by_line.get(node.lineno)
            if function is None:
                continue
            scanner = FunctionBodyScanner(module, function)
            for child in node.body:
                scanner.visit(child)
            continue
        if not isinstance(node, ast.ClassDef):
            continue
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function = methods_by_line.get(child.lineno)
                if function is None:
                    continue
                scanner = FunctionBodyScanner(module, function)
                for grandchild in child.body:
                    scanner.visit(grandchild)
