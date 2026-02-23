"""Shared stale-path scanning helpers for tooling governance."""

from __future__ import annotations

import subprocess
from collections import defaultdict

from .config import REPO_ROOT
from .script_catalog import LEGACY_CHECK_SCRIPT_REWRITES

PATH_AUDIT_EXCLUDED_PREFIXES = ("dev/archive/",)


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
