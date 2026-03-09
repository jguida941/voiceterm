"""Reusable audit helpers for `devctl hygiene`.

Use these helpers when you need to add or change hygiene rules.
Keeping them separate from the command runner keeps the checks easier to read.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

from ..publication_sync import (
    DEFAULT_PUBLICATION_SYNC_REGISTRY_REL,
    build_publication_sync_report,
)
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


def _collect_top_level_script_inventory(scripts_dir: Path, readme_text: str) -> Dict:
    """Collect top-level script names and README coverage gaps."""
    top_level_scripts = sorted(
        path.name
        for path in scripts_dir.iterdir()
        if path.is_file() and path.name != "README.md"
    )
    return {
        "top_level_scripts": top_level_scripts,
        "undocumented": [name for name in top_level_scripts if name not in readme_text],
    }


def _collect_check_script_inventory(
    repo_root: Path,
    checks_dir: Path,
    readme_text: str,
) -> Dict:
    """Collect check-script docs and catalog reconciliation details."""
    catalog_path = repo_root / "dev/scripts/devctl/script_catalog.py"
    catalog_contract_available = catalog_path.is_file()
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
    return {
        "check_scripts": check_scripts,
        "catalog_check_scripts": catalog_check_scripts,
        "undocumented_checks": [path for path in check_scripts if path not in readme_text],
        "unregistered_checks": (
            [
                path
                for path in filesystem_check_scripts
                if path not in catalog_check_script_set
            ]
            if catalog_contract_available
            else []
        ),
        "stale_catalog_checks": (
            [path for path in catalog_check_scripts if not (repo_root / path).is_file()]
            if catalog_contract_available
            else []
        ),
    }


def _collect_pycache_inventory(repo_root: Path, scripts_dir: Path) -> Dict:
    """Collect Python cache directories and split ignored vs actionable paths."""
    pycache_dirs = sorted(
        str(path.relative_to(repo_root))
        for path in scripts_dir.rglob("__pycache__")
        if path.is_dir()
    )
    ignored_pycache_dirs = [
        path for path in pycache_dirs if _is_git_ignored(repo_root, path)
    ]
    ignored_pycache_set = set(ignored_pycache_dirs)
    return {
        "pycache_dirs": pycache_dirs,
        "ignored_pycache_dirs": ignored_pycache_dirs,
        "actionable_pycache_dirs": [
            path for path in pycache_dirs if path not in ignored_pycache_set
        ],
    }


def _build_script_audit_messages(
    undocumented: List[str],
    undocumented_checks: List[str],
    unregistered_checks: List[str],
    stale_catalog_checks: List[str],
    actionable_pycache_dirs: List[str],
) -> Dict:
    """Build the stable error and warning payload for script audits."""
    errors: List[str] = []
    warnings: List[str] = []
    error_groups = (
        (
            undocumented,
            "Top-level scripts not documented in dev/scripts/README.md: ",
        ),
        (
            undocumented_checks,
            "Check scripts not documented in dev/scripts/README.md: ",
        ),
        (
            unregistered_checks,
            "Check scripts missing from dev/scripts/devctl/script_catalog.py: ",
        ),
        (
            stale_catalog_checks,
            "Script catalog entries reference missing check scripts: ",
        ),
    )
    for paths, prefix in error_groups:
        if paths:
            errors.append(prefix + ", ".join(paths))
    if actionable_pycache_dirs:
        warnings.append(
            "Python cache directories present in repo tree: "
            + ", ".join(actionable_pycache_dirs)
        )
    return {"errors": errors, "warnings": warnings}


def audit_scripts(repo_root: Path) -> Dict:
    """Check script inventory docs and cache-dir hygiene."""
    scripts_dir = repo_root / "dev/scripts"
    checks_dir = scripts_dir / "checks"
    readme_text = (scripts_dir / "README.md").read_text(encoding="utf-8")
    top_level_inventory = _collect_top_level_script_inventory(scripts_dir, readme_text)
    check_inventory = _collect_check_script_inventory(
        repo_root,
        checks_dir,
        readme_text,
    )
    pycache_inventory = _collect_pycache_inventory(repo_root, scripts_dir)
    messages = _build_script_audit_messages(
        top_level_inventory["undocumented"],
        check_inventory["undocumented_checks"],
        check_inventory["unregistered_checks"],
        check_inventory["stale_catalog_checks"],
        pycache_inventory["actionable_pycache_dirs"],
    )
    return {
        "top_level_scripts": top_level_inventory["top_level_scripts"],
        "undocumented": top_level_inventory["undocumented"],
        "check_scripts": check_inventory["check_scripts"],
        "catalog_check_scripts": check_inventory["catalog_check_scripts"],
        "undocumented_checks": check_inventory["undocumented_checks"],
        "unregistered_checks": check_inventory["unregistered_checks"],
        "stale_catalog_checks": check_inventory["stale_catalog_checks"],
        "pycache_dirs": pycache_inventory["pycache_dirs"],
        "ignored_pycache_dirs": pycache_inventory["ignored_pycache_dirs"],
        "actionable_pycache_dirs": pycache_inventory["actionable_pycache_dirs"],
        "errors": messages["errors"],
        "warnings": messages["warnings"],
    }


def audit_publication_sync(repo_root: Path) -> Dict:
    """Report tracked external publication drift without blocking normal hygiene lanes."""
    registry_path = repo_root / DEFAULT_PUBLICATION_SYNC_REGISTRY_REL
    if not registry_path.is_file():
        return {
            "registry_path": DEFAULT_PUBLICATION_SYNC_REGISTRY_REL,
            "publication_count": 0,
            "stale_publication_count": 0,
            "publications": [],
            "errors": [],
            "warnings": [],
            "notices": [],
        }

    report = build_publication_sync_report(
        repo_root=repo_root,
        registry_path=registry_path,
        allow_missing_registry=False,
    )
    errors = list(report.get("errors", []))
    warnings: List[str] = []
    notices: List[str] = []

    for item in report.get("publications", []):
        for message in item.get("errors", []):
            errors.append(f"publication `{item['id']}`: {message}")
        if not item.get("stale"):
            continue
        impacted_paths = item.get("impacted_paths", [])
        preview = ", ".join(impacted_paths[:5]) if impacted_paths else "none"
        remaining = len(impacted_paths) - 5
        if remaining > 0:
            preview = f"{preview}, ... {remaining} more"
        notices.append(
            "Publication drift detected for "
            f"`{item['id']}` ({item['public_url']}). "
            f"Impacted watched paths since {item['source_ref'][:12]}: {preview}. "
            "Update the external publication and then record the new source ref with "
            "`python3 dev/scripts/devctl.py publication-sync --publication "
            f"{item['id']} --record-source-ref HEAD --record-external-ref <external-site-commit>`."
        )

    return {
        "registry_path": report.get("registry_path", DEFAULT_PUBLICATION_SYNC_REGISTRY_REL),
        "publication_count": report.get("publication_count", 0),
        "stale_publication_count": report.get("stale_publication_count", 0),
        "publications": report.get("publications", []),
        "errors": errors,
        "warnings": warnings,
        "notices": notices,
    }
