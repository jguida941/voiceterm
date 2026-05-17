"""AST scanner for typed enum connectivity."""

from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping
from pathlib import Path

from .models import EnumConsumer, EnumMember

DEFAULT_SCAN_ROOTS = (
    "dev/scripts/devctl",
    "dev/scripts/checks",
)
_EXCLUDED_DIR_NAMES = frozenset({"__pycache__", ".mypy_cache", ".pytest_cache"})


def scan_enum_connectivity(
    *,
    repo_root: Path,
    scan_roots: Iterable[str] = DEFAULT_SCAN_ROOTS,
    include_tests: bool = False,
) -> tuple[tuple[EnumMember, ...], tuple[EnumConsumer, ...]]:
    """Return discovered enum members and their decision-site consumers."""
    files = tuple(_iter_python_files(repo_root, scan_roots, include_tests=include_tests))
    members = tuple(_discover_enum_members(repo_root, files))
    consumers = tuple(_discover_consumers(repo_root, files, members))
    return members, consumers


def _iter_python_files(
    repo_root: Path,
    roots: Iterable[str],
    *,
    include_tests: bool,
) -> Iterable[Path]:
    for root in roots:
        scan_root = repo_root / root
        if not scan_root.exists():
            continue
        for path in sorted(scan_root.rglob("*.py")):
            parts = set(path.relative_to(repo_root).parts)
            if parts & _EXCLUDED_DIR_NAMES:
                continue
            if not include_tests and "tests" in parts:
                continue
            yield path


def _discover_enum_members(repo_root: Path, files: Iterable[Path]) -> list[EnumMember]:
    members: list[EnumMember] = []
    for path in files:
        tree = _parse_python(path)
        if tree is None:
            continue
        relpath = _relpath(repo_root, path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or not _is_enum_class(node):
                continue
            for child in node.body:
                member = _enum_member_from_assignment(
                    enum_name=node.name,
                    relpath=relpath,
                    node=child,
                )
                if member is not None:
                    members.append(member)
    return members


def _discover_consumers(
    repo_root: Path,
    files: Iterable[Path],
    members: tuple[EnumMember, ...],
) -> list[EnumConsumer]:
    by_enum_member = {member.key: member for member in members}
    by_value: dict[str, list[EnumMember]] = {}
    for member in members:
        by_value.setdefault(member.value, []).append(member)
    consumers: dict[tuple[str, str, str, int, str], EnumConsumer] = {}
    for path in files:
        tree = _parse_python(path)
        if tree is None:
            continue
        visitor = _EnumConsumerVisitor(
            relpath=_relpath(repo_root, path),
            by_enum_member=by_enum_member,
            by_value=by_value,
        )
        visitor.visit(tree)
        for consumer in visitor.consumers:
            consumers[
                (
                    consumer.enum_name,
                    consumer.member_name,
                    consumer.path,
                    consumer.line,
                    consumer.kind,
                )
            ] = consumer
    return sorted(
        consumers.values(),
        key=lambda item: (item.enum_name, item.member_name, item.path, item.line),
    )


class _EnumConsumerVisitor(ast.NodeVisitor):
    """AST visitor for decision-site enum use."""

    def __init__(
        self,
        *,
        relpath: str,
        by_enum_member: Mapping[tuple[str, str], EnumMember],
        by_value: Mapping[str, list[EnumMember]],
    ) -> None:
        self.relpath = relpath
        self.by_enum_member = by_enum_member
        self.by_value = by_value
        self.consumers: list[EnumConsumer] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> object:
        if _is_enum_class(node):
            return None
        return self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> object:
        self._record_enum_attr(node, kind="enum_reference")
        return self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> object:
        self._record_expression(node.left, kind="comparison")
        for comparator in node.comparators:
            self._record_expression(comparator, kind="comparison")
        return self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> object:
        for key in node.keys:
            if key is not None:
                self._record_expression(key, kind="dict_key")
        return self.generic_visit(node)

    def visit_MatchValue(self, node: ast.MatchValue) -> object:
        self._record_expression(node.value, kind="match_value")
        return self.generic_visit(node)

    def _record_expression(self, node: ast.AST, *, kind: str) -> None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            self._record_value(node.value, line=getattr(node, "lineno", 0), kind=kind)
            return
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            for element in node.elts:
                self._record_expression(element, kind=kind)
            return
        self._record_enum_attr(node, kind=kind)

    def _record_enum_attr(self, node: ast.AST, *, kind: str) -> None:
        reference = _enum_member_reference(node)
        if reference is None:
            return
        member = self.by_enum_member.get(reference)
        if member is None:
            return
        self.consumers.append(
            EnumConsumer(
                enum_name=member.enum_name,
                member_name=member.member_name,
                value=member.value,
                path=self.relpath,
                line=getattr(node, "lineno", 0),
                kind=kind,
            )
        )

    def _record_value(self, value: str, *, line: int, kind: str) -> None:
        for member in self.by_value.get(value, ()):
            self.consumers.append(
                EnumConsumer(
                    enum_name=member.enum_name,
                    member_name=member.member_name,
                    value=member.value,
                    path=self.relpath,
                    line=line,
                    kind=kind,
                )
            )


def _enum_member_from_assignment(
    *,
    enum_name: str,
    relpath: str,
    node: ast.stmt,
) -> EnumMember | None:
    target_name = ""
    value_node: ast.AST | None = None
    if isinstance(node, ast.Assign):
        first_target = node.targets[0] if node.targets else None
        if isinstance(first_target, ast.Name):
            target_name = first_target.id
            value_node = node.value
    elif isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            target_name = node.target.id
            value_node = node.value
    if not target_name or target_name.startswith("_") or value_node is None:
        return None
    if not isinstance(value_node, ast.Constant) or not isinstance(value_node.value, str):
        return None
    return EnumMember(
        enum_name=enum_name,
        member_name=target_name,
        value=value_node.value,
        path=relpath,
        line=getattr(node, "lineno", 0),
    )


def _enum_member_reference(node: ast.AST) -> tuple[str, str] | None:
    if isinstance(node, ast.Attribute):
        if node.attr == "value" and isinstance(node.value, ast.Attribute):
            node = node.value
        if isinstance(node.value, ast.Name):
            return (node.value.id, node.attr)
    return None


def _is_enum_class(node: ast.ClassDef) -> bool:
    base_names = {_base_name(base) for base in node.bases}
    return "Enum" in base_names or "StrEnum" in base_names


def _base_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return ""


def _parse_python(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None


def _relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)
