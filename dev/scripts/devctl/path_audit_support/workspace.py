"""Workspace-contract scan helpers for path-audit governance."""

from __future__ import annotations

import re
from pathlib import Path

WORKSPACE_CONTRACT_SCAN_PREFIXES = (".github/workflows/",)
WORKSPACE_CONTRACT_SCAN_FILES = (
    ".github/dependabot.yml",
    ".github/CODEOWNERS",
    "AGENTS.md",
    "dev/scripts/checks/check_agents_contract.py",
)
WORKSPACE_CONTRACT_RULES = (
    {
        "id": "runtime_src_glob",
        "token": "src/**",
        "replacement": "rust/src/**",
        "pattern": re.compile(r"(?<!rust/)src/\*\*"),
    },
    {
        "id": "working_directory_src",
        "token": "working-directory: src",
        "replacement": "working-directory: rust",
        "pattern": re.compile(r"^\s*working-directory:\s*['\"]?src['\"]?\s*$"),
    },
    {
        "id": "dependabot_src_directory",
        "token": "directory: /src",
        "replacement": "directory: /rust",
        "pattern": re.compile(r"^\s*directory:\s*['\"]?/src['\"]?\s*$"),
    },
    {
        "id": "codeowners_src_root",
        "token": "/src/",
        "replacement": "/rust/src/",
        "pattern": re.compile(r"^\s*/src/\s+@"),
    },
)


def _workspace_contract_violation(
    *,
    relative_path: str,
    lineno: int,
    legacy_path: str,
    replacement_path: str,
    line_text: str,
    rule_id: str,
) -> dict:
    """Build one workspace-contract violation row without a large dict literal."""
    violation = {
        "file": relative_path,
        "line": lineno,
        "legacy_path": legacy_path,
    }
    violation["replacement_path"] = replacement_path
    violation["line_text"] = line_text
    violation["violation_type"] = "workspace_contract"
    violation["rule_id"] = rule_id
    return violation


def workspace_rule_entries() -> list[dict[str, str]]:
    """Render workspace-contract rules as serializable rows."""
    return [
        {
            "id": rule["id"],
            "token": rule["token"],
            "replacement": rule["replacement"],
        }
        for rule in WORKSPACE_CONTRACT_RULES
    ]


def _scan_text_for_workspace_contract_references(
    relative_path: str, text: str
) -> list[dict]:
    violations: list[dict] = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, start=1):
        for rule in WORKSPACE_CONTRACT_RULES:
            if not rule["pattern"].search(line):
                continue
            violations.append(
                _workspace_contract_violation(
                    relative_path=relative_path,
                    lineno=lineno,
                    legacy_path=rule["token"],
                    replacement_path=rule["replacement"],
                    line_text=line.strip(),
                    rule_id=rule["id"],
                )
            )
    return violations


def should_scan_workspace_contract_path(
    relative_path: str,
    *,
    include_path,
) -> bool:
    return include_path(relative_path) and (
        relative_path.startswith(WORKSPACE_CONTRACT_SCAN_PREFIXES)
        or relative_path in WORKSPACE_CONTRACT_SCAN_FILES
    )


def scan_workspace_contract_references(
    *,
    repo_root: Path,
    tracked_paths: list[str],
    list_error: str | None,
    include_path,
    workspace_scan_report,
) -> dict:
    """Scan workflow/governance files for stale workspace-root path contracts."""
    if list_error:
        report = workspace_scan_report(ok=False, checked_file_count=0, violations=[])
        report["error"] = list_error
        return report

    violations: list[dict] = []
    checked_file_count = 0
    for relative_path in tracked_paths:
        if not should_scan_workspace_contract_path(
            relative_path,
            include_path=include_path,
        ):
            continue
        target = repo_root / relative_path
        try:
            text = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        checked_file_count += 1
        violations.extend(
            _scan_text_for_workspace_contract_references(relative_path, text)
        )

    return workspace_scan_report(
        ok=not violations,
        checked_file_count=checked_file_count,
        violations=violations,
    )
