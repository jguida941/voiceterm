"""Shared parsing and semantic helpers for contract-connectivity indexing."""

from __future__ import annotations

import ast
import re
from pathlib import Path

LAYER_ROOTS = {
    "runtime": Path("dev/scripts/devctl/runtime"),
    "governance": Path("dev/scripts/devctl/governance"),
    "platform": Path("dev/scripts/devctl/platform"),
    "operator_console": Path("app/operator_console"),
}
META_FIELDS = {"schema_version", "contract_id"}
GENERIC_FIELDS = {
    "agent_id",
    "authority",
    "category",
    "command",
    "description",
    "label",
    "name",
    "path",
    "role",
    "status",
    "summary",
}

FIELD_SEMANTIC_ALIASES = {
    "name": "identifier",
    "label": "identifier",
    "script_id": "identifier",
    "command_id": "identifier",
    "surface_id": "identifier",
    "contract_id": "identifier",
    "check_id": "identifier",
    "finding_id": "identifier",
    "path": "locator",
    "relative_path": "locator",
    "handler_module": "locator",
    "module_path": "locator",
    "module_name": "locator",
    "description": "description",
    "summary": "description",
    "status": "status",
    "category": "classification",
    "authority": "classification",
    "read_only": "access_mode",
    "bundle_name": "bundle",
    "recommended_bundle": "bundle",
    "preflight_command": "preflight_command",
    "preflight_commands": "preflight_command",
    "command": "command",
    "command_names": "command",
    "guard_ids": "guard",
    "applicable_guards": "guard",
    "probe_ids": "probe",
    "applicable_probes": "probe",
    "surface_ids": "surface",
    "contract_ids": "contract",
    "consumes_contracts": "contract",
    "plan_paths": "plan",
    "changed_paths": "changed_paths",
    "context_level": "context_level",
    "evidence": "evidence",
    "generated_at_utc": "generated_at",
    "languages": "languages",
}
FIELD_TOKEN_ALIASES = {
    "path": "locator",
    "paths": "locator",
    "module": "locator",
    "handler": "",
    "relative": "",
    "name": "identifier",
    "id": "identifier",
    "label": "identifier",
    "description": "description",
    "summary": "description",
    "status": "status",
    "category": "classification",
    "authority": "classification",
    "bundle": "bundle",
    "recommended": "",
    "preflight": "preflight",
    "command": "command",
    "commands": "command",
    "guard": "guard",
    "guards": "guard",
    "probe": "probe",
    "probes": "probe",
    "surface": "surface",
    "surfaces": "surface",
    "contract": "contract",
    "contracts": "contract",
    "plan": "plan",
    "plans": "plan",
    "language": "language",
    "languages": "language",
    "read": "access",
    "only": "access",
}
FIELD_TOKEN_NOISE = frozenset({"all", "at", "by", "for", "schema", "total", "utc", "version"})
PURPOSE_STOP_WORDS = frozenset({
    "a",
    "an",
    "and",
    "built",
    "by",
    "carries",
    "carry",
    "class",
    "classes",
    "consumer",
    "consumers",
    "contract",
    "contracts",
    "data",
    "dataclass",
    "dataclasses",
    "derived",
    "entry",
    "entries",
    "existing",
    "for",
    "from",
    "generated",
    "holds",
    "in",
    "is",
    "model",
    "models",
    "of",
    "one",
    "or",
    "payload",
    "primary",
    "registered",
    "report",
    "reports",
    "result",
    "results",
    "row",
    "rows",
    "runtime",
    "set",
    "snapshot",
    "snapshots",
    "state",
    "states",
    "static",
    "the",
    "to",
    "top",
    "typed",
    "with",
})
TOKEN_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z]|[0-9]|$)|[A-Z]?[a-z]+|[0-9]+")


def module_name_for_path(path: Path) -> str:
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def package_module_name(module_name: str, path: Path) -> str:
    if path.name == "__init__.py":
        return module_name
    return module_name.rpartition(".")[0]


def resolve_import_module(
    *,
    package_module: str,
    module: str | None,
    level: int,
) -> str:
    if level <= 0:
        return str(module or "").strip()
    package_parts = [part for part in package_module.split(".") if part]
    trim = max(level - 1, 0)
    if trim > len(package_parts):
        return ""
    base_parts = package_parts[: len(package_parts) - trim]
    if module:
        return ".".join((*base_parts, *module.split(".")))
    return ".".join(base_parts)


def has_dataclass_decorator(node: ast.ClassDef) -> bool:
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Name) and target.id == "dataclass":
            return True
        if isinstance(target, ast.Attribute) and target.attr == "dataclass":
            return True
    return False


def class_field_names(node: ast.ClassDef) -> list[str]:
    fields: list[str] = []
    for statement in node.body:
        if not isinstance(statement, ast.AnnAssign):
            continue
        if not isinstance(statement.target, ast.Name):
            continue
        if _is_classvar_annotation(statement.annotation):
            continue
        fields.append(statement.target.id)
    return fields


def interesting_fields(field_names: tuple[str, ...]) -> tuple[str, ...]:
    filtered = tuple(
        field
        for field in field_names
        if field not in META_FIELDS and field not in GENERIC_FIELDS
    )
    if filtered:
        return filtered
    return tuple(field for field in field_names if field not in META_FIELDS)


def semantic_fields(field_names: tuple[str, ...]) -> tuple[str, ...]:
    labels: list[str] = []
    for field_name in field_names:
        if field_name in META_FIELDS:
            continue
        label = _semantic_field_label(field_name)
        if label and label not in labels:
            labels.append(label)
    return tuple(labels)


def purpose_tokens(contract_name: str, docstring: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for token in (*_identifier_tokens(contract_name), *_text_tokens(docstring)):
        if token in PURPOSE_STOP_WORDS:
            continue
        if token not in tokens:
            tokens.append(token)
    return tuple(tokens)


def literal_string(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def is_test_path(path: Path) -> bool:
    normalized = f"/{path.as_posix()}/"
    name = path.name
    return "/tests/" in normalized or name.startswith("test_") or name.endswith(
        "_test.py"
    )


def layer_for_path(path: Path) -> str:
    normalized = path.as_posix()
    for layer, root in LAYER_ROOTS.items():
        if normalized.startswith(f"{root.as_posix()}/") or normalized == root.as_posix():
            return layer
    return ""


def _is_classvar_annotation(annotation: ast.AST) -> bool:
    if isinstance(annotation, ast.Name):
        return annotation.id == "ClassVar"
    if isinstance(annotation, ast.Subscript):
        return _is_classvar_annotation(annotation.value)
    if isinstance(annotation, ast.Attribute):
        return annotation.attr == "ClassVar"
    return False


def _semantic_field_label(field_name: str) -> str:
    alias = FIELD_SEMANTIC_ALIASES.get(field_name)
    if alias is not None:
        return alias

    tokens: list[str] = []
    for token in _identifier_tokens(field_name):
        mapped = FIELD_TOKEN_ALIASES.get(token, token)
        if not mapped or mapped in FIELD_TOKEN_NOISE:
            continue
        if mapped not in tokens:
            tokens.append(mapped)
    if tokens:
        return "_".join(tokens)
    return field_name


def _identifier_tokens(value: str) -> tuple[str, ...]:
    expanded = value.replace("_", " ")
    return tuple(
        token.lower()
        for part in expanded.split()
        for token in TOKEN_RE.findall(part)
        if token
    )


def _text_tokens(value: str) -> tuple[str, ...]:
    return tuple(
        token.lower()
        for token in TOKEN_RE.findall(value)
        if token
    )
