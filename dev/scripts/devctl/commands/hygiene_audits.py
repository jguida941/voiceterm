"""Reusable audit helpers for `devctl hygiene`.

Use these helpers when you need to add or change hygiene rules.
Keeping them separate from the command runner keeps the checks easier to read.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

from ..script_catalog import CHECK_SCRIPT_RELATIVE_PATHS
from .hygiene_audits_adrs import audit_adrs
from .hygiene_audits_archive import audit_archive


def _is_git_ignored(repo_root: Path, relative_path: str) -> bool:
    """Return True when git ignore rules cover `relative_path`."""
    if not shutil.which("git"):
        return False
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", relative_path],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def audit_scripts(repo_root: Path) -> Dict:
    """Check script inventory docs and cache-dir hygiene."""
    scripts_dir = repo_root / "dev/scripts"
    checks_dir = scripts_dir / "checks"
    catalog_path = repo_root / "dev/scripts/devctl/script_catalog.py"
    catalog_contract_available = catalog_path.is_file()
    readme_path = scripts_dir / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")

    top_level_scripts = sorted(
        path.name
        for path in scripts_dir.iterdir()
        if path.is_file() and path.name != "README.md"
    )
    undocumented = [name for name in top_level_scripts if name not in readme_text]
    filesystem_check_scripts = sorted(
        str(path.relative_to(repo_root))
        for path in checks_dir.glob("check_*.py")
        if path.is_file()
    )
    catalog_check_script_set = (
        set(CHECK_SCRIPT_RELATIVE_PATHS.values())
        if catalog_contract_available
        else set()
    )
    catalog_check_scripts = sorted(catalog_check_script_set)
    check_scripts = (
        catalog_check_scripts
        if catalog_contract_available
        else filesystem_check_scripts
    )
    undocumented_checks = [path for path in check_scripts if path not in readme_text]
    unregistered_checks = (
        [
            path
            for path in filesystem_check_scripts
            if path not in catalog_check_script_set
        ]
        if catalog_contract_available
        else []
    )
    stale_catalog_checks = (
        [path for path in catalog_check_scripts if not (repo_root / path).is_file()]
        if catalog_contract_available
        else []
    )

    pycache_dirs = sorted(
        str(path.relative_to(repo_root))
        for path in scripts_dir.rglob("__pycache__")
        if path.is_dir()
    )
    ignored_pycache_dirs = [
        path for path in pycache_dirs if _is_git_ignored(repo_root, path)
    ]
    ignored_pycache_set = set(ignored_pycache_dirs)
    actionable_pycache_dirs = [
        path for path in pycache_dirs if path not in ignored_pycache_set
    ]

    errors: List[str] = []
    warnings: List[str] = []
    if undocumented:
        errors.append(
            "Top-level scripts not documented in dev/scripts/README.md: "
            + ", ".join(undocumented)
        )
    if undocumented_checks:
        errors.append(
            "Check scripts not documented in dev/scripts/README.md: "
            + ", ".join(undocumented_checks)
        )
    if unregistered_checks:
        errors.append(
            "Check scripts missing from dev/scripts/devctl/script_catalog.py: "
            + ", ".join(unregistered_checks)
        )
    if stale_catalog_checks:
        errors.append(
            "Script catalog entries reference missing check scripts: "
            + ", ".join(stale_catalog_checks)
        )
    if actionable_pycache_dirs:
        warnings.append(
            "Python cache directories present in repo tree: "
            + ", ".join(actionable_pycache_dirs)
        )

    return {
        "top_level_scripts": top_level_scripts,
        "undocumented": undocumented,
        "check_scripts": check_scripts,
        "catalog_check_scripts": catalog_check_scripts,
        "undocumented_checks": undocumented_checks,
        "unregistered_checks": unregistered_checks,
        "stale_catalog_checks": stale_catalog_checks,
        "pycache_dirs": pycache_dirs,
        "ignored_pycache_dirs": ignored_pycache_dirs,
        "actionable_pycache_dirs": actionable_pycache_dirs,
        "errors": errors,
        "warnings": warnings,
    }
