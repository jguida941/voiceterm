#!/usr/bin/env python3
"""Guard against split-brain provider lists on agent-facing CLI flags."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections.abc import Iterable
from pathlib import Path

_BOOT_ROOT = str(Path(__file__).resolve().parents[4])
if _BOOT_ROOT not in sys.path:
    sys.path.insert(0, _BOOT_ROOT)

try:
    from check_bootstrap import REPO_ROOT, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover - package-style fallback
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, utc_timestamp

from dev.scripts.devctl.runtime.provider_registry import KNOWN_AGENT_PROVIDERS

SCAN_ROOTS = (
    Path("dev/scripts/devctl/cli_parser"),
    Path("dev/scripts/devctl/commands"),
)


def build_report(*, repo_root: Path = REPO_ROOT, scan_roots: Iterable[Path] = SCAN_ROOTS) -> dict[str, object]:
    """Return provider-list parity violations for agent-facing parser flags."""
    violations: list[dict[str, object]] = []
    files_scanned = 0
    for root in scan_roots:
        scan_root = repo_root / root
        if not scan_root.exists():
            continue
        for path in sorted(scan_root.rglob("*.py")):
            files_scanned += 1
            violations.extend(_provider_choice_violations(path=path, repo_root=repo_root))
    return {
        "command": "check_provider_list_parity_graph",
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "files_scanned": files_scanned,
        "known_agent_providers": list(KNOWN_AGENT_PROVIDERS),
        "violations": violations,
    }


def _provider_choice_violations(*, path: Path, repo_root: Path) -> list[dict[str, object]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return []
    relative = path.relative_to(repo_root).as_posix()
    violations: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_add_argument_call(node):
            continue
        if "--agent" not in _string_args(node):
            continue
        choices = _choices_literal(node)
        if not choices:
            continue
        provider_choices = sorted(set(choices).intersection(KNOWN_AGENT_PROVIDERS))
        if len(provider_choices) < 2:
            continue
        violations.append(
            {
                "check": "agent_provider_choices_use_shared_registry",
                "path": relative,
                "line": node.lineno,
                "provider_choices": provider_choices,
                "detail": (
                    "`--agent` parser choices hardcode provider ids. Use "
                    "`runtime.provider_registry` syntax validation so agent-facing "
                    "commands do not drift apart."
                ),
            }
        )
    return violations


def _is_add_argument_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr == "add_argument"
    return isinstance(func, ast.Name) and func.id == "add_argument"


def _string_args(node: ast.Call) -> tuple[str, ...]:
    rows: list[str] = []
    for arg in node.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            rows.append(arg.value)
    return tuple(rows)


def _choices_literal(node: ast.Call) -> tuple[str, ...]:
    for keyword in node.keywords:
        if keyword.arg != "choices":
            continue
        value = keyword.value
        if not isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            return ()
        rows: list[str] = []
        for element in value.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                rows.append(element.value)
        return tuple(rows)
    return ()


def _render_md(report: dict[str, object]) -> str:
    violations = report.get("violations")
    rows = violations if isinstance(violations, list) else []
    lines = ["# check_provider_list_parity_graph", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_scanned: {report['files_scanned']}")
    lines.append(f"- violations: {len(rows)}")
    if rows:
        lines.append("")
        lines.append("## Violations")
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('path')}:{row.get('line')}` "
                f"{row.get('detail')}"
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check that agent-facing CLI provider lists do not drift apart."
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
