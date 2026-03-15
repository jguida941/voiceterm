"""Repo-visible reference scanning for compatibility-shim lifecycle hints."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

if __package__:
    from .bootstrap import import_attr
    from .probe_compatibility_rules import PublicShimContract, ShimFinding
else:  # pragma: no cover - standalone script fallback
    from bootstrap import import_attr
    from probe_compatibility_rules import PublicShimContract, ShimFinding

canonical_module_name = import_attr(
    "python_analysis.cyclic_imports_graph",
    "canonical_module_name",
)
resolve_relative_module = import_attr(
    "python_analysis.cyclic_imports_graph",
    "resolve_relative_module",
)

DEFAULT_EXCLUDED_PARTS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "target",
        "venv",
    }
)
TEXT_REFERENCE_SUFFIXES = frozenset(
    {".cfg", ".ini", ".json", ".jsonl", ".md", ".py", ".rst", ".sh", ".toml", ".txt", ".yaml", ".yml"}
)
TEXT_REFERENCE_FILENAMES = frozenset({"AGENTS.md", "Dockerfile", "Makefile", "README.md"})


@dataclass(frozen=True)
class ShimReference:
    source_path: Path
    kind: str
    matched_text: str


@dataclass(frozen=True)
class ShimLifecycle:
    finding: ShimFinding
    public_contract: PublicShimContract | None
    references: tuple[ShimReference, ...]

    @property
    def is_public(self) -> bool:
        return self.public_contract is not None

    @property
    def has_repo_references(self) -> bool:
        return bool(self.references)


@dataclass(frozen=True)
class RepoReferenceCorpus:
    python_imports: dict[Path, tuple[str, ...]]
    text_by_path: dict[Path, str]


def match_public_contract(
    relative_path: Path,
    public_contracts: tuple[PublicShimContract, ...],
) -> PublicShimContract | None:
    for contract in public_contracts:
        if contract.matches(relative_path):
            return contract
    return None


def _is_excluded(relative_path: Path, *, exclude_roots: tuple[Path, ...]) -> bool:
    if any(part in DEFAULT_EXCLUDED_PARTS for part in relative_path.parts):
        return True
    return any(relative_path == root or root in relative_path.parents for root in exclude_roots)


def _is_text_reference_path(relative_path: Path) -> bool:
    return relative_path.name in TEXT_REFERENCE_FILENAMES or relative_path.suffix in TEXT_REFERENCE_SUFFIXES


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _collect_python_imports(relative_path: Path, text: str) -> tuple[str, ...]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ()
    current_module = canonical_module_name(relative_path)
    current_is_package = relative_path.name == "__init__.py"
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names if alias.name)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        base_module = (
            resolve_relative_module(
                current_module=current_module,
                current_is_package=current_is_package,
                level=node.level,
                module=node.module,
            )
            if node.level
            else node.module
        )
        if not base_module:
            continue
        modules.add(base_module)
        modules.update(
            f"{base_module}.{alias.name}"
            for alias in node.names
            if alias.name and alias.name != "*"
        )
    return tuple(sorted(modules))


def build_reference_corpus(
    repo_root: Path,
    *,
    exclude_roots: tuple[Path, ...],
) -> RepoReferenceCorpus:
    python_imports: dict[Path, tuple[str, ...]] = {}
    text_by_path: dict[Path, str] = {}
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(repo_root)
        if _is_excluded(relative_path, exclude_roots=exclude_roots):
            continue
        if not _is_text_reference_path(relative_path):
            continue
        text = _read_text(path)
        if text is None:
            continue
        text_by_path[relative_path] = text
        if relative_path.suffix == ".py":
            python_imports[relative_path] = _collect_python_imports(relative_path, text)
    return RepoReferenceCorpus(python_imports=python_imports, text_by_path=text_by_path)


def _module_tokens(relative_path: Path) -> tuple[str, ...]:
    module_name = canonical_module_name(relative_path)
    return (module_name,) if module_name else ()


def _match_python_imports(
    finding: ShimFinding,
    corpus: RepoReferenceCorpus,
) -> list[ShimReference]:
    matched: list[ShimReference] = []
    module_tokens = _module_tokens(finding.relative_path)
    if not module_tokens:
        return matched
    for source_path, modules in corpus.python_imports.items():
        if source_path == finding.relative_path:
            continue
        for token in module_tokens:
            if any(module == token or module.startswith(f"{token}.") for module in modules):
                matched.append(
                    ShimReference(
                        source_path=source_path,
                        kind="python-import",
                        matched_text=token,
                    )
                )
                break
    return matched


def _match_text_references(
    finding: ShimFinding,
    corpus: RepoReferenceCorpus,
) -> list[ShimReference]:
    matched: list[ShimReference] = []
    path_token = finding.relative_path.as_posix()
    module_tokens = _module_tokens(finding.relative_path)
    for source_path, text in corpus.text_by_path.items():
        if source_path == finding.relative_path:
            continue
        if path_token in text:
            matched.append(
                ShimReference(
                    source_path=source_path,
                    kind="path-reference",
                    matched_text=path_token,
                )
            )
            continue
        if source_path.suffix == ".py":
            continue
        token = next((item for item in module_tokens if item and item in text), "")
        if token:
            matched.append(
                ShimReference(
                    source_path=source_path,
                    kind="text-reference",
                    matched_text=token,
                )
            )
    return matched


def classify_shim_lifecycle(
    repo_root: Path,
    findings: list[ShimFinding],
    *,
    public_contracts: tuple[PublicShimContract, ...],
    usage_scan_exclude_roots: tuple[Path, ...],
) -> tuple[ShimLifecycle, ...]:
    corpus = build_reference_corpus(
        repo_root,
        exclude_roots=usage_scan_exclude_roots,
    )
    lifecycle: list[ShimLifecycle] = []
    for finding in findings:
        public_contract = match_public_contract(
            finding.relative_path,
            public_contracts,
        )
        references: tuple[ShimReference, ...] = ()
        if public_contract is None:
            refs = _match_python_imports(finding, corpus)
            refs.extend(_match_text_references(finding, corpus))
            refs.sort(key=lambda ref: (ref.source_path.as_posix(), ref.kind, ref.matched_text))
            references = tuple(refs)
        lifecycle.append(
            ShimLifecycle(
                finding=finding,
                public_contract=public_contract,
                references=references,
            )
        )
    return tuple(lifecycle)


__all__ = [
    "PublicShimContract",
    "RepoReferenceCorpus",
    "ShimLifecycle",
    "ShimReference",
    "build_reference_corpus",
    "classify_shim_lifecycle",
    "match_public_contract",
]
