#!/usr/bin/env python3
"""Guard bridge/projection compatibility surfaces from becoming authority."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ENFORCED_AUTHORITY_FILES = (
    "dev/scripts/devctl/runtime/push_authorization.py",
    "dev/scripts/devctl/runtime/review_state_parse_support.py",
    "dev/scripts/devctl/runtime/review_state_models.py",
    "dev/scripts/devctl/review_channel/status_projection_bridge_state.py",
    "dev/scripts/devctl/review_channel/status_projection_helpers.py",
    "dev/scripts/devctl/review_channel/bridge_projection_metadata.py",
)
"""Files with bridge-as-authority regressions already repaired in this slice."""

BRIDGE_POLL_FILES = (
    "dev/scripts/devctl/commands/review_channel/_bridge_poll.py",
)

BRIDGE_METADATA_FIELD = "bridge_metadata_reviewer_mode"
ACK_COMPATIBILITY_LITERALS = ("Claude Ack", "Implementer Ack")
ACK_FILTER_MARKERS = ("_ACK_ONLY_ERROR_PREFIXES", "ACK_REVISION_REQUIREMENT_PREFIX")


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


def _existing_files(root: Path, rel_paths: tuple[str, ...]) -> tuple[Path, ...]:
    paths: list[Path] = []
    for rel_path in rel_paths:
        path = root / rel_path
        if path.exists() and path.is_file():
            paths.append(path)
    return tuple(paths)


def _line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _excerpt_for_line(text: str, line: int) -> str:
    lines = text.splitlines()
    if 1 <= line <= len(lines):
        return lines[line - 1].strip()
    return ""


def _text_violations(path: Path, root: Path, text: str) -> list[Violation]:
    rel_path = _relative(path, root)
    violations: list[Violation] = []

    if BRIDGE_METADATA_FIELD in text:
        offset = text.index(BRIDGE_METADATA_FIELD)
        line = _line_for_offset(text, offset)
        violations.append(
            Violation(
                rule="bridge_metadata_reviewer_mode_forbidden",
                path=rel_path,
                line=line,
                detail=(
                    "`bridge_metadata_reviewer_mode` must not flow into typed "
                    "authority or compatibility-parser state."
                ),
                excerpt=_excerpt_for_line(text, line),
            )
        )

    if rel_path.endswith("push_authorization.py") and "effective_reviewer_mode" in text:
        offset = text.index("effective_reviewer_mode")
        line = _line_for_offset(text, offset)
        violations.append(
            Violation(
                rule="push_authorization_effective_mode_string_forbidden",
                path=rel_path,
                line=line,
                detail=(
                    "Push authorization must derive dual-agent authority from "
                    "`LiveRoleTopology`, not the `effective_reviewer_mode` string."
                ),
                excerpt=_excerpt_for_line(text, line),
            )
        )

    if rel_path.endswith("push_authorization.py") and '"active_dual_agent"' in text:
        offset = text.index('"active_dual_agent"')
        line = _line_for_offset(text, offset)
        violations.append(
            Violation(
                rule="push_authorization_active_dual_literal_forbidden",
                path=rel_path,
                line=line,
                detail=(
                    "Push authorization must not restore an `active_dual_agent` "
                    "string equality gate."
                ),
                excerpt=_excerpt_for_line(text, line),
            )
        )

    if rel_path.endswith("_bridge_poll.py"):
        for marker in ACK_FILTER_MARKERS:
            if marker in text:
                offset = text.index(marker)
                line = _line_for_offset(text, offset)
                violations.append(
                    Violation(
                        rule="bridge_poll_ack_filter_forbidden",
                        path=rel_path,
                        line=line,
                        detail=(
                            "Bridge-poll must not hide ACK freshness errors with "
                            "compatibility-string filters."
                        ),
                        excerpt=_excerpt_for_line(text, line),
                    )
                )
        for literal in ACK_COMPATIBILITY_LITERALS:
            if literal in text:
                offset = text.index(literal)
                line = _line_for_offset(text, offset)
                violations.append(
                    Violation(
                        rule="bridge_poll_ack_literal_authority_forbidden",
                        path=rel_path,
                        line=line,
                        detail=(
                            "Bridge-poll authority must not branch on legacy ACK "
                            "section headings."
                        ),
                        excerpt=_excerpt_for_line(text, line),
                    )
                )

    return violations


def _bridge_poll_call_violations(path: Path, root: Path, text: str) -> list[Violation]:
    rel_path = _relative(path, root)
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
        if not isinstance(node, ast.Call):
            continue
        if not _is_name(node.func, "validate_live_bridge_contract"):
            continue
        if any(keyword.arg == "typed_current_session" for keyword in node.keywords):
            continue
        line = getattr(node, "lineno", 1)
        violations.append(
            Violation(
                rule="bridge_validation_requires_typed_current_session",
                path=rel_path,
                line=line,
                detail=(
                    "`validate_live_bridge_contract(...)` may only run from "
                    "bridge-poll when driven by `typed_current_session`."
                ),
                excerpt=_excerpt_for_line(text, line),
            )
        )
    return violations


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _build_report(root: Path | None = None) -> dict[str, object]:
    repo_root = root or REPO_ROOT
    violations: list[Violation] = []
    checked_paths: list[str] = []

    for path in _existing_files(repo_root, ENFORCED_AUTHORITY_FILES):
        checked_paths.append(_relative(path, repo_root))
        text = path.read_text(encoding="utf-8")
        violations.extend(_text_violations(path, repo_root, text))

    for path in _existing_files(repo_root, BRIDGE_POLL_FILES):
        checked_paths.append(_relative(path, repo_root))
        text = path.read_text(encoding="utf-8")
        violations.extend(_text_violations(path, repo_root, text))
        violations.extend(_bridge_poll_call_violations(path, repo_root, text))

    ok = not violations
    return {
        "command": "check_bridge_projection_only",
        "ok": ok,
        "contract_id": "BridgeProjectionOnlyGuard",
        "schema_version": 1,
        "checked_paths": sorted(set(checked_paths)),
        "violation_count": len(violations),
        "violations": [asdict(violation) for violation in violations],
        "known_debt_policy": (
            "This guard locks repaired authority/projection seams. The wider "
            "active_dual_agent and ACK-literal debt inventory is retired by "
            "later slices, then added to this enforced set."
        ),
    }


def _render_md(report: dict[str, object]) -> str:
    lines = ["# check_bridge_projection_only", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- contract_id: {report.get('contract_id', '')}")
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
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
