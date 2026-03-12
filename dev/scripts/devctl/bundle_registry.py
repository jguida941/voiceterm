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
    "python3 dev/scripts/checks/check_python_subprocess_policy.py",
    "python3 dev/scripts/checks/check_workflow_shell_hygiene.py",
    "python3 dev/scripts/checks/check_workflow_action_pinning.py",
    "python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations",
    "python3 dev/scripts/checks/check_compat_matrix.py",
    "python3 dev/scripts/checks/compat_matrix_smoke.py",
    "python3 dev/scripts/checks/check_naming_consistency.py",
    "python3 dev/scripts/checks/check_rust_test_shape.py",
    "python3 dev/scripts/checks/check_rust_lint_debt.py",
    "python3 dev/scripts/checks/check_rust_best_practices.py",
    "python3 dev/scripts/checks/check_rust_compiler_warnings.py",
    "python3 dev/scripts/checks/check_serde_compatibility.py",
    "python3 dev/scripts/checks/check_rust_runtime_panic_policy.py",
    "python3 dev/scripts/checks/check_facade_wrappers.py",
    "python3 dev/scripts/checks/check_god_class.py",
    "python3 dev/scripts/checks/check_mobile_relay_protocol.py",
    "python3 dev/scripts/checks/check_nesting_depth.py",
    "python3 dev/scripts/checks/check_parameter_count.py",
    "python3 dev/scripts/checks/check_python_dict_schema.py",
    "python3 dev/scripts/checks/check_python_global_mutable.py",
    "python3 dev/scripts/checks/check_python_design_complexity.py",
    "python3 dev/scripts/checks/check_python_cyclic_imports.py",
    "python3 dev/scripts/checks/check_python_suppression_debt.py",
    "python3 dev/scripts/checks/check_structural_similarity.py",
    "markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md",
    "find . -maxdepth 1 -type f -name '--*'",
)

_POST_PUSH_DIFF_GUARD_COMMANDS: Final[frozenset[str]] = frozenset(
    {
        "python3 dev/scripts/checks/check_code_shape.py",
        "python3 dev/scripts/checks/check_python_subprocess_policy.py",
        "python3 dev/scripts/checks/check_rust_test_shape.py",
        "python3 dev/scripts/checks/check_rust_lint_debt.py",
        "python3 dev/scripts/checks/check_rust_best_practices.py",
        "python3 dev/scripts/checks/check_rust_compiler_warnings.py",
        "python3 dev/scripts/checks/check_serde_compatibility.py",
        "python3 dev/scripts/checks/check_rust_runtime_panic_policy.py",
        "python3 dev/scripts/checks/check_facade_wrappers.py",
        "python3 dev/scripts/checks/check_god_class.py",
        "python3 dev/scripts/checks/check_mobile_relay_protocol.py",
        "python3 dev/scripts/checks/check_nesting_depth.py",
        "python3 dev/scripts/checks/check_parameter_count.py",
        "python3 dev/scripts/checks/check_python_dict_schema.py",
        "python3 dev/scripts/checks/check_python_global_mutable.py",
        "python3 dev/scripts/checks/check_python_design_complexity.py",
        "python3 dev/scripts/checks/check_python_cyclic_imports.py",
        "python3 dev/scripts/checks/check_python_suppression_debt.py",
        "python3 dev/scripts/checks/check_structural_similarity.py",
    }
)

# Governance checks shared by tooling and release bundles.
_SHARED_GOVERNANCE_CHECKS: Final[tuple[str, ...]] = (
    "python3 dev/scripts/checks/check_agents_contract.py",
    "python3 dev/scripts/checks/check_release_version_parity.py",
    "python3 dev/scripts/checks/check_repo_url_parity.py",
    "python3 dev/scripts/checks/check_guard_enforcement_inventory.py",
    "python3 dev/scripts/checks/check_architecture_surface_sync.py",
    "python3 dev/scripts/checks/check_bundle_registry_dry.py",
    "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
    "python3 dev/scripts/checks/check_review_channel_bridge.py",
)

# Publication drift only blocks release lanes. Normal tooling/post-push work
# still sees the warning via hygiene, but should not fail on unrelated external
# site sync debt.
_RELEASE_ONLY_GOVERNANCE_CHECKS: Final[tuple[str, ...]] = ("python3 dev/scripts/checks/check_publication_sync.py",)

# Orchestration status commands used by tooling, release, and post-push bundles.
_ORCHESTRATE_COMMANDS: Final[tuple[str, ...]] = (
    "python3 dev/scripts/devctl.py orchestrate-status --format md",
    "python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md",
)

# Host-side cleanup/audit step for repo-related stale/orphan process trees.
_HOST_PROCESS_HYGIENE_COMMAND: Final[str] = "python3 dev/scripts/devctl.py process-cleanup --verify --format md"

# Operator Console proof path for tooling changes touching the optional PyQt UI.
_OPERATOR_CONSOLE_TESTS_COMMAND: Final[str] = "python3 -m pytest app/operator_console/tests/ -q --tb=short"


def _compose_post_push_guard_checks() -> tuple[str, ...]:
    """Reuse the canonical guard list while scoping diff-aware checks to origin/develop."""
    commands: list[str] = []
    for command in _GUARD_CHECKS:
        if command in _POST_PUSH_DIFF_GUARD_COMMANDS:
            commands.append(f"{command} --since-ref origin/develop")
        else:
            commands.append(command)
    return tuple(commands)


_POST_PUSH_GUARD_CHECKS: Final[tuple[str, ...]] = _compose_post_push_guard_checks()

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
        _HOST_PROCESS_HYGIENE_COMMAND,
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
        *_SHARED_GOVERNANCE_CHECKS,
        *_GUARD_CHECKS,
        _OPERATOR_CONSOLE_TESTS_COMMAND,
        _HOST_PROCESS_HYGIENE_COMMAND,
    ),
    "bundle.release": (
        "python3 dev/scripts/devctl.py check --profile release",
        "python3 dev/scripts/devctl.py docs-check --user-facing --strict",
        "python3 dev/scripts/devctl.py docs-check --strict-tooling",
        "python3 dev/scripts/devctl.py hygiene --strict-warnings",
        *_ORCHESTRATE_COMMANDS,
        *_SHARED_GOVERNANCE_CHECKS,
        *_RELEASE_ONLY_GOVERNANCE_CHECKS,
        "CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master",
        "CI=1 python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master",
        *_GUARD_CHECKS,
        _HOST_PROCESS_HYGIENE_COMMAND,
    ),
    "bundle.post-push": (
        "git status",
        "git log --oneline --decorate -n 10",
        "python3 dev/scripts/devctl.py status --ci --require-ci --format md",
        *_ORCHESTRATE_COMMANDS,
        "python3 dev/scripts/devctl.py docs-check --user-facing --since-ref origin/develop",
        "python3 dev/scripts/devctl.py hygiene",
        "python3 dev/scripts/checks/check_active_plan_sync.py",
        "python3 dev/scripts/checks/check_review_channel_bridge.py",
        *_POST_PUSH_GUARD_CHECKS[1:],
        _HOST_PROCESS_HYGIENE_COMMAND,
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
    return "\n\n".join(render_bundle_reference_markdown(bundle_name) for bundle_name in bundle_names())


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
