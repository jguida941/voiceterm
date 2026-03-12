#!/usr/bin/env python3
"""Review probe: detect weak Python exception-handling patterns.

Targets AI-written fallback patterns that technically work but degrade
observability and maintenance quality:

- suppressive broad handlers that silently fall back without logging/context
- exception translation that re-raises a generic message with no runtime detail

This probe always exits 0. It emits structured risk hints for AI review.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

try:
    from check_bootstrap import (
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )
    from probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import (
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )
    from dev.scripts.checks.probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )

try:
    from dev.scripts.devctl.quality_scan_mode import is_adoption_scan
except ModuleNotFoundError:  # pragma: no cover
    repo_root_str = str(Path(__file__).resolve().parents[3])
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    from dev.scripts.devctl.quality_scan_mode import is_adoption_scan

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")
is_review_probe_test_path = import_attr("probe_path_filters", "is_review_probe_test_path")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

REVIEW_LENS = "error_handling"
SUPPRESSIVE_SIGNAL = "suppressive broad handler"
TRANSLATION_SIGNAL = "translated exception without runtime context"

AI_INSTRUCTIONS = {
    "silent_suppressive_broad": (
        "This broad exception handler swallows control flow without logging or "
        "runtime context. Narrow the exception type if possible. If fail-soft "
        "behavior is intentional, emit structured context or return a typed "
        "result object so the fallback is observable and reviewable."
    ),
    "weak_exception_translation": (
        "This handler catches an exception and re-raises a generic message with "
        "little runtime detail. Include the path/id/input that failed, or add "
        "structured context before translating the exception."
    ),
}


def _handler_kind(node_type: ast.expr | None) -> str | None:
    if node_type is None:
        return "bare"
    if isinstance(node_type, ast.Tuple):
        return _tuple_handler_kind(node_type)
    if isinstance(node_type, ast.Name):
        name = node_type.id
    elif isinstance(node_type, ast.Attribute):
        name = node_type.attr
    else:
        return None
    if name in {"Exception", "BaseException"}:
        return name
    return None


def _tuple_handler_kind(node_type: ast.Tuple) -> str | None:
    members: set[str] = set()
    for element in node_type.elts:
        kind = _handler_kind(element)
        if kind is not None:
            members.add(kind)
    if not members:
        return None
    return ",".join(sorted(members))


def _has_raise(handler: ast.ExceptHandler) -> bool:
    return any(isinstance(node, ast.Raise) for node in ast.walk(handler))


def _has_observable_call(handler: ast.ExceptHandler) -> bool:
    return any(isinstance(node, ast.Call) for node in ast.walk(handler))


def _returns_sentinel(handler: ast.ExceptHandler) -> bool:
    for node in ast.walk(handler):
        if isinstance(node, ast.Return):
            return True
        if isinstance(node, ast.Pass | ast.Continue | ast.Break):
            return True
    return False


def _name_set(node: ast.AST) -> set[str]:
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}


def _call_context_names(call: ast.Call) -> set[str]:
    names: set[str] = set()
    for arg in call.args:
        names.update(_name_set(arg))
    for keyword in call.keywords:
        if keyword.value is not None:
            names.update(_name_set(keyword.value))
    return names


def _is_generic_raise_message(node: ast.Raise, exc_name: str | None) -> bool:
    if node.exc is None:
        return False
    if not isinstance(node.exc, ast.Call):
        return False
    if not node.exc.args:
        return True
    if node.cause is None:
        return False
    if not isinstance(node.cause, ast.Name):
        return False
    if exc_name is None or node.cause.id != exc_name:
        return False
    first_arg = node.exc.args[0]
    context_names = _call_context_names(node.exc)
    allowed = {exc_name}
    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
        return not context_names or context_names <= allowed
    if isinstance(first_arg, ast.JoinedStr):
        return not context_names or context_names <= allowed
    return False


def _symbol_name(stack: list[str]) -> str:
    if not stack:
        return "(module)"
    return stack[-1]


def _is_silent_suppressive_handler(node: ast.ExceptHandler) -> bool:
    kind = _handler_kind(node.type)
    if kind is None:
        return False
    if _has_raise(node) or not _returns_sentinel(node):
        return False
    return not _has_observable_call(node)


def _build_hint(
    *,
    path: Path,
    symbol: str,
    severity: str,
    signals: list[str],
    instruction_key: str,
) -> RiskHint:
    return RiskHint(
        file=path.as_posix(),
        symbol=symbol,
        risk_type="error_handling",
        severity=severity,
        signals=signals,
        ai_instruction=AI_INSTRUCTIONS[instruction_key],
        review_lens=REVIEW_LENS,
    )


def _iter_generic_translation_raises(node: ast.ExceptHandler, exc_name: str | None) -> list[ast.Raise]:
    matches: list[ast.Raise] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Raise) and _is_generic_raise_message(child, exc_name):
            matches.append(child)
    return matches


class _ExceptionQualityVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.stack: list[str] = []
        self.hints: list[RiskHint] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        symbol = _symbol_name(self.stack)
        if _is_silent_suppressive_handler(node):
            self.hints.append(
                _build_hint(
                    path=self.path,
                    symbol=symbol,
                    severity="high",
                    signals=[
                        f"{SUPPRESSIVE_SIGNAL} at line {node.lineno} falls back " "without logging or runtime context"
                    ],
                    instruction_key="silent_suppressive_broad",
                )
            )
        exc_name = node.name if isinstance(node.name, str) else None
        for child in _iter_generic_translation_raises(node, exc_name):
            self.hints.append(
                _build_hint(
                    path=self.path,
                    symbol=symbol,
                    severity="medium",
                    signals=[f"{TRANSLATION_SIGNAL} at line {child.lineno}"],
                    instruction_key="weak_exception_translation",
                )
            )
        self.generic_visit(node)


def build_report(
    *,
    repo_root: Path,
    candidate_paths: list[Path],
    current_text_by_path: dict[str, str | None],
    mode: str,
) -> ProbeReport:
    report = ProbeReport(command="probe_exception_quality")
    report.mode = mode
    files_with_hints: set[str] = set()
    target_roots = resolve_quality_scope_roots("python_probe", repo_root=repo_root)

    for path in candidate_paths:
        if path.suffix != ".py":
            continue
        if not is_under_target_roots(path, repo_root=repo_root, target_roots=target_roots):
            continue
        if is_review_probe_test_path(path):
            continue
        relative = path.relative_to(repo_root).as_posix() if path.is_absolute() else path.as_posix()
        text = current_text_by_path.get(relative)
        if text is None:
            continue
        report.files_scanned += 1
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        visitor = _ExceptionQualityVisitor(Path(relative))
        visitor.visit(tree)
        if visitor.hints:
            files_with_hints.add(relative)
            report.risk_hints.extend(visitor.hints)

    report.files_with_hints = len(files_with_hints)
    return report


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, _base_map = list_changed_paths_with_base_map(
            guard.run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError:
        report = ProbeReport(command="probe_exception_quality")
        report.mode = (
            "adoption-scan"
            if is_adoption_scan(since_ref=args.since_ref, head_ref=args.head_ref)
            else ("commit-range" if args.since_ref else "working-tree")
        )
        return emit_probe_report(report, output_format=args.format)

    current_text_by_path: dict[str, str | None] = {}
    for path in changed_paths:
        if path.suffix != ".py":
            continue
        relative = path.as_posix()
        text = guard.read_text_from_ref(path, args.head_ref) if args.since_ref else guard.read_text_from_worktree(path)
        current_text_by_path[relative] = text

    mode = (
        "adoption-scan"
        if is_adoption_scan(since_ref=args.since_ref, head_ref=args.head_ref)
        else ("commit-range" if args.since_ref else "working-tree")
    )
    report = build_report(
        repo_root=REPO_ROOT,
        candidate_paths=changed_paths,
        current_text_by_path=current_text_by_path,
        mode=mode,
    )
    report.since_ref = args.since_ref
    report.head_ref = args.head_ref
    return emit_probe_report(report, output_format=args.format)


if __name__ == "__main__":
    sys.exit(main())
