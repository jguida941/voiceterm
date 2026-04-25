"""Static writer-authority checks for typed review-state fields."""

from __future__ import annotations

import ast
from pathlib import Path

from dev.scripts.devctl.config import REPO_ROOT
from dev.scripts.devctl.platform.connectivity_registry import (
    build_connectivity_registry_snapshot,
)
from dev.scripts.devctl.platform.connectivity_registry_models import (
    ConnectivityRegistrySnapshot,
)

_CURRENT_SESSION_CONSTRUCTOR_ALLOWLIST = frozenset(
    {
        "dev/scripts/devctl/review_channel/current_session_projection.py",
        "dev/scripts/devctl/review_channel/current_session_support.py",
        "dev/scripts/devctl/review_channel/event_reducer_state.py",
        "dev/scripts/devctl/review_channel/recovery_assessment.py",
        "dev/scripts/devctl/runtime/review_state_parser_rows.py",
    }
)

_CURRENT_SESSION_REVIEW_STATE_WRITE_ALLOWLIST = frozenset(
    {
        "dev/scripts/devctl/review_channel/event_projection_assembly.py",
    }
)

_REVIEWER_MODE_WRITE_ALLOWLIST = frozenset(
    {
        "dev/scripts/devctl/commands/governance/session_resume_authority_payload.py",
        "dev/scripts/devctl/review_channel/event_projection_bridge.py",
        "dev/scripts/devctl/review_channel/projection_bundle_parity.py",
        "dev/scripts/devctl/review_channel/status_projection_bridge_state.py",
        "dev/scripts/devctl/review_channel/status_projection_helpers.py",
    }
)

_REVIEWER_MODE_KEYS = frozenset({"reviewer_mode", "effective_reviewer_mode"})
_REVIEWER_MODE_TARGETS = frozenset(
    {
        "bridge_liveness",
        "bridge_state",
        "payload",
        "review_state",
        "review_state_payload",
        "typed",
    }
)


def check_typed_state_writer_authority(
    *,
    repo_root: Path = REPO_ROOT,
    python_files: tuple[Path, ...] | None = None,
) -> tuple[dict[str, object], tuple[dict[str, object], ...]]:
    """Return coverage and violations for typed review-state writer chokepoints."""
    files = tuple(python_files) if python_files is not None else _iter_python_files(repo_root)
    violations: list[dict[str, object]] = []
    scanned_files = 0
    registry = build_connectivity_registry_snapshot(repo_root=repo_root)
    violations.extend(_registry_writer_violations(registry))
    for path in files:
        rel_path = _relative_path(path, repo_root)
        if _is_test_path(rel_path):
            continue
        scanned_files += 1
        violations.extend(_scan_file(path=path, rel_path=rel_path))

    coverage = {
        "kind": "typed_state_writer_authority",
        "contract_id": "ReviewState",
        "check": "review-typed-state-writer-authority",
        "ok": not violations,
        "scanned_files": scanned_files,
        "source_contract": registry.contract_id,
        "registry_contract_count": len(registry.connected_contracts),
        "violation_count": len(violations),
        "detail": (
            "Typed review-state writer authority is confined to approved chokepoints."
            if not violations
            else "Typed review-state writer authority has bypasses."
        ),
    }
    return coverage, tuple(violations)


def _registry_writer_violations(
    registry: ConnectivityRegistrySnapshot,
) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    for contract in registry.connected_contracts:
        for field in contract.fields:
            if field.field_kind == "source" and len(field.writer_ids) != 1:
                violations.append(
                    _violation(
                        rel_path=contract.writer.path,
                        line=1,
                        field=f"{contract.contract_id}.{field.field_name}",
                        detail=(
                            "ConnectivityRegistry source fields must declare "
                            "exactly one writer."
                        ),
                    )
                )
            if field.field_kind == "derived" and not field.derived_from:
                violations.append(
                    _violation(
                        rel_path=contract.writer.path,
                        line=1,
                        field=f"{contract.contract_id}.{field.field_name}",
                        detail=(
                            "ConnectivityRegistry derived fields must declare "
                            "their source fields."
                        ),
                    )
                )
    return violations


def _iter_python_files(repo_root: Path) -> tuple[Path, ...]:
    devctl_root = repo_root / "dev/scripts/devctl"
    return tuple(sorted(devctl_root.rglob("*.py")))


def _scan_file(*, path: Path, rel_path: str) -> tuple[dict[str, object], ...]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel_path)
    except (OSError, SyntaxError) as exc:
        return (
            _violation(
                rel_path=rel_path,
                line=1,
                field="module",
                detail=f"Unable to parse typed-state writer source: {exc}",
            ),
        )
    visitor = _TypedStateWriterVisitor(rel_path=rel_path)
    visitor.visit(tree)
    return tuple(visitor.violations)


class _TypedStateWriterVisitor(ast.NodeVisitor):
    def __init__(self, *, rel_path: str) -> None:
        self.rel_path = rel_path
        self.violations: list[dict[str, object]] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if (
            _call_name(node.func) == "ReviewCurrentSessionState"
            and self.rel_path not in _CURRENT_SESSION_CONSTRUCTOR_ALLOWLIST
        ):
            self.violations.append(
                _violation(
                    rel_path=self.rel_path,
                    line=node.lineno,
                    field="ReviewCurrentSessionState",
                    detail=(
                        "ReviewCurrentSessionState must be constructed through the "
                        "approved current-session builder/parser chokepoints."
                    ),
                )
            )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:  # noqa: N802
        for target in node.targets:
            self._check_assignment_target(target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:  # noqa: N802
        self._check_assignment_target(node.target)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:  # noqa: N802
        self._check_assignment_target(node.target)
        self.generic_visit(node)

    def _check_assignment_target(self, target: ast.AST) -> None:
        if not isinstance(target, ast.Subscript):
            return
        key = _literal_subscript_key(target.slice)
        base_name = _base_name(target.value)
        if (
            key == "current_session"
            and base_name == "review_state"
            and self.rel_path not in _CURRENT_SESSION_REVIEW_STATE_WRITE_ALLOWLIST
        ):
            self.violations.append(
                _violation(
                    rel_path=self.rel_path,
                    line=target.lineno,
                    field="current_session",
                    detail=(
                        'Direct review_state["current_session"] writes must flow '
                        "through the event projection assembly chokepoint."
                    ),
                )
            )
            return
        if (
            key in _REVIEWER_MODE_KEYS
            and base_name in _REVIEWER_MODE_TARGETS
            and self.rel_path not in _REVIEWER_MODE_WRITE_ALLOWLIST
        ):
            self.violations.append(
                _violation(
                    rel_path=self.rel_path,
                    line=target.lineno,
                    field=key,
                    detail=(
                        "Reviewer-mode projection writes must use the approved "
                        "authority projection chokepoints."
                    ),
                )
            )


def _call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _literal_subscript_key(slice_node: ast.AST) -> str:
    if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
        return slice_node.value
    return ""


def _base_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _relative_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _is_test_path(rel_path: str) -> bool:
    return "/tests/" in f"/{rel_path}"


def _violation(
    *,
    rel_path: str,
    line: int,
    field: str,
    detail: str,
) -> dict[str, object]:
    return {
        "kind": "typed_state_writer_authority",
        "contract_id": "ReviewState",
        "rule": "typed-state-writer-bypass",
        "file": rel_path,
        "line": line,
        "field": field,
        "detail": detail,
    }
