"""Shared stale-path scanning helpers for tooling governance."""

from __future__ import annotations

import re
import subprocess
from collections import defaultdict

from .config import REPO_ROOT
from .script_catalog import LEGACY_CHECK_SCRIPT_REWRITES

PATH_AUDIT_EXCLUDED_PREFIXES = ("dev/archive/",)
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


def _tracked_repo_paths() -> tuple[list[str], str | None]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        error = (completed.stderr or completed.stdout).strip() or "git ls-files failed"
        return [], error
    paths = [value for value in completed.stdout.split("\0") if value.strip()]
    return paths, None


def _include_path(relative_path: str) -> bool:
    return not any(relative_path.startswith(prefix) for prefix in PATH_AUDIT_EXCLUDED_PREFIXES)


def _include_workspace_contract_path(relative_path: str) -> bool:
    return _include_path(relative_path) and (
        relative_path.startswith(WORKSPACE_CONTRACT_SCAN_PREFIXES)
        or relative_path in WORKSPACE_CONTRACT_SCAN_FILES
    )


def _scan_text_for_legacy_references(relative_path: str, text: str) -> list[dict]:
    violations: list[dict] = []
    lines = text.splitlines()
    for legacy_path, replacement_path in LEGACY_CHECK_SCRIPT_REWRITES.items():
        for lineno, line in enumerate(lines, start=1):
            if legacy_path not in line:
                continue
            violations.append(
                {
                    "file": relative_path,
                    "line": lineno,
                    "legacy_path": legacy_path,
                    "replacement_path": replacement_path,
                    "line_text": line.strip(),
                }
            )
    return violations


def _scan_text_for_workspace_contract_references(relative_path: str, text: str) -> list[dict]:
    violations: list[dict] = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, start=1):
        for rule in WORKSPACE_CONTRACT_RULES:
            if not rule["pattern"].search(line):
                continue
            violations.append(
                {
                    "file": relative_path,
                    "line": lineno,
                    "legacy_path": rule["token"],
                    "replacement_path": rule["replacement"],
                    "line_text": line.strip(),
                    "violation_type": "workspace_contract",
                    "rule_id": rule["id"],
                }
            )
    return violations


def scan_legacy_path_references() -> dict:
    """Scan tracked files for stale legacy check-script paths."""
    tracked_paths, list_error = _tracked_repo_paths()
    if list_error:
        return {
            "ok": False,
            "error": list_error,
            "checked_file_count": 0,
            "excluded_prefixes": list(PATH_AUDIT_EXCLUDED_PREFIXES),
            "rules": LEGACY_CHECK_SCRIPT_REWRITES,
            "violations": [],
        }

    violations: list[dict] = []
    checked_file_count = 0

    for relative_path in tracked_paths:
        if not _include_path(relative_path):
            continue
        target = REPO_ROOT / relative_path
        try:
            text = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        checked_file_count += 1
        violations.extend(_scan_text_for_legacy_references(relative_path, text))

    return {
        "ok": not violations,
        "checked_file_count": checked_file_count,
        "excluded_prefixes": list(PATH_AUDIT_EXCLUDED_PREFIXES),
        "rules": LEGACY_CHECK_SCRIPT_REWRITES,
        "violations": violations,
    }


def scan_workspace_contract_references() -> dict:
    """Scan workflow/governance files for stale workspace-root path contracts."""
    tracked_paths, list_error = _tracked_repo_paths()
    if list_error:
        return {
            "ok": False,
            "error": list_error,
            "checked_file_count": 0,
            "excluded_prefixes": list(PATH_AUDIT_EXCLUDED_PREFIXES),
            "scan_prefixes": list(WORKSPACE_CONTRACT_SCAN_PREFIXES),
            "scan_files": list(WORKSPACE_CONTRACT_SCAN_FILES),
            "rules": [
                {"id": rule["id"], "token": rule["token"], "replacement": rule["replacement"]}
                for rule in WORKSPACE_CONTRACT_RULES
            ],
            "violations": [],
        }

    violations: list[dict] = []
    checked_file_count = 0
    for relative_path in tracked_paths:
        if not _include_workspace_contract_path(relative_path):
            continue
        target = REPO_ROOT / relative_path
        try:
            text = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        checked_file_count += 1
        violations.extend(_scan_text_for_workspace_contract_references(relative_path, text))

    return {
        "ok": not violations,
        "checked_file_count": checked_file_count,
        "excluded_prefixes": list(PATH_AUDIT_EXCLUDED_PREFIXES),
        "scan_prefixes": list(WORKSPACE_CONTRACT_SCAN_PREFIXES),
        "scan_files": list(WORKSPACE_CONTRACT_SCAN_FILES),
        "rules": [
            {"id": rule["id"], "token": rule["token"], "replacement": rule["replacement"]}
            for rule in WORKSPACE_CONTRACT_RULES
        ],
        "violations": violations,
    }


