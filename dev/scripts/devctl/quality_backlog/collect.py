"""Inventory and guard-check collection for quality backlog reporting."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..config import REPO_ROOT
from .models import (
    ABSOLUTE_CHECKS,
    AbsoluteCheck,
    CheckExecution,
    InventoryRow,
)

CHECKS_DIR = REPO_ROOT / "dev/scripts/checks"
if str(CHECKS_DIR) not in sys.path:
    sys.path.insert(0, str(CHECKS_DIR))

try:
    from code_shape_policy import policy_for_path
except ModuleNotFoundError:  # pragma: no cover - package-style fallback
    from dev.scripts.checks.code_shape_policy import policy_for_path


def _run_git_lines(args: list[str]) -> list[str]:
    result = subprocess.run(
        args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise RuntimeError(f"{' '.join(args)} failed ({result.returncode}): {stderr}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _list_shape_governed_paths() -> list[Path]:
    paths: set[Path] = set()
    tracked = _run_git_lines(["git", "ls-files"])
    untracked = _run_git_lines(["git", "ls-files", "--others", "--exclude-standard"])
    for entry in (*tracked, *untracked):
        path = Path(entry)
        policy, _source = policy_for_path(path)
        if policy is not None:
            paths.add(path)
    return sorted(paths)


def _is_test_path(path: Path) -> bool:
    normalized = f"/{path.as_posix()}/"
    name = path.name
    if path.suffix == ".rs":
        return "/tests/" in normalized or name == "tests.rs" or name.endswith("_test.rs")
    if path.suffix == ".py":
        return "/tests/" in normalized or name.startswith("test_") or name.endswith("_test.py")
    return False


def _read_line_count(path: Path) -> int:
    try:
        text = (REPO_ROOT / path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
    return len(text.splitlines())


def _inventory_status(lines: int, soft_limit: int, hard_limit: int) -> str:
    if lines > hard_limit:
        return "exceeds_hard"
    if lines > soft_limit:
        return "exceeds_soft"
    if soft_limit > 0 and (lines / soft_limit) >= 0.9:
        return "near_soft"
    return "within_budget"


def _inventory_score(status: str, lines: int, soft_limit: int, hard_limit: int) -> int:
    if status == "exceeds_hard":
        return 500 + max(0, lines - hard_limit)
    if status == "exceeds_soft":
        return 250 + max(0, lines - soft_limit)
    if status == "near_soft":
        return 80
    return 0


def collect_source_inventory(*, include_tests: bool) -> dict[str, Any]:
    language_totals: dict[str, dict[str, int]] = {}
    rows: list[InventoryRow] = []
    for path in _list_shape_governed_paths():
        if not include_tests and _is_test_path(path):
            continue
        policy, policy_source = policy_for_path(path)
        if policy is None:
            continue
        full_path = REPO_ROOT / path
        if not full_path.exists() or not full_path.is_file():
            continue
        line_count = _read_line_count(path)
        status = _inventory_status(line_count, policy.soft_limit, policy.hard_limit)
        score = _inventory_score(status, line_count, policy.soft_limit, policy.hard_limit)
        pressure_pct = (
            round((line_count / policy.soft_limit) * 100.0, 2)
            if policy.soft_limit > 0
            else 0.0
        )
        row = InventoryRow(
            path=path.as_posix(),
            language=path.suffix,
            line_count=line_count,
            soft_limit=policy.soft_limit,
            hard_limit=policy.hard_limit,
            pressure_pct=pressure_pct,
            status=status,
            score=score,
            policy_source=policy_source,
        )
        rows.append(row)
        lang = language_totals.setdefault(
            path.suffix,
            {"files": 0, "total_lines": 0, "exceeds_soft": 0, "exceeds_hard": 0},
        )
        lang["files"] += 1
        lang["total_lines"] += line_count
        if status == "exceeds_soft":
            lang["exceeds_soft"] += 1
        if status == "exceeds_hard":
            lang["exceeds_hard"] += 1
    rows.sort(key=lambda row: (-row.score, -row.line_count, row.path))
    return {
        "rows": rows,
        "rows_json": [row.to_dict() for row in rows],
        "language_totals": language_totals,
    }


def run_json_check(check: AbsoluteCheck) -> CheckExecution:
    command = ["python3", check.script, "--absolute", "--format", "json"]
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    payload: dict[str, Any] = {}
    parse_error = ""
    if stdout:
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                payload = parsed
            else:
                parse_error = "expected JSON object payload"
        except json.JSONDecodeError as exc:
            parse_error = f"invalid JSON payload ({exc})"
    else:
        parse_error = "empty stdout payload"
    ok = bool(payload.get("ok", False) and result.returncode == 0)
    return CheckExecution(
        key=check.key,
        command=" ".join(command),
        exit_code=int(result.returncode),
        ok=ok,
        stderr=stderr,
        parse_error=parse_error,
        report=payload,
    )


def collect_absolute_checks() -> dict[str, Any]:
    executions = [run_json_check(check) for check in ABSOLUTE_CHECKS]
    checks = {entry.key: entry.to_dict() for entry in executions}
    warnings = [f"{entry.key}: {entry.stderr}" for entry in executions if entry.stderr]
    errors = [
        f"{entry.key}: {entry.parse_error}"
        for entry in executions
        if entry.parse_error
    ]
    return {"checks": checks, "warnings": warnings, "errors": errors}
