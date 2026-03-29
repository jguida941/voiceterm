"""AST-based compatibility-shim validation helpers."""

from __future__ import annotations

import ast
from pathlib import Path
import re

if __package__:
    from .rule_models import CompatibilityShimValidation
else:  # pragma: no cover - standalone script fallback
    from rule_models import CompatibilityShimValidation

_SHIM_METADATA_PATTERN = re.compile(
    r"^(?:#\s*)?shim-(?P<key>[a-z0-9_-]+)\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE,
)
STANDARD_SHIM_METADATA_FIELDS = ("owner", "reason", "expiry", "target")


def _trim_module_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    if not body:
        return []
    first_stmt = body[0]
    if not isinstance(first_stmt, ast.Expr):
        return list(body)
    value = first_stmt.value
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        return list(body)
    return list(body[1:])


def _is_if_main_guard(stmt: ast.stmt) -> bool:
    if not isinstance(stmt, ast.If) or stmt.orelse or len(stmt.body) != 1:
        return False
    test = stmt.test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    if not isinstance(test.left, ast.Name) or test.left.id != "__name__":
        return False
    if not isinstance(test.ops[0], ast.Eq):
        return False
    comparator = test.comparators[0]
    if not isinstance(comparator, ast.Constant) or comparator.value != "__main__":
        return False
    body_stmt = stmt.body[0]
    if not isinstance(body_stmt, ast.Raise) or body_stmt.cause is not None:
        return False
    exc = body_stmt.exc
    if not isinstance(exc, ast.Call):
        return False
    if not isinstance(exc.func, ast.Name) or exc.func.id != "SystemExit":
        return False
    return len(exc.keywords) == 0 and len(exc.args) == 1


def _import_targets(module: ast.Module) -> tuple[str, ...]:
    targets: list[str] = []
    for stmt in _trim_module_docstring(module.body):
        if isinstance(stmt, ast.ImportFrom) and stmt.module is not None:
            targets.append(f"{'.' * stmt.level}{stmt.module}")
    return tuple(targets)


def _is_export_list_assignment(stmt: ast.stmt) -> bool:
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        return False
    target = stmt.targets[0]
    if not isinstance(target, ast.Name) or target.id != "__all__":
        return False
    value = stmt.value
    if not isinstance(value, (ast.List, ast.Tuple)):
        return False
    return all(
        isinstance(element, ast.Constant) and isinstance(element.value, str)
        for element in value.elts
    )


def _has_supported_shim_shape(module: ast.Module) -> bool:
    body = _trim_module_docstring(module.body)
    if not body:
        return False
    saw_import = False
    for stmt in body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module is not None:
            saw_import = True
            continue
        if _is_export_list_assignment(stmt):
            continue
        if _is_if_main_guard(stmt):
            continue
        return False
    return saw_import


def _parse_shim_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = _SHIM_METADATA_PATTERN.match(line)
        if match is None:
            continue
        metadata[match.group("key").lower()] = match.group("value").strip()
    return metadata


def _count_shim_nonblank_lines(text: str) -> int:
    count = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#!"):
            continue
        if _SHIM_METADATA_PATTERN.match(line):
            continue
        count += 1
    return count


def _namespace_targets_match(import_targets: tuple[str, ...], namespace_subdir: str) -> bool:
    if not namespace_subdir:
        return True
    return any(
        target == f".{namespace_subdir}"
        or target.startswith(f".{namespace_subdir}.")
        or target == namespace_subdir
        or target.startswith(f"{namespace_subdir}.")
        for target in import_targets
    )


def resolve_shim_target_path(repo_root: Path, target: str) -> Path | None:
    """Resolve one shim target to a live repo path when possible."""
    target_text = target.strip()
    if not target_text:
        return None
    target_path = repo_root / Path(target_text)
    if target_path.exists():
        return target_path
    if "/" in target_text or "\\" in target_text or target_text.endswith(".py"):
        return None
    dotted = Path(*target_text.split("."))
    module_path = repo_root / dotted.with_suffix(".py")
    package_init = repo_root / dotted / "__init__.py"
    if module_path.exists():
        return module_path
    if package_init.exists():
        return package_init
    return None


def detect_compatibility_shim(
    path: Path,
    *,
    namespace_subdir: str,
    shim_contains_all: tuple[str, ...] = (),
    shim_max_nonblank_lines: int = 0,
    shim_required_metadata_fields: tuple[str, ...] = (),
) -> CompatibilityShimValidation:
    """Validate whether a file is a minimal compatibility shim."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return CompatibilityShimValidation(False, {})
    max_nonblank_lines = shim_max_nonblank_lines or 3
    if _count_shim_nonblank_lines(text) > max_nonblank_lines:
        return CompatibilityShimValidation(False, {})
    try:
        module = ast.parse(text)
    except SyntaxError:
        return CompatibilityShimValidation(False, {})
    docstring = ast.get_docstring(module, clean=False) or ""
    if "Backward-compat shim" not in docstring:
        return CompatibilityShimValidation(False, {})
    if not _has_supported_shim_shape(module):
        return CompatibilityShimValidation(False, {})
    import_targets = _import_targets(module)
    stripped_lines = [line.strip() for line in text.splitlines() if line.strip()]
    stripped_text = " ".join(stripped_lines)
    if shim_contains_all and not all(token in stripped_text for token in shim_contains_all):
        return CompatibilityShimValidation(False, {})
    if not shim_contains_all and not _namespace_targets_match(import_targets, namespace_subdir):
        return CompatibilityShimValidation(False, {})
    metadata = _parse_shim_metadata(text)
    missing_metadata_fields = tuple(
        field for field in shim_required_metadata_fields if not metadata.get(field)
    )
    if missing_metadata_fields:
        return CompatibilityShimValidation(
            False,
            metadata,
            missing_metadata_fields=missing_metadata_fields,
        )
    return CompatibilityShimValidation(True, metadata)


def is_backward_compat_shim(
    path: Path,
    *,
    namespace_subdir: str,
    shim_contains_all: tuple[str, ...] = (),
    shim_max_nonblank_lines: int = 0,
    shim_required_metadata_fields: tuple[str, ...] = (),
) -> bool:
    """Return whether a short file is an intentional compatibility shim."""
    return detect_compatibility_shim(
        path,
        namespace_subdir=namespace_subdir,
        shim_contains_all=shim_contains_all,
        shim_max_nonblank_lines=shim_max_nonblank_lines,
        shim_required_metadata_fields=shim_required_metadata_fields,
    ).is_valid


__all__ = [
    "STANDARD_SHIM_METADATA_FIELDS",
    "detect_compatibility_shim",
    "is_backward_compat_shim",
    "resolve_shim_target_path",
]
