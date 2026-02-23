"""Shared stale-path scanning helpers for tooling governance."""

from __future__ import annotations

import subprocess

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

    return {
        "ok": not violations,
        "checked_file_count": checked_file_count,
        "excluded_prefixes": list(PATH_AUDIT_EXCLUDED_PREFIXES),
        "rules": LEGACY_CHECK_SCRIPT_REWRITES,
        "violations": violations,
    }
