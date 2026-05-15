#!/usr/bin/env python3
"""Require local runtime-state receipt stores to stay ignored and untracked."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


COMMAND = "check_runtime_state_ignore_posture"
RUNTIME_STATE_IGNORE_POSTURE_GUARD_ID = "RuntimeStateIgnorePosture"
RUNTIME_STATE_IGNORE_POSTURE_CONTRACT_ID = "RuntimeStateIgnorePostureGuard"
DEFAULT_RUNTIME_STATE_PATHS: tuple[str, ...] = (
    "dev/state/bypass_lifecycles.jsonl",
    "dev/state/governed_exception_lifecycles.jsonl",
    "dev/state/raw_git_bypass_receipts.jsonl",
)


@dataclass(frozen=True, slots=True)
class RuntimeStatePathFinding:
    """One runtime-state path that violates local-state ignore posture."""

    path: str
    tracked: bool
    ignored: bool
    ignore_source: str
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RuntimeStateIgnorePostureGuard:
    """Registry-facing contract for runtime-state ignore posture checks."""

    guard_id: str
    ok: bool
    report_only: bool
    would_fail: bool
    checked_path_count: int = 0
    ignored_path_count: int = 0
    tracked_path_count: int = 0
    violation_count: int = 0
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    schema_version: int = 1
    contract_id: str = RUNTIME_STATE_IGNORE_POSTURE_CONTRACT_ID
    command: str = COMMAND


@dataclass(frozen=True)
class _PathPosture:
    path: str
    tracked: bool
    ignored: bool
    ignore_source: str


def evaluate_runtime_state_ignore_posture(
    *,
    repo_root: Path = REPO_ROOT,
    paths: tuple[str, ...] = DEFAULT_RUNTIME_STATE_PATHS,
) -> RuntimeStateIgnorePostureGuard:
    """Return guard status for local runtime-state stores."""

    postures: list[_PathPosture] = []
    violations: list[RuntimeStatePathFinding] = []
    errors: list[str] = []
    for path in paths:
        tracked, tracked_error = _git_path_tracked(repo_root=repo_root, path=path)
        ignored, ignore_source, ignored_error = _git_path_ignored(
            repo_root=repo_root,
            path=path,
        )
        errors.extend(error for error in (tracked_error, ignored_error) if error)
        posture = _PathPosture(
            path=path,
            tracked=tracked,
            ignored=ignored,
            ignore_source=ignore_source,
        )
        postures.append(posture)
        if tracked or not ignored:
            violations.append(_finding_for(posture))

    ok = not violations and not errors
    return RuntimeStateIgnorePostureGuard(
        guard_id=RUNTIME_STATE_IGNORE_POSTURE_GUARD_ID,
        ok=ok,
        report_only=False,
        would_fail=not ok,
        checked_path_count=len(postures),
        ignored_path_count=sum(1 for posture in postures if posture.ignored),
        tracked_path_count=sum(1 for posture in postures if posture.tracked),
        violation_count=len(violations),
        violations=tuple(violation.to_dict() for violation in violations),
        errors=tuple(errors),
    )


def _finding_for(posture: _PathPosture) -> RuntimeStatePathFinding:
    details: list[str] = []
    if posture.tracked:
        details.append("path is tracked by git and can dirty startup gates")
    if not posture.ignored:
        details.append("path is not covered by git ignore rules")
    return RuntimeStatePathFinding(
        path=posture.path,
        tracked=posture.tracked,
        ignored=posture.ignored,
        ignore_source=posture.ignore_source,
        detail="; ".join(details),
    )


def _git_path_tracked(*, repo_root: Path, path: str) -> tuple[bool, str]:
    completed = _run_git(repo_root, "ls-files", "--error-unmatch", "--", path)
    if completed.returncode == 0:
        return True, ""
    if completed.returncode == 1:
        return False, ""
    return False, _git_error("git-ls-files-failed", path, completed)


def _git_path_ignored(*, repo_root: Path, path: str) -> tuple[bool, str, str]:
    completed = _run_git(repo_root, "check-ignore", "--no-index", "-v", "--", path)
    if completed.returncode == 0:
        source = _ignore_source(completed.stdout)
        return True, source, ""
    if completed.returncode == 1:
        return False, "", ""
    return False, "", _git_error("git-check-ignore-failed", path, completed)


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _ignore_source(stdout: str) -> str:
    first_line = next((line for line in stdout.splitlines() if line.strip()), "")
    return first_line.split("\t", 1)[0].strip()


def _git_error(
    prefix: str,
    path: str,
    completed: subprocess.CompletedProcess[str],
) -> str:
    stderr = (completed.stderr or completed.stdout).strip()
    return f"{prefix}:{path}:exit={completed.returncode}:{stderr}"


def _render_md(report: RuntimeStateIgnorePostureGuard) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- report_only: {report.report_only}")
    lines.append(f"- would_fail: {report.would_fail}")
    lines.append(f"- checked_path_count: {report.checked_path_count}")
    lines.append(f"- ignored_path_count: {report.ignored_path_count}")
    lines.append(f"- tracked_path_count: {report.tracked_path_count}")
    lines.append(f"- violation_count: {report.violation_count}")
    if report.errors:
        lines.append("")
        lines.append("## Errors")
        lines.extend(f"- {error}" for error in report.errors)
    if report.violations:
        lines.append("")
        lines.append("## Violations")
        for violation in report.violations:
            if not isinstance(violation, dict):
                continue
            lines.append(
                "- "
                f"`{violation.get('path')}`: "
                f"{violation.get('detail')} "
                f"(ignore_source={violation.get('ignore_source') or 'none'})"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = evaluate_runtime_state_ignore_posture()
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print(_render_md(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
