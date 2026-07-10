"""Internal helpers for bounded codeshape ingestion."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._codeshape_models import FunctionInfo, ModuleIndex


_MUTATING_GIT_VERBS = frozenset(
    {
        "add",
        "am",
        "apply",
        "branch",
        "checkout",
        "cherry-pick",
        "commit",
        "merge",
        "mv",
        "push",
        "rebase",
        "reset",
        "restore",
        "revert",
        "rm",
        "stash",
        "switch",
        "tag",
    }
)
_DYNAMIC_GIT_ATTR_VERBS = {"git_commit_args": "commit"}


def module_name_for_rel_path(rel_path: str) -> str:
    return rel_path.removesuffix(".py").replace("/", ".")


def module_name_to_rel_path(module_name: str, *, repo_root: Path) -> str | None:
    rel_path = module_name.replace(".", "/") + ".py"
    target = repo_root / rel_path
    return rel_path if target.is_file() else None


def resolve_import_target(
    current_module_name: str,
    *,
    level: int,
    module_name: str | None,
    repo_root: Path,
) -> str | None:
    if level:
        parts = current_module_name.split(".")[:-level]
    else:
        parts = []
    if module_name:
        if level:
            parts.extend(part for part in module_name.split(".") if part)
        else:
            parts = [part for part in module_name.split(".") if part]
    rel_path = "/".join(parts) + ".py"
    target = repo_root / rel_path
    return rel_path if target.is_file() else None


def resolve_call_target(
    func: ast.expr,
    *,
    module: "ModuleIndex",
    function: "FunctionInfo",
    instance_types: dict[str, str],
) -> str:
    if isinstance(func, ast.Name):
        local = module.top_level_by_name.get(func.id)
        if local is not None:
            return local.canonical_pointer_ref
        imported = module.imported_functions.get(func.id)
        if imported:
            return imported
        return ""

    if not isinstance(func, ast.Attribute):
        return ""

    if isinstance(func.value, ast.Name):
        base_name = func.value.id
        if base_name in {"self", "cls"} and function.class_name is not None:
            method = module.methods_by_name.get((function.class_name, func.attr))
            if method is not None:
                return method.canonical_pointer_ref
        module_rel = module.imported_modules.get(base_name)
        if module_rel is not None:
            return f"{module_rel}::{func.attr}"
        class_name = instance_types.get(base_name, "")
        class_rel = module.imported_classes.get(class_name)
        if class_rel is not None:
            return f"{class_rel}::{class_name}.{func.attr}"

    return ""


def mutation_candidate_for_call(
    node: ast.Call,
    *,
    rel_path: str,
    qualname: str,
    git_command_vars: dict[str, str],
) -> dict[str, str] | None:
    func_name = call_name(node.func)
    command_expr = mutation_command_expr(node, func_name)
    if command_expr is None:
        return None
    git_verb = git_verb_from_expr(command_expr, git_command_vars)
    if not git_verb:
        return None
    return {
        "path": rel_path,
        "qualname": qualname,
        "git_verb": git_verb,
        "command_source": func_name,
        "command_literal": safe_unparse(command_expr),
    }


def mutation_command_expr(node: ast.Call, func_name: str) -> ast.expr | None:
    if func_name == "run_git_capture":
        return node.args[0] if node.args else None
    if func_name in {"run_cmd", "run_cmd_fn", "command_runner", "repo_bound_runner"}:
        return node.args[1] if len(node.args) > 1 else None
    if func_name in {"subprocess.run", "subprocess.check_output", "run", "check_output"}:
        return node.args[0] if node.args else None
    return None


def git_verb_from_expr(expr: ast.expr, git_command_vars: dict[str, str]) -> str:
    if isinstance(expr, ast.Name):
        return git_command_vars.get(expr.id, "")
    if isinstance(expr, ast.List | ast.Tuple):
        return git_verb_from_sequence(expr.elts)
    if (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Name)
        and expr.func.id in {"list", "tuple"}
    ):
        if expr.args:
            return git_verb_from_expr(expr.args[0], git_command_vars)
        return ""
    if isinstance(expr, ast.Attribute):
        return _DYNAMIC_GIT_ATTR_VERBS.get(expr.attr, "")
    return ""


def git_verb_from_sequence(elements: list[ast.expr]) -> str:
    constants = [value for value in (string_literal(element) for element in elements) if value]
    if not constants:
        return ""
    if constants[0] == "git" and len(constants) > 1 and constants[1] in _MUTATING_GIT_VERBS:
        return constants[1]
    if constants[0] in _MUTATING_GIT_VERBS:
        return constants[0]
    return ""


def instance_alias_from_expr(expr: ast.expr) -> str:
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
        return expr.func.id
    if isinstance(expr, ast.BoolOp):
        for value in expr.values:
            alias = instance_alias_from_expr(value)
            if alias:
                return alias
    return ""


def call_name(func: ast.expr) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        base = call_name(func.value)
        return f"{base}.{func.attr}" if base else func.attr
    return ""


def string_literal(node: ast.expr) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def safe_unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - broad-except: allow reason=ast.unparse may fail on unsupported or partial nodes fallback=return placeholder text
        return "<unparseable>"
