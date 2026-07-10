#!/usr/bin/env python3
"""Validate emitted ActionResult.status values stay within ActionOutcome.ALL.

P193 guard (per GUARD_AUDIT_FINDINGS.md + cached-hammock R130 finding):
ActionResult.status is declared as a closed domain ActionOutcome.ALL =
{pass, fail, unknown, defer}, but `command_runner.py:95,169` emits
"started"/"interrupted"/"completed"/"failed" — values OUTSIDE the
declared set. This is the canonical "typed boundary lie" the operator
flagged as architecture inversion.

This guard scans repo for `status="<literal>"` values passed to ActionResult
envelopes and flags any literal not in ActionOutcome.ALL. Report-only mode
initially per P188 discipline (would_fail tracks but does not block).

Composes with: ActionOutcome enum (action_contracts.py:84) + check_runtime_bridge_projection_separation
+ check_plan_row_contract_refs_resolve (sibling guards landed this session).
"""

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


COMMAND = "check_action_result_status_domain"
ACTION_RESULT_STATUS_DOMAIN_GUARD_ID = "ActionResultStatusDomain"
ACTION_RESULT_STATUS_DOMAIN_CONTRACT_ID = "ActionResultStatusDomainGuard"

# ActionOutcome.ALL from dev/scripts/devctl/runtime/action_contracts.py:84
ACTION_OUTCOME_ALL = frozenset({"pass", "fail", "unknown", "defer"})
ACTION_RESULT_STATUS_CALLS = frozenset({"ActionResult", "ActionResultFields"})

# Scan these directories for status= literals; skip tests + fixtures
SCAN_ROOTS = (
    "dev/scripts/devctl/runtime",
    "dev/scripts/devctl/review_channel",
    "dev/scripts/devctl/commands",
    "dev/scripts/devctl",
)
SKIP_PATH_FRAGMENTS = (
    "/tests/",
    "/test_",
    "/fixtures/",
    "/__pycache__/",
)


@dataclass(frozen=True, slots=True)
class ActionResultStatusDomainGuard:
    """Registry-facing contract for the ActionResult.status domain guard report."""

    guard_id: str
    ok: bool
    report_only: bool
    would_fail: bool
    declared_domain: tuple[str, ...]
    files_scanned: int = 0
    violation_count: int = 0
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    schema_version: int = 1
    contract_id: str = "ActionResultStatusDomainGuard"
    command: str = "check_action_result_status_domain"


@dataclass(frozen=True)
class StatusDomainViolation:
    path: str
    line: int
    literal: str
    excerpt: str

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "line": self.line,
            "literal": self.literal,
            "excerpt": self.excerpt,
        }


def _should_skip(path: Path, repo_root: Path) -> bool:
    try:
        rel_path = "/" + path.relative_to(repo_root).as_posix()
    except ValueError:
        rel_path = "/" + path.as_posix()
    return any(fragment in rel_path for fragment in SKIP_PATH_FRAGMENTS)


def _excerpt_for_line(text: str, line: int) -> str:
    lines = text.splitlines()
    if 1 <= line <= len(lines):
        return lines[line - 1].strip()
    return ""


def _scan_keyword_status_literal(node: ast.keyword) -> str:
    if node.arg != "status":
        return ""
    value = node.value
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return ""


def _scan_file(path: Path, repo_root: Path) -> list[StatusDomainViolation]:
    rel_path = str(path.relative_to(repo_root))
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    violations: list[StatusDomainViolation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node.func) not in ACTION_RESULT_STATUS_CALLS:
            continue
        for keyword in node.keywords:
            literal = _scan_keyword_status_literal(keyword)
            if not literal or literal in ACTION_OUTCOME_ALL:
                continue
            line = getattr(keyword, "lineno", getattr(node, "lineno", 1))
            violations.append(
                StatusDomainViolation(
                    path=rel_path,
                    line=line,
                    literal=literal,
                    excerpt=_excerpt_for_line(text, line),
                )
            )
    return violations


def evaluate_action_result_status_domain(
    *,
    repo_root: Path = REPO_ROOT,
) -> ActionResultStatusDomainGuard:
    files_scanned = 0
    violations: list[StatusDomainViolation] = []
    seen: set[Path] = set()
    for root_rel in SCAN_ROOTS:
        root = repo_root / root_rel
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if path in seen or _should_skip(path, repo_root):
                continue
            seen.add(path)
            files_scanned += 1
            violations.extend(_scan_file(path, repo_root))

    return ActionResultStatusDomainGuard(
        guard_id=ACTION_RESULT_STATUS_DOMAIN_GUARD_ID,
        ok=True,
        report_only=True,
        would_fail=bool(violations),
        declared_domain=tuple(sorted(ACTION_OUTCOME_ALL)),
        files_scanned=files_scanned,
        violation_count=len(violations),
        violations=tuple(violation.to_dict() for violation in violations[:50]),
    )


def _render_md(report: ActionResultStatusDomainGuard) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- report_only: {report.report_only}")
    lines.append(f"- would_fail: {report.would_fail}")
    lines.append(f"- declared_domain: {report.declared_domain}")
    lines.append(f"- files_scanned: {report.files_scanned}")
    lines.append(f"- violation_count: {report.violation_count}")
    if report.violations:
        lines.append("")
        lines.append("## Violations (first 50)")
        for violation in report.violations:
            if not isinstance(violation, dict):
                continue
            lines.append(
                "- "
                f"{violation.get('path')}:{violation.get('line')} "
                f"literal={violation.get('literal')!r}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = evaluate_action_result_status_domain()
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2))
    else:
        print(_render_md(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
