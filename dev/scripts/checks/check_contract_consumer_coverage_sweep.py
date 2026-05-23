#!/usr/bin/env python3
"""Find typed contract dataclasses without external writer and reader seams."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        utc_timestamp,
    )

try:
    from _git_status_helpers import path_from_git_status_line as _path_from_git_status_line
except ModuleNotFoundError:
    from dev.scripts.checks._git_status_helpers import (
        path_from_git_status_line as _path_from_git_status_line,
    )

try:
    from contract_connectivity.inventory_helpers import (
        has_dataclass_decorator as _has_dataclass_decorator,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.contract_connectivity.inventory_helpers import (
        has_dataclass_decorator as _has_dataclass_decorator,
    )


COMMAND = "check_contract_consumer_coverage_sweep"
CONTRACT_ID = "ContractConsumerCoverageSweepGuard"

REASON_NO_WRITER = "contract_without_external_writer"
REASON_NO_READER = "contract_without_external_reader"

DISPLAY_TEXT = (
    "AI DUMBASS ALERT: contract coverage gap. Typed contracts need external "
    "writer and reader seams before they can count as architecture."
)

CONTRACT_ROOTS = (
    "dev/scripts/devctl/runtime/",
    "dev/scripts/devctl/review_channel/",
    "dev/scripts/devctl/platform/",
)
REFERENCE_SCAN_ROOTS = ("dev/scripts",)
READER_CLASSMETHODS = frozenset(
    {
        "from_mapping",
        "from_dict",
        "from_json",
        "model_validate",
        "parse_obj",
        "read",
        "load",
    }
)
PRODUCER_CLASSMETHODS = frozenset({"from_values"})


@dataclass(frozen=True, slots=True)
class ContractDefinition:
    name: str
    module_name: str
    module_path: str

    @property
    def key(self) -> tuple[str, str]:
        return self.module_name, self.name

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "module_name": self.module_name,
            "module_path": self.module_path,
        }


@dataclass(frozen=True, slots=True)
class ContractCoverage:
    contract_name: str
    module_name: str
    module_path: str
    writer_refs: tuple[str, ...]
    reader_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["writer_refs"] = list(self.writer_refs)
        payload["reader_refs"] = list(self.reader_refs)
        return payload


@dataclass(frozen=True, slots=True)
class ContractConsumerCoverageViolation:
    contract_name: str
    module_path: str
    reason: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    scope: str = "changed",
    changed_paths: Sequence[str | Path] | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    candidate_paths = _candidate_paths_for_scope(
        repo_root=repo_root,
        scope=scope,
        changed_paths=changed_paths,
        warnings=warnings,
    )
    all_python_paths = _all_python_paths(repo_root)
    reference_modules = _parsed_reference_modules(
        repo_root=repo_root,
        paths=all_python_paths,
        warnings=warnings,
    )
    contracts = tuple(
        contract
        for path in candidate_paths
        for contract in _contract_definitions(repo_root=repo_root, path=path, warnings=warnings)
    )
    coverage_rows: list[ContractCoverage] = []
    violations: list[ContractConsumerCoverageViolation] = []
    for contract in contracts:
        coverage = _coverage_for_contract(
            contract=contract,
            repo_root=repo_root,
            reference_modules=reference_modules,
        )
        coverage_rows.append(coverage)
        violations.extend(_violations_for_coverage(coverage))

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "scope": scope,
        "contract_count": len(coverage_rows),
        "contracts": [row.to_dict() for row in coverage_rows],
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


def _candidate_paths_for_scope(
    *,
    repo_root: Path,
    scope: str,
    changed_paths: Sequence[str | Path] | None,
    warnings: list[str],
) -> tuple[Path, ...]:
    if scope == "all":
        return tuple(
            path
            for path in _all_python_paths(repo_root)
            if _is_contract_surface_path(path.as_posix())
        )
    if scope != "changed":
        warnings.append(f"unknown scope {scope!r}; defaulting to changed")
    paths = (
        tuple(Path(path) for path in changed_paths)
        if changed_paths is not None
        else _git_changed_paths(repo_root, warnings)
    )
    candidates: list[Path] = []
    for path in paths:
        rel = _relative_path(path, repo_root)
        if rel and _is_contract_surface_path(rel) and rel.endswith(".py"):
            candidates.append(Path(rel))
    return tuple(sorted(set(candidates)))


def _contract_definitions(
    *,
    repo_root: Path,
    path: Path,
    warnings: list[str],
) -> tuple[ContractDefinition, ...]:
    full_path = repo_root / path
    try:
        text = full_path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=path.as_posix())
    except (OSError, SyntaxError) as exc:
        warnings.append(f"could not parse {path.as_posix()}: {exc}")
        return ()
    module_name = _module_name_for_path(path)
    contracts: list[ContractDefinition] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not _has_dataclass_decorator(node):
            continue
        contracts.append(
            ContractDefinition(
                name=node.name,
                module_name=module_name,
                module_path=path.as_posix(),
            )
        )
    return tuple(contracts)


def _coverage_for_contract(
    *,
    contract: ContractDefinition,
    repo_root: Path,
    reference_modules: Sequence["_ParsedReferenceModule"],
) -> ContractCoverage:
    writer_refs: set[str] = set()
    reader_refs: set[str] = set()
    producer_symbols = _contract_producer_symbols(
        contract=contract,
        reference_modules=reference_modules,
    )
    for module in reference_modules:
        if module.path == contract.module_path or _is_test_path(module.path):
            continue
        aliases = _contract_aliases(module, contract)
        producer_aliases = _producer_aliases(module, contract, producer_symbols)
        if (
            not aliases.local_aliases
            and not aliases.module_aliases
            and not producer_aliases.local_aliases
            and not producer_aliases.module_aliases
        ):
            continue
        writers, readers = _references_in_tree(module.tree, aliases)
        producer_writers, producer_readers = _producer_references_in_tree(
            module.tree,
            producer_aliases,
        )
        writer_refs.update(f"{module.path}:{ref}" for ref in writers)
        writer_refs.update(f"{module.path}:{ref}" for ref in producer_writers)
        reader_refs.update(f"{module.path}:{ref}" for ref in readers)
        reader_refs.update(f"{module.path}:{ref}" for ref in producer_readers)
    return ContractCoverage(
        contract_name=contract.name,
        module_name=contract.module_name,
        module_path=contract.module_path,
        writer_refs=tuple(sorted(writer_refs)),
        reader_refs=tuple(sorted(reader_refs)),
    )


def _violations_for_coverage(
    coverage: ContractCoverage,
) -> tuple[ContractConsumerCoverageViolation, ...]:
    violations: list[ContractConsumerCoverageViolation] = []
    if not coverage.writer_refs:
        violations.append(
            ContractConsumerCoverageViolation(
                contract_name=coverage.contract_name,
                module_path=coverage.module_path,
                reason=REASON_NO_WRITER,
                detail="contract dataclass has no external constructor/writer reference",
                remediation="Add or name the canonical writer seam before relying on this contract.",
            )
        )
    if not coverage.reader_refs:
        violations.append(
            ContractConsumerCoverageViolation(
                contract_name=coverage.contract_name,
                module_path=coverage.module_path,
                reason=REASON_NO_READER,
                detail="contract dataclass has no external reader/consumer reference",
                remediation="Add or name the reader/consumer seam that validates or consumes this contract.",
            )
        )
    return tuple(violations)


@dataclass(frozen=True, slots=True)
class _ContractAliases:
    local_aliases: frozenset[str]
    module_aliases: frozenset[str]
    contract_name: str


@dataclass(frozen=True, slots=True)
class _ProducerAliases:
    local_aliases: Mapping[str, str]
    module_aliases: Mapping[str, frozenset[str]]
    contract_name: str


@dataclass(frozen=True, slots=True)
class _ProducerSymbol:
    module_name: str
    name: str


@dataclass(frozen=True, slots=True)
class _ParsedReferenceModule:
    path: str
    tree: ast.AST
    symbol_import_aliases: Mapping[tuple[str, str], frozenset[str]]
    module_import_aliases: Mapping[str, frozenset[str]]


def _parsed_reference_modules(
    *,
    repo_root: Path,
    paths: Sequence[Path],
    warnings: list[str],
) -> tuple[_ParsedReferenceModule, ...]:
    modules: list[_ParsedReferenceModule] = []
    for path in paths:
        if _is_test_path(path.as_posix()):
            continue
        try:
            tree = ast.parse(
                (repo_root / path).read_text(encoding="utf-8"),
                filename=path.as_posix(),
            )
        except (OSError, SyntaxError) as exc:
            warnings.append(f"could not parse {path.as_posix()}: {exc}")
            continue
        modules.append(
            _ParsedReferenceModule(
                path=path.as_posix(),
                tree=tree,
                symbol_import_aliases=_symbol_import_aliases(
                    tree,
                    module_name=_module_name_for_path(path),
                ),
                module_import_aliases=_module_import_aliases(tree),
            )
        )
    return tuple(modules)


def _symbol_import_aliases(
    tree: ast.AST,
    *,
    module_name: str,
) -> Mapping[tuple[str, str], frozenset[str]]:
    aliases: dict[tuple[str, str], set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            source_module = _resolve_import_from_module(
                module_name=module_name,
                import_module=node.module,
                level=node.level,
            )
            if not source_module:
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                aliases.setdefault((source_module, alias.name), set()).add(
                    alias.asname or alias.name
                )
    return {
        key: frozenset(values)
        for key, values in aliases.items()
    }


def _resolve_import_from_module(
    *,
    module_name: str,
    import_module: str | None,
    level: int,
) -> str:
    if level <= 0:
        return import_module or ""
    parts = module_name.split(".")
    base = parts[: max(0, len(parts) - level)]
    if import_module:
        base.extend(import_module.split("."))
    return ".".join(base)


def _module_import_aliases(tree: ast.AST) -> Mapping[str, frozenset[str]]:
    aliases: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases.setdefault(alias.name, set()).add(
                    alias.asname or alias.name.split(".")[-1]
                )
    return {
        key: frozenset(values)
        for key, values in aliases.items()
    }


def _contract_aliases(
    module: _ParsedReferenceModule,
    contract: ContractDefinition,
) -> _ContractAliases:
    return _ContractAliases(
        local_aliases=module.symbol_import_aliases.get(
            (contract.module_name, contract.name),
            frozenset(),
        ),
        module_aliases=module.module_import_aliases.get(
            contract.module_name,
            frozenset(),
        ),
        contract_name=contract.name,
    )


def _producer_aliases(
    module: _ParsedReferenceModule,
    contract: ContractDefinition,
    producer_symbols: frozenset[_ProducerSymbol],
) -> _ProducerAliases:
    local_aliases: dict[str, str] = {}
    module_aliases: dict[str, set[str]] = {}
    for producer in producer_symbols:
        for alias in module.symbol_import_aliases.get(
            (producer.module_name, producer.name),
            frozenset(),
        ):
            local_aliases[alias] = producer.name
        for module_alias in module.module_import_aliases.get(
            producer.module_name,
            frozenset(),
        ):
            module_aliases.setdefault(module_alias, set()).add(producer.name)
    return _ProducerAliases(
        local_aliases=local_aliases,
        module_aliases={
            alias: frozenset(names)
            for alias, names in module_aliases.items()
        },
        contract_name=contract.name,
    )


def _contract_producer_symbols(
    *,
    contract: ContractDefinition,
    reference_modules: Sequence[_ParsedReferenceModule],
) -> frozenset[_ProducerSymbol]:
    symbols: set[_ProducerSymbol] = set()
    for module in reference_modules:
        if _is_test_path(module.path):
            continue
        module_name = _module_name_for_path(Path(module.path))
        aliases = _producer_contract_aliases(module, contract)
        if not aliases.local_aliases and not aliases.module_aliases:
            continue
        functions = {
            node.name: node
            for node in ast.walk(module.tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        producers: set[str] = set()
        for name, node in functions.items():
            if _function_produces_contract(node, aliases):
                producers.add(name)

        changed = True
        while changed:
            changed = False
            for name, node in functions.items():
                if name in producers:
                    continue
                if _function_calls_any(node, producers):
                    producers.add(name)
                    changed = True
        symbols.update(
            _ProducerSymbol(module_name=module_name, name=name)
            for name in producers
        )
    return frozenset(symbols)


def _producer_contract_aliases(
    module: _ParsedReferenceModule,
    contract: ContractDefinition,
) -> _ContractAliases:
    aliases = _contract_aliases(module, contract)
    if module.path != contract.module_path:
        return aliases
    return _ContractAliases(
        local_aliases=frozenset({*aliases.local_aliases, contract.name}),
        module_aliases=aliases.module_aliases,
        contract_name=contract.name,
    )


def _function_produces_contract(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    aliases: _ContractAliases,
) -> bool:
    if _annotation_references_contract(node.returns, aliases):
        return True
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        if _call_constructs_contract(candidate, aliases):
            return True
        if _call_builds_contract(candidate, aliases):
            return True
        if _call_uses_contract_as_factory_argument(candidate, aliases):
            return True
    return False


def _function_calls_any(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    function_names: set[str],
) -> bool:
    if not function_names:
        return False
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        func = candidate.func
        if isinstance(func, ast.Name) and func.id in function_names:
            return True
    return False


def _references_in_tree(
    tree: ast.AST,
    aliases: _ContractAliases,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    writers: set[str] = set()
    readers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if _call_constructs_contract(node, aliases):
                writers.add(aliases.contract_name)
            builder_ref = _call_builds_contract(node, aliases)
            if builder_ref:
                writers.add(builder_ref)
                readers.add(builder_ref)
            factory_ref = _call_uses_contract_as_factory_argument(node, aliases)
            if factory_ref:
                writers.add(factory_ref)
                readers.add(factory_ref)
            reader_ref = _call_reads_contract(node, aliases)
            if reader_ref:
                readers.add(reader_ref)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _annotation_references_contract(node.returns, aliases):
                writers.add(f"return_annotation:{aliases.contract_name}")
            if _function_args_reference_contract(node, aliases):
                readers.add(f"argument_annotation:{aliases.contract_name}")
        if isinstance(node, ast.AnnAssign) and _annotation_references_contract(
            node.annotation,
            aliases,
        ):
            readers.add(f"variable_annotation:{aliases.contract_name}")
    return tuple(sorted(writers)), tuple(sorted(readers))


def _producer_references_in_tree(
    tree: ast.AST,
    aliases: _ProducerAliases,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    writers: set[str] = set()
    readers: set[str] = set()
    if not aliases.local_aliases and not aliases.module_aliases:
        return (), ()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        producer_ref = _call_references_producer(node, aliases)
        if not producer_ref:
            continue
        ref = f"producer:{producer_ref}->{aliases.contract_name}"
        writers.add(ref)
        readers.add(ref)
    return tuple(sorted(writers)), tuple(sorted(readers))


def _call_constructs_contract(node: ast.Call, aliases: _ContractAliases) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in aliases.local_aliases
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return func.value.id in aliases.module_aliases and func.attr == aliases.contract_name
    return False


def _call_builds_contract(node: ast.Call, aliases: _ContractAliases) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name) and func.value.id in aliases.local_aliases:
            if func.attr in PRODUCER_CLASSMETHODS:
                return f"{aliases.contract_name}.{func.attr}"
        if (
            isinstance(func.value, ast.Attribute)
            and isinstance(func.value.value, ast.Name)
            and func.value.value.id in aliases.module_aliases
            and func.value.attr == aliases.contract_name
            and func.attr in PRODUCER_CLASSMETHODS
        ):
            return f"{aliases.contract_name}.{func.attr}"
    return ""


def _call_uses_contract_as_factory_argument(
    node: ast.Call,
    aliases: _ContractAliases,
) -> str:
    func = node.func
    if isinstance(func, ast.Name) and func.id in {"isinstance", "issubclass"}:
        return ""
    if any(_expr_references_contract(arg, aliases) for arg in node.args):
        return f"factory_arg:{aliases.contract_name}"
    if any(
        keyword.value is not None
        and _expr_references_contract(keyword.value, aliases)
        for keyword in node.keywords
    ):
        return f"factory_arg:{aliases.contract_name}"
    return ""


def _call_references_producer(node: ast.Call, aliases: _ProducerAliases) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return aliases.local_aliases.get(func.id, "")
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        if func.attr in aliases.module_aliases.get(func.value.id, frozenset()):
            return func.attr
    return ""


def _call_reads_contract(node: ast.Call, aliases: _ContractAliases) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name) and func.value.id in aliases.local_aliases:
            if func.attr in READER_CLASSMETHODS:
                return f"{aliases.contract_name}.{func.attr}"
        if (
            isinstance(func.value, ast.Attribute)
            and isinstance(func.value.value, ast.Name)
            and func.value.value.id in aliases.module_aliases
            and func.value.attr == aliases.contract_name
            and func.attr in READER_CLASSMETHODS
        ):
            return f"{aliases.contract_name}.{func.attr}"
    if isinstance(func, ast.Name) and func.id == "isinstance" and len(node.args) >= 2:
        if _expr_references_contract(node.args[1], aliases):
            return f"isinstance:{aliases.contract_name}"
    return ""


def _function_args_reference_contract(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    aliases: _ContractAliases,
) -> bool:
    args = node.args
    annotations: list[ast.AST | None] = [
        arg.annotation
        for arg in (
            tuple(args.posonlyargs)
            + tuple(args.args)
            + tuple(args.kwonlyargs)
        )
    ]
    annotations.append(args.vararg.annotation if args.vararg else None)
    annotations.append(args.kwarg.annotation if args.kwarg else None)
    return any(_annotation_references_contract(annotation, aliases) for annotation in annotations)


def _annotation_references_contract(
    node: ast.AST | None,
    aliases: _ContractAliases,
) -> bool:
    if node is None:
        return False
    return _expr_references_contract(node, aliases)


def _expr_references_contract(node: ast.AST, aliases: _ContractAliases) -> bool:
    if isinstance(node, ast.Name):
        return node.id in aliases.local_aliases
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return node.value.id in aliases.module_aliases and node.attr == aliases.contract_name
    if isinstance(node, ast.Subscript):
        return _expr_references_contract(node.value, aliases) or _expr_references_contract(
            node.slice,
            aliases,
        )
    if isinstance(node, ast.BinOp):
        return _expr_references_contract(node.left, aliases) or _expr_references_contract(
            node.right,
            aliases,
        )
    if isinstance(node, ast.UnaryOp):
        return _expr_references_contract(node.operand, aliases)
    if isinstance(node, ast.Tuple):
        return any(_expr_references_contract(item, aliases) for item in node.elts)
    if isinstance(node, ast.List):
        return any(_expr_references_contract(item, aliases) for item in node.elts)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        try:
            parsed = ast.parse(node.value, mode="eval")
        except SyntaxError:
            return node.value in aliases.local_aliases or any(
                f"{alias}.{aliases.contract_name}" == node.value
                for alias in aliases.module_aliases
            )
        return _expr_references_contract(parsed.body, aliases)
    return False


def _all_python_paths(repo_root: Path) -> tuple[Path, ...]:
    paths: set[Path] = set()
    for root in REFERENCE_SCAN_ROOTS:
        scan_root = repo_root / root
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            paths.add(path.relative_to(repo_root))
    return tuple(sorted(paths))


def _git_changed_paths(repo_root: Path, warnings: list[str]) -> tuple[Path, ...]:
    result = subprocess.run(
        (
            "git",
            "status",
            "--short",
            "--untracked-files=all",
            "--",
            "dev/scripts/devctl/runtime",
            "dev/scripts/devctl/review_channel",
            "dev/scripts/devctl/platform",
        ),
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        warnings.append(f"git status failed: {result.stderr.strip()}")
        return ()
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        path_text = _path_from_git_status_line(line)
        if path_text:
            paths.append(Path(path_text))
    return tuple(paths)


def _relative_path(path: str | Path, repo_root: Path) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        return candidate.as_posix()
    try:
        return candidate.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return ""


def _is_contract_surface_path(path: str) -> bool:
    return any(path.startswith(root) for root in CONTRACT_ROOTS)


def _is_test_path(path: str) -> bool:
    parts = Path(path).parts
    return "tests" in parts or Path(path).name.startswith("test_")


def _module_name_for_path(path: Path) -> str:
    return ".".join(path.with_suffix("").parts)


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- scope: {report.get('scope')}")
    lines.append(f"- contract_count: {report.get('contract_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('module_path')}::{violation.get('contract_name')}: "
                f"{violation.get('reason')} ({violation.get('detail')})"
            )
    warnings = report.get("warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)) and warnings:
        lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("changed", "all"), default="changed")
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(scope=args.scope)
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
