"""Canonical script path registry for devctl and tooling checks."""

from __future__ import annotations

from pathlib import Path

from .config import REPO_ROOT

CHECKS_DIR = "dev/scripts/checks"

CHECK_SCRIPT_FILES = {
    "active_plan_sync": "check_active_plan_sync.py",
    "agents_contract": "check_agents_contract.py",
    "cli_flags_parity": "check_cli_flags_parity.py",
    "code_shape": "check_code_shape.py",
    "coderabbit_gate": "check_coderabbit_gate.py",
    "coderabbit_ralph_gate": "check_coderabbit_ralph_gate.py",
    "multi_agent_sync": "check_multi_agent_sync.py",
    "mutation_score": "check_mutation_score.py",
    "release_version_parity": "check_release_version_parity.py",
    "rust_best_practices": "check_rust_best_practices.py",
    "rust_audit_patterns": "check_rust_audit_patterns.py",
    "rust_security_footguns": "check_rust_security_footguns.py",
    "rust_lint_debt": "check_rust_lint_debt.py",
    "rustsec_policy": "check_rustsec_policy.py",
    "screenshot_integrity": "check_screenshot_integrity.py",
}

CHECK_SCRIPT_RELATIVE_PATHS = {
    name: f"{CHECKS_DIR}/{filename}" for name, filename in CHECK_SCRIPT_FILES.items()
}

CHECK_SCRIPT_PATHS = {
    name: REPO_ROOT / relative for name, relative in CHECK_SCRIPT_RELATIVE_PATHS.items()
}

LEGACY_CHECK_SCRIPT_REWRITES = {
    f"dev/scripts/{filename}": relative
    for filename, relative in (
        (filename, f"{CHECKS_DIR}/{filename}")
        for filename in CHECK_SCRIPT_FILES.values()
    )
}


def check_script_relative_path(name: str) -> str:
    """Return a check script's repository-relative path."""
    try:
        return CHECK_SCRIPT_RELATIVE_PATHS[name]
    except KeyError as exc:
        raise KeyError(f"unknown check script id: {name}") from exc


def check_script_path(name: str) -> Path:
    """Return a check script's absolute filesystem path."""
    try:
        return CHECK_SCRIPT_PATHS[name]
    except KeyError as exc:
        raise KeyError(f"unknown check script id: {name}") from exc


def check_script_cmd(name: str, *args: str) -> list[str]:
    """Return a python command list for one check script."""
    return ["python3", check_script_relative_path(name), *args]