def scan_path_audit_references() -> dict:
    """Aggregate legacy check-script and workspace-contract path scans."""
    legacy_scan = scan_legacy_path_references()
    workspace_scan = scan_workspace_contract_references()

    legacy_violations = list(legacy_scan.get("violations", []))
    workspace_violations = list(workspace_scan.get("violations", []))
    violations = [*legacy_violations, *workspace_violations]

    errors: list[str] = []
    if legacy_scan.get("error"):
        errors.append(f"legacy:{legacy_scan['error']}")
    if workspace_scan.get("error"):
        errors.append(f"workspace:{workspace_scan['error']}")

    legacy_checked_file_count = int(legacy_scan.get("checked_file_count", 0))
    workspace_checked_file_count = int(workspace_scan.get("checked_file_count", 0))
    return {
        "ok": bool(legacy_scan.get("ok", False)) and bool(workspace_scan.get("ok", False)),
        "error": "; ".join(errors) if errors else None,
        "checked_file_count": legacy_checked_file_count + workspace_checked_file_count,
        "unique_checked_file_count": legacy_checked_file_count,
        "legacy_checked_file_count": legacy_checked_file_count,
        "workspace_checked_file_count": workspace_checked_file_count,
        "excluded_prefixes": list(PATH_AUDIT_EXCLUDED_PREFIXES),
        "legacy_rules": legacy_scan.get("rules", {}),
        "workspace_rules": workspace_scan.get("rules", []),
        "legacy_violation_count": len(legacy_violations),
        "workspace_contract_violation_count": len(workspace_violations),
        "violations": violations,
    }


def rewrite_legacy_path_references(*, dry_run: bool) -> dict:
    """Rewrite legacy check-script paths in tracked files."""
    tracked_paths, list_error = _tracked_repo_paths()
    if list_error:
        return {
            "ok": False,
            "error": list_error,
            "dry_run": dry_run,
            "checked_file_count": 0,
            "changed_file_count": 0,
            "replacement_count": 0,
            "changes": [],
            "post_scan": None,
        }

    checked_file_count = 0
    replacement_count = 0
    changes: list[dict] = []

    for relative_path in tracked_paths:
        if not _include_path(relative_path):
            continue
        target = REPO_ROOT / relative_path
        try:
            original = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        checked_file_count += 1

        updated = original
        replacement_counts_by_rule: dict[str, int] = defaultdict(int)
        for legacy_path, replacement_path in LEGACY_CHECK_SCRIPT_REWRITES.items():
            count = updated.count(legacy_path)
            if count == 0:
                continue
            updated = updated.replace(legacy_path, replacement_path)
            replacement_counts_by_rule[legacy_path] += count
            replacement_count += count

        if updated == original:
            continue

        if not dry_run:
            target.write_text(updated, encoding="utf-8")

        changes.append(
            {
                "file": relative_path,
                "replacements": sum(replacement_counts_by_rule.values()),
                "replacements_by_rule": dict(replacement_counts_by_rule),
            }
        )

    post_scan = scan_legacy_path_references()
    return {
        "ok": bool(post_scan.get("ok", False)),
        "dry_run": dry_run,
        "checked_file_count": checked_file_count,
        "changed_file_count": len(changes),
        "replacement_count": replacement_count,
        "changes": changes,
        "post_scan": post_scan,
    }
