"""Report runtime dependencies on bridge projection helpers."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from _ast_helpers import _call_name
except ModuleNotFoundError:
    from dev.scripts.checks._ast_helpers import _call_name


RUNTIME_ROOT = "dev/scripts/devctl/runtime"
REVIEW_CHANNEL_ROOT = "dev/scripts/devctl/review_channel"
COMMANDS_ROOT = "dev/scripts/devctl/commands"
SCAN_ROOTS = (
    RUNTIME_ROOT,
    REVIEW_CHANNEL_ROOT,
    COMMANDS_ROOT,
)
BRIDGE_SEPARATION_GUARD_CONTRACT_ID = "BridgeSeparationGuard"
RUNTIME_BRIDGE_PROJECTION_SEPARATION_GUARD_ID = "RuntimeBridgeProjectionSeparation"
FORBIDDEN_MODULE_FRAGMENTS = (
    "dev.scripts.devctl.review_channel.bridge_",
    "dev.scripts.devctl.review_channel.bridge.",
    "dev.scripts.devctl.commands.review_channel.bridge_",
    "dev.scripts.devctl.commands.review_channel.bridge.",
    "review_channel.bridge_",
    "review_channel.bridge.",
    "commands.review_channel.bridge_",
    "commands.review_channel.bridge.",
    "dev.scripts.devctl.commands.bridge_",
    "dev.scripts.devctl.commands.bridge.",
    "commands.bridge_",
    "commands.bridge.",
    ".bridge_",
    ".bridge.",
)


@dataclass(frozen=True, slots=True)
class BridgeSeparationGuard:
    """Registry-facing contract for the runtime bridge-separation guard report."""

    guard_id: str
    ok: bool
    report_only: bool
    would_fail: bool
    scan_roots: tuple[str, ...] = field(default_factory=tuple)
    checked_paths: tuple[str, ...] = field(default_factory=tuple)
    violation_count: int = 0
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    migration_policy: str = ""
    schema_version: int = 1
    contract_id: str = "BridgeSeparationGuard"
    command: str = "check_runtime_bridge_projection_separation"


@dataclass(frozen=True)
class Violation:
    rule: str
    path: str
    line: int
    detail: str
    excerpt: str = ""


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _excerpt_for_line(text: str, line: int) -> str:
    lines = text.splitlines()
    if 1 <= line <= len(lines):
        return lines[line - 1].strip()
    return ""


def _is_bridge_projection_module(module_name: str) -> bool:
    normalized = module_name.replace("/", ".")
    return any(fragment in normalized for fragment in FORBIDDEN_MODULE_FRAGMENTS)


def _is_bridge_projection_call(name: str) -> bool:
    return (
        name.startswith("extract_bridge_")
        or (name.startswith("bridge_") and "_from_" in name)
        or (name.startswith("build_") and "_bridge_" in name)
    )


def _node_violation(
    *,
    rule: str,
    rel_path: str,
    text: str,
    node: ast.AST,
    detail: str,
) -> Violation:
    line = getattr(node, "lineno", 1)
    return Violation(
        rule=rule,
        path=rel_path,
        line=line,
        detail=detail,
        excerpt=_excerpt_for_line(text, line),
    )


def _import_module_names(node: ast.Import | ast.ImportFrom) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    return ("." * node.level + (node.module or ""),)


def _scan_import_node(node: ast.Import | ast.ImportFrom, rel_path: str, text: str) -> list[Violation]:
    modules = _import_module_names(node)
    if not any(_is_bridge_projection_module(module) for module in modules):
        return []
    return [
        _node_violation(
            rule="runtime_bridge_projection_import",
            rel_path=rel_path,
            text=text,
            node=node,
            detail="Scanned control-plane code must not import bridge projection modules.",
        )
    ]


def _scan_call_node(node: ast.Call, rel_path: str, text: str) -> list[Violation]:
    name = _call_name(node.func)
    if not _is_bridge_projection_call(name):
        return []
    return [
        _node_violation(
            rule="runtime_bridge_projection_call",
            rel_path=rel_path,
            text=text,
            node=node,
            detail="Scanned control-plane code must not call bridge-derived helper APIs.",
        )
    ]


def _scan_ast_node(node: ast.AST, rel_path: str, text: str) -> list[Violation]:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return _scan_import_node(node, rel_path, text)
    if isinstance(node, ast.Call):
        return _scan_call_node(node, rel_path, text)
    return []


def _scan_file(path: Path, root: Path) -> list[Violation]:
    rel_path = _relative(path, root)
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [
            Violation(
                rule="python_parse_error",
                path=rel_path,
                line=exc.lineno or 1,
                detail=f"Unable to parse Python file: {exc.msg}",
            )
        ]

    violations: list[Violation] = []
    for node in ast.walk(tree):
        violations.extend(_scan_ast_node(node, rel_path, text))
    return violations


def _build_report(root: Path | None = None) -> dict[str, object]:
    repo_root = root or REPO_ROOT
    checked_paths: list[str] = []
    violations: list[Violation] = []
    for scan_root in SCAN_ROOTS:
        root_path = repo_root / scan_root
        for path in sorted(root_path.rglob("*.py")):
            checked_paths.append(_relative(path, repo_root))
            violations.extend(_scan_file(path, repo_root))
    return {
        "command": "check_runtime_bridge_projection_separation",
        "ok": True,
        "would_fail": bool(violations),
        "report_only": True,
        "contract_id": BRIDGE_SEPARATION_GUARD_CONTRACT_ID,
        "guard_id": RUNTIME_BRIDGE_PROJECTION_SEPARATION_GUARD_ID,
        "schema_version": 1,
        "scan_roots": list(SCAN_ROOTS),
        "checked_paths": checked_paths,
        "violation_count": len(violations),
        "violations": [asdict(violation) for violation in violations],
        "migration_policy": (
            "Report-only until P188 typed snapshot, renderer, absent-bridge dogfood, "
            "bridge-reader migration, and scoped review-channel/commands baselines "
            "establish the strict baseline."
        ),
    }


def _render_md(report: dict[str, object]) -> str:
    lines = ["# check_runtime_bridge_projection_separation", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- report_only: {report.get('report_only', False)}")
    lines.append(f"- would_fail: {report.get('would_fail', False)}")
    lines.append(f"- scan_roots: {', '.join(report.get('scan_roots', []))}")
    lines.append(f"- checked_paths: {len(report.get('checked_paths', []))}")
    lines.append(f"- violation_count: {report.get('violation_count', 0)}")
    if report.get("violations"):
        lines.append("")
        lines.append("## Violations")
        for violation in report["violations"]:
            if not isinstance(violation, dict):
                continue
            lines.append(
                "- "
                f"{violation.get('path')}:{violation.get('line')} "
                f"{violation.get('rule')} - {violation.get('detail')}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = _build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
