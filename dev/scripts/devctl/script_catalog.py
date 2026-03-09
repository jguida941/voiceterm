"""Canonical script path registry for devctl and tooling checks."""

from __future__ import annotations

from pathlib import Path

from .config import REPO_ROOT

CHECKS_DIR = "dev/scripts/checks"

CHECK_SCRIPT_FILES = {
    "active_plan_sync": "check_active_plan_sync.py",
    "architecture_surface_sync": "check_architecture_surface_sync.py",
    "agents_contract": "check_agents_contract.py",
    "agents_bundle_render": "check_agents_bundle_render.py",
    "bootstrap": "check_bootstrap.py",
    "bundle_registry_dry": "check_bundle_registry_dry.py",
    "bundle_workflow_parity": "check_bundle_workflow_parity.py",
    "cli_flags_parity": "check_cli_flags_parity.py",
    "clippy_high_signal": "check_clippy_high_signal.py",
    "duplication_audit": "check_duplication_audit.py",
    "duplication_audit_support": "check_duplication_audit_support.py",
    "duplicate_types": "check_duplicate_types.py",
    "guard_enforcement_inventory": "check_guard_enforcement_inventory.py",
    "python_broad_except": "check_python_broad_except.py",
    "python_subprocess_policy": "check_python_subprocess_policy.py",
    "compat_matrix": "check_compat_matrix.py",
    "compat_matrix_smoke": "compat_matrix_smoke.py",
    "code_shape": "check_code_shape.py",
    "coderabbit_gate": "check_coderabbit_gate.py",
    "coderabbit_ralph_gate": "check_coderabbit_ralph_gate.py",
    "ide_provider_isolation": "check_ide_provider_isolation.py",
    "naming_consistency": "check_naming_consistency.py",
    "multi_agent_sync": "check_multi_agent_sync.py",
    "markdown_metadata_header": "check_markdown_metadata_header.py",
    "mutation_score": "check_mutation_score.py",
    "publication_sync": "check_publication_sync.py",
    "release_version_parity": "check_release_version_parity.py",
    "repo_url_parity": "check_repo_url_parity.py",
    "review_channel_bridge": "check_review_channel_bridge.py",
    "rust_best_practices": "check_rust_best_practices.py",
    "rust_audit_patterns": "check_rust_audit_patterns.py",
    "rust_runtime_panic_policy": "check_rust_runtime_panic_policy.py",
    "rust_security_footguns": "check_rust_security_footguns.py",
    "rust_lint_debt": "check_rust_lint_debt.py",
    "function_duplication": "check_function_duplication.py",
    "structural_complexity": "check_structural_complexity.py",
    "rust_test_shape": "check_rust_test_shape.py",
    "rustsec_policy": "check_rustsec_policy.py",
    "screenshot_integrity": "check_screenshot_integrity.py",
    "test_coverage_parity": "check_test_coverage_parity.py",
    "workflow_action_pinning": "check_workflow_action_pinning.py",
    "workflow_shell_hygiene": "check_workflow_shell_hygiene.py",
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
