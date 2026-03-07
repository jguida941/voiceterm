"""Canonical command-bundle registry for tooling checks and routing.

Bundle commands are defined here as the single execution authority.
Docs may render these lists for reference, but runtime/check scripts should
consume this registry directly.

Bundles use a composition model: shared check layers are defined once and
assembled per bundle to eliminate duplication (DRY).
"""

from __future__ import annotations

from typing import Final

BUNDLE_AUTHORITY_PATH: Final[str] = "dev/scripts/devctl/bundle_registry.py"
AGENTS_BUNDLE_SECTION_HEADING: Final[str] = "## Command bundles (rendered reference)"
AGENTS_BUNDLE_SECTION_INTRO_LINES: Final[tuple[str, ...]] = (
    f"Canonical command authority lives in `{BUNDLE_AUTHORITY_PATH}`.",
    "The bundle blocks below are rendered reference for human read-through and must",
    "stay aligned with the registry.",
)

# ---------------------------------------------------------------------------
# Shared command layers (compose into bundles below)
# ---------------------------------------------------------------------------

# Guard checks shared across all non-bootstrap bundles.
_GUARD_CHECKS: Final[tuple[str, ...]] = (
    "python3 dev/scripts/checks/check_active_plan_sync.py",
    "python3 dev/scripts/checks/check_multi_agent_sync.py",
    "python3 dev/scripts/checks/check_cli_flags_parity.py",
    "python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120",
    "python3 dev/scripts/checks/check_code_shape.py",
    "python3 dev/scripts/checks/check_workflow_shell_hygiene.py",
    "python3 dev/scripts/checks/check_workflow_action_pinning.py",
    "python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations",
    "python3 dev/scripts/checks/check_compat_matrix.py",
    "python3 dev/scripts/checks/compat_matrix_smoke.py",
    "python3 dev/scripts/checks/check_naming_consistency.py",
    "python3 dev/scripts/checks/check_rust_test_shape.py",
    "python3 dev/scripts/checks/check_rust_lint_debt.py",
    "python3 dev/scripts/checks/check_rust_best_practices.py",
    "python3 dev/scripts/checks/check_rust_runtime_panic_policy.py",
    "markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md",
    "find . -maxdepth 1 -type f -name '--*'",
)

# Governance checks used by tooling and release bundles.
_GOVERNANCE_CHECKS: Final[tuple[str, ...]] = (
    "python3 dev/scripts/checks/check_agents_contract.py",
    "python3 dev/scripts/checks/check_release_version_parity.py",
    "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
)

# Orchestration status commands used by tooling, release, and post-push bundles.
_ORCHESTRATE_COMMANDS: Final[tuple[str, ...]] = (
    "python3 dev/scripts/devctl.py orchestrate-status --format md",
    "python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md",
)

# ---------------------------------------------------------------------------
# Bundle definitions (composed from shared layers)
# ---------------------------------------------------------------------------

BUNDLE_REGISTRY: Final[dict[str, tuple[str, ...]]] = {
    "bundle.bootstrap": (
        "git status --short",
        "git branch --show-current",
        "git remote -v",
        "git log --oneline --decorate -n 10",
        "sed -n '1,220p' dev/active/INDEX.md",
        "python3 dev/scripts/devctl.py list",
        "find . -maxdepth 1 -type f -name '--*'",
    ),
    "bundle.runtime": (
        "python3 dev/scripts/devctl.py check --profile ci",
        "python3 dev/scripts/devctl.py docs-check --user-facing",
        "python3 dev/scripts/devctl.py hygiene",
        *_GUARD_CHECKS,
    ),
    "bundle.docs": (
        "python3 dev/scripts/devctl.py docs-check --user-facing",
        "python3 dev/scripts/devctl.py hygiene",
        *_GUARD_CHECKS,
    ),
    "bundle.tooling": (
        "python3 dev/scripts/devctl.py docs-check --strict-tooling",
        "python3 dev/scripts/devctl.py hygiene --strict-warnings",
        *_ORCHESTRATE_COMMANDS,
        *_GOVERNANCE_CHECKS,
        *_GUARD_CHECKS,
    ),
    "bundle.release": (
        "python3 dev/scripts/devctl.py check --profile release",
        "python3 dev/scripts/devctl.py docs-check --user-facing --strict",
        "python3 dev/scripts/devctl.py docs-check --strict-tooling",
        "python3 dev/scripts/devctl.py hygiene --strict-warnings",
        *_ORCHESTRATE_COMMANDS,
        *_GOVERNANCE_CHECKS,
        "CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master",
        "CI=1 python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master",
        *_GUARD_CHECKS,
    ),
    "bundle.post-push": (
        "git status",
        "git log --oneline --decorate -n 10",
        "python3 dev/scripts/devctl.py status --ci --require-ci --format md",
        *_ORCHESTRATE_COMMANDS,
        "python3 dev/scripts/devctl.py docs-check --user-facing --since-ref origin/develop",
        "python3 dev/scripts/devctl.py hygiene",
        "python3 dev/scripts/checks/check_active_plan_sync.py",
        "python3 dev/scripts/checks/check_multi_agent_sync.py",
        "python3 dev/scripts/checks/check_cli_flags_parity.py",
        "python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120",
        "python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop",
        "python3 dev/scripts/checks/check_workflow_shell_hygiene.py",
        "python3 dev/scripts/checks/check_workflow_action_pinning.py",
        "python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations",
        "python3 dev/scripts/checks/check_compat_matrix.py",
        "python3 dev/scripts/checks/compat_matrix_smoke.py",
        "python3 dev/scripts/checks/check_naming_consistency.py",
        "python3 dev/scripts/checks/check_rust_test_shape.py --since-ref origin/develop",
        "python3 dev/scripts/checks/check_rust_lint_debt.py --since-ref origin/develop",
        "python3 dev/scripts/checks/check_rust_best_practices.py --since-ref origin/develop",
        "python3 dev/scripts/checks/check_rust_runtime_panic_policy.py --since-ref origin/develop",
        "find . -maxdepth 1 -type f -name '--*'",
    ),
}


def bundle_names() -> tuple[str, ...]:
    """Return bundle names in registry order."""
    return tuple(BUNDLE_REGISTRY.keys())


def get_bundle_commands(bundle_name: str) -> list[str]:
    """Return commands for a registered bundle.

    Raises:
        KeyError: if bundle_name is not in the registry.
    """

    commands = BUNDLE_REGISTRY.get(bundle_name)
    if commands is None:
        raise KeyError(bundle_name)
    return list(commands)


def render_bundle_reference_markdown(bundle_name: str) -> str:
    """Render one bundle block in AGENTS markdown style."""
    commands = get_bundle_commands(bundle_name)
    lines = [f"### `{bundle_name}`", "", "```bash", *commands, "```"]
    return "\n".join(lines)


def render_all_bundle_reference_markdown() -> str:
    """Render all bundles in AGENTS markdown style."""
    return "\n\n".join(
        render_bundle_reference_markdown(bundle_name) for bundle_name in bundle_names()
    )


def render_agents_bundle_section_markdown() -> str:
    """Render the full AGENTS command-bundle section."""
    lines = [
        AGENTS_BUNDLE_SECTION_HEADING,
        "",
        *AGENTS_BUNDLE_SECTION_INTRO_LINES,
        "",
        render_all_bundle_reference_markdown(),
    ]
    return "\n".join(lines)
