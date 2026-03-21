"""Shared stale-path scanning helpers for tooling governance."""

from __future__ import annotations

import re
import subprocess
from collections import defaultdict

from .config import REPO_ROOT
from .path_audit_support.report import PathAuditAggregateReport
from .script_catalog import LEGACY_SCRIPT_PATH_REWRITES

PATH_AUDIT_EXCLUDED_PREFIXES = ("dev/archive/",)
PATH_AUDIT_EXCLUDED_FILES = (
    "bridge.md",
    "dev/scripts/devctl/script_catalog.py",
)
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


def _base_scan_report(*, ok: bool, checked_file_count: int) -> dict:
    """Build shared scan metadata without large dict literals."""
    report = {"ok": ok, "checked_file_count": checked_file_count}
    report["excluded_prefixes"] = list(PATH_AUDIT_EXCLUDED_PREFIXES)
    report["excluded_files"] = list(PATH_AUDIT_EXCLUDED_FILES)
    return report


def _legacy_scan_report(*, ok: bool, checked_file_count: int, violations: list[dict]) -> dict:
    """Build a legacy-path scan report."""
    report = _base_scan_report(ok=ok, checked_file_count=checked_file_count)
    report["rules"] = LEGACY_SCRIPT_PATH_REWRITES
    report["violations"] = violations
    return report


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


def _workspace_scan_report(
    *,
    ok: bool,
    checked_file_count: int,
    violations: list[dict],
) -> dict:
    """Build a workspace-contract scan report."""
    report = _base_scan_report(ok=ok, checked_file_count=checked_file_count)
    report["scan_prefixes"] = list(WORKSPACE_CONTRACT_SCAN_PREFIXES)
    report["scan_files"] = list(WORKSPACE_CONTRACT_SCAN_FILES)
    report["rules"] = workspace_rule_entries()
    report["violations"] = violations
    return report


def _rewrite_report(
    *,
    ok: bool,
    dry_run: bool,
    checked_file_count: int,
    changes: list[dict],
    replacement_count: int,
    post_scan: dict | None,
) -> dict:
    """Build a rewrite result payload."""
    report = _base_scan_report(ok=ok, checked_file_count=checked_file_count)
    report["dry_run"] = dry_run
    report["changed_file_count"] = len(changes)
    report["replacement_count"] = replacement_count
    report["changes"] = changes
    report["post_scan"] = post_scan
    return report


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
    return relative_path not in PATH_AUDIT_EXCLUDED_FILES and not any(
        relative_path.startswith(prefix) for prefix in PATH_AUDIT_EXCLUDED_PREFIXES
    )


def should_scan_workspace_contract_path(relative_path: str) -> bool:
    return _include_path(relative_path) and (
        relative_path.startswith(WORKSPACE_CONTRACT_SCAN_PREFIXES)
        or relative_path in WORKSPACE_CONTRACT_SCAN_FILES
    )


def scan_text_for_legacy_references(relative_path: str, text: str) -> list[dict]:
    violations: list[dict] = []
    lines = text.splitlines()
    for legacy_path, replacement_path in LEGACY_SCRIPT_PATH_REWRITES.items():
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


_scan_text_for_legacy_references = scan_text_for_legacy_references


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
    """Scan tracked files for stale legacy tooling script paths."""
    tracked_paths, list_error = _tracked_repo_paths()
    if list_error:
        report = _legacy_scan_report(ok=False, checked_file_count=0, violations=[])
        report["error"] = list_error
        return report

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
        violations.extend(scan_text_for_legacy_references(relative_path, text))

    return _legacy_scan_report(
        ok=not violations,
        checked_file_count=checked_file_count,
        violations=violations,
    )


def scan_workspace_contract_references() -> dict:
    """Scan workflow/governance files for stale workspace-root path contracts."""
    tracked_paths, list_error = _tracked_repo_paths()
    if list_error:
        report = _workspace_scan_report(ok=False, checked_file_count=0, violations=[])
        report["error"] = list_error
        return report

    violations: list[dict] = []
    checked_file_count = 0
    for relative_path in tracked_paths:
        if not should_scan_workspace_contract_path(relative_path):
            continue
        target = REPO_ROOT / relative_path
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

    return _workspace_scan_report(
        ok=not violations,
        checked_file_count=checked_file_count,
        violations=violations,
    )


def scan_path_audit_references() -> dict:
    """Aggregate legacy tooling-script and workspace-contract path scans."""
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
    report = PathAuditAggregateReport(
        ok=bool(legacy_scan.get("ok", False)) and bool(workspace_scan.get("ok", False)),
        error="; ".join(errors) if errors else None,
        checked_file_count=legacy_checked_file_count + workspace_checked_file_count,
        unique_checked_file_count=legacy_checked_file_count,
        legacy_checked_file_count=legacy_checked_file_count,
        workspace_checked_file_count=workspace_checked_file_count,
        excluded_prefixes=list(PATH_AUDIT_EXCLUDED_PREFIXES),
        excluded_files=list(PATH_AUDIT_EXCLUDED_FILES),
        legacy_rules=legacy_scan.get("rules", {}),
        workspace_rules=workspace_scan.get("rules", []),
        legacy_violation_count=len(legacy_violations),
        workspace_contract_violation_count=len(workspace_violations),
        violations=violations,
    )
    return report.to_dict()


def rewrite_legacy_path_references(*, dry_run: bool) -> dict:
    """Rewrite legacy tooling-script paths in tracked files."""
    tracked_paths, list_error = _tracked_repo_paths()
    if list_error:
        report = _rewrite_report(
            ok=False,
            dry_run=dry_run,
            checked_file_count=0,
            changes=[],
            replacement_count=0,
            post_scan=None,
        )
        report["error"] = list_error
        return report

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
        for legacy_path, replacement_path in LEGACY_SCRIPT_PATH_REWRITES.items():
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
    return _rewrite_report(
        ok=bool(post_scan.get("ok", False)),
        dry_run=dry_run,
        checked_file_count=checked_file_count,
        changes=changes,
        replacement_count=replacement_count,
        post_scan=post_scan,
    )
