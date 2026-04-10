"""Source indexing for contract-connectivity analysis."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from dev.scripts.checks.rust_guard_common import GuardContext

LAYER_ROOTS = {
    "runtime": Path("dev/scripts/devctl/runtime"),
    "governance": Path("dev/scripts/devctl/governance"),
    "platform": Path("dev/scripts/devctl/platform"),
}
META_FIELDS = {"schema_version", "contract_id"}
GENERIC_FIELDS = {
    "authority",
    "category",
    "command",
    "description",
    "label",
    "name",
    "path",
    "status",
    "summary",
}
@dataclass(frozen=True, slots=True)
class ContractDefinition:
    contract_name: str
    layer: str
    module_name: str
    module_path: str
    field_names: tuple[str, ...]
    interesting_fields: tuple[str, ...]

    @property
    def key(self) -> tuple[str, str]:
        return (self.module_name, self.contract_name)
@dataclass(frozen=True, slots=True)
class ParsedModule:
    module_name: str
    module_path: str
    layer: str
    symbol_imports: tuple[tuple[str, str, str], ...]
    module_imports: tuple[tuple[str, str], ...]
    used_names: frozenset[str]
    used_attrs: frozenset[tuple[str, str]]
    raw_mapping_keys: frozenset[str]
    contracts: tuple[ContractDefinition, ...]
@dataclass(frozen=True, slots=True)
class SourceIndex:
    parsed_modules: tuple[ParsedModule, ...]
    contracts: tuple[ContractDefinition, ...]
    importers_by_contract: dict[tuple[str, str], tuple[ParsedModule, ...]]
    importer_paths_by_contract: dict[tuple[str, str], tuple[str, ...]]
def analyze_source(
    *,
    repo_root: Path,
    guard: GuardContext,
    ref: str | None,
) -> SourceIndex:
    """Build the parsed module and contract index for one git/tree state."""
    module_paths = _python_module_paths(repo_root=repo_root, guard=guard, ref=ref)
    module_registry = {
        _module_name_for_path(path): path
        for path in module_paths
        if not _is_test_path(path)
    }
    parsed_modules: list[ParsedModule] = []
    for path in module_paths:
        if _is_test_path(path):
            continue
        text = _read_text(guard=guard, path=path, ref=ref)
        if text is None:
            continue
        parsed_modules.append(
            _parse_module(
                path=path,
                text=text,
                module_registry=module_registry,
            )
        )

    contracts = tuple(
        contract
        for module in parsed_modules
        for contract in module.contracts
        if contract.layer
    )
    contract_lookup = {contract.key: contract for contract in contracts}
    importers_by_contract, importer_paths_by_contract = _importer_maps(
        parsed_modules=tuple(parsed_modules),
        contract_lookup=contract_lookup,
    )
    return SourceIndex(
        parsed_modules=tuple(parsed_modules),
        contracts=contracts,
        importers_by_contract=importers_by_contract,
        importer_paths_by_contract=importer_paths_by_contract,
    )
def contract_references(
    module: ParsedModule,
    contract_lookup: dict[tuple[str, str], ContractDefinition],
) -> set[tuple[str, str]]:
    """Resolve dataclass contracts explicitly imported and used by one module."""
    references: set[tuple[str, str]] = set()
    for local_name, source_module, imported_name in module.symbol_imports:
        key = (source_module, imported_name)
        if local_name in module.used_names and key in contract_lookup:
            references.add(key)
    for alias, source_module in module.module_imports:
        for local_name, attr_name in module.used_attrs:
            if local_name != alias:
                continue
            key = (source_module, attr_name)
            if key in contract_lookup:
                references.add(key)
    return references
def _python_module_paths(
    *,
    repo_root: Path,
    guard: GuardContext,
    ref: str | None,
) -> tuple[Path, ...]:
    paths: set[Path] = set()
    if ref is None:
        for line in guard.run_git(["git", "ls-files"]).stdout.splitlines():
            if line.strip().endswith(".py"):
                paths.add(Path(line.strip()))
        for line in guard.run_git(
            ["git", "ls-files", "--others", "--exclude-standard"]
        ).stdout.splitlines():
            if line.strip().endswith(".py"):
                paths.add(Path(line.strip()))
        return tuple(sorted(path for path in paths if (repo_root / path).exists()))

    result = guard.run_git(["git", "ls-tree", "-r", "--name-only", ref])
    for line in result.stdout.splitlines():
        if line.strip().endswith(".py"):
            paths.add(Path(line.strip()))
    return tuple(sorted(paths))
def _read_text(*, guard: GuardContext, path: Path, ref: str | None) -> str | None:
    if ref is None:
        return guard.read_text_from_worktree(path)
    return guard.read_text_from_ref(path, ref)
def _parse_module(
    *,
    path: Path,
    text: str,
    module_registry: dict[str, Path],
) -> ParsedModule:
    module_name = _module_name_for_path(path)
    tree = ast.parse(text, filename=path.as_posix())
    package_module = _package_module_name(module_name, path)
    symbol_imports: list[tuple[str, str, str]] = []
    module_imports: list[tuple[str, str]] = []
    used_names: set[str] = set()
    used_attrs: set[tuple[str, str]] = set()
    raw_mapping_keys: set[str] = set()
    contracts: list[ContractDefinition] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.split(".")[-1]
                module_imports.append((local_name, alias.name))
            continue
        if isinstance(node, ast.ImportFrom):
            resolved_module = _resolve_import_module(
                package_module=package_module,
                module=node.module,
                level=node.level,
            )
            if not resolved_module:
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                local_name = alias.asname or alias.name
                candidate_module = f"{resolved_module}.{alias.name}"
                if candidate_module in module_registry:
                    module_imports.append((local_name, candidate_module))
                else:
                    symbol_imports.append((local_name, resolved_module, alias.name))
            continue
        if isinstance(node, ast.Name):
            used_names.add(node.id)
            continue
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            used_attrs.add((node.value.id, node.attr))
            continue
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "get" and node.args:
                key = _literal_string(node.args[0])
                if key:
                    raw_mapping_keys.add(key)
            continue
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load):
            key = _literal_string(node.slice)
            if key:
                raw_mapping_keys.add(key)
            continue
        if isinstance(node, ast.ClassDef) and _has_dataclass_decorator(node):
            fields = tuple(_class_field_names(node))
            layer = _layer_for_path(path)
            contracts.append(
                ContractDefinition(
                    contract_name=node.name,
                    layer=layer,
                    module_name=module_name,
                    module_path=path.as_posix(),
                    field_names=fields,
                    interesting_fields=_interesting_fields(fields),
                )
            )

    return ParsedModule(
        module_name=module_name,
        module_path=path.as_posix(),
        layer=_layer_for_path(path),
        symbol_imports=tuple(symbol_imports),
        module_imports=tuple(module_imports),
        used_names=frozenset(used_names),
        used_attrs=frozenset(used_attrs),
        raw_mapping_keys=frozenset(raw_mapping_keys),
        contracts=tuple(contracts),
    )
def _importer_maps(
    *,
    parsed_modules: tuple[ParsedModule, ...],
    contract_lookup: dict[tuple[str, str], ContractDefinition],
) -> tuple[dict[tuple[str, str], tuple[ParsedModule, ...]], dict[tuple[str, str], tuple[str, ...]]]:
    importers: dict[tuple[str, str], list[ParsedModule]] = {
        key: [] for key in contract_lookup
    }
    importer_paths: dict[tuple[str, str], list[str]] = {
        key: [] for key in contract_lookup
    }
    for module in parsed_modules:
        for key in contract_references(module, contract_lookup):
            importers[key].append(module)
            importer_paths[key].append(module.module_path)
    return (
        {key: tuple(rows) for key, rows in importers.items()},
        {key: tuple(rows) for key, rows in importer_paths.items()},
    )
def _module_name_for_path(path: Path) -> str:
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)
def _package_module_name(module_name: str, path: Path) -> str:
    if path.name == "__init__.py":
        return module_name
    return module_name.rpartition(".")[0]
def _resolve_import_module(
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
def _has_dataclass_decorator(node: ast.ClassDef) -> bool:
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Name) and target.id == "dataclass":
            return True
        if isinstance(target, ast.Attribute) and target.attr == "dataclass":
            return True
    return False
def _class_field_names(node: ast.ClassDef) -> list[str]:
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
def _is_classvar_annotation(annotation: ast.AST) -> bool:
    if isinstance(annotation, ast.Name):
        return annotation.id == "ClassVar"
    if isinstance(annotation, ast.Subscript):
        return _is_classvar_annotation(annotation.value)
    if isinstance(annotation, ast.Attribute):
        return annotation.attr == "ClassVar"
    return False
def _interesting_fields(field_names: tuple[str, ...]) -> tuple[str, ...]:
    filtered = tuple(
        field
        for field in field_names
        if field not in META_FIELDS and field not in GENERIC_FIELDS
    )
    if filtered:
        return filtered
    return tuple(field for field in field_names if field not in META_FIELDS)
def _literal_string(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""
def _is_test_path(path: Path) -> bool:
    normalized = f"/{path.as_posix()}/"
    name = path.name
    return "/tests/" in normalized or name.startswith("test_") or name.endswith(
        "_test.py"
    )
def _layer_for_path(path: Path) -> str:
    normalized = path.as_posix()
    for layer, root in LAYER_ROOTS.items():
        if normalized.startswith(f"{root.as_posix()}/") or normalized == root.as_posix():
            return layer
    return ""
