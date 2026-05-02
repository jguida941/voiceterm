"""Canonical command-bundle registry for tooling checks and routing.

Bundle commands are defined here as the single execution authority.
Docs may render these lists for reference, but runtime/check scripts should
consume this registry directly.

Bundles use a composition model: shared check layers are defined once and
assembled per bundle to eliminate duplication (DRY).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

try:
    from ..governance.script_catalog_registry import check_script_shell_command
except ImportError:
    # Loaded as standalone file via importlib.util.spec_from_file_location
    # (e.g. check_bundle_registry_dry loader). Fall back to absolute import
    # with repo-root sys.path adjustment.
    import sys as _sys
    from pathlib import Path as _Path

    _REPO_ROOT = _Path(__file__).resolve().parents[3]
    if str(_REPO_ROOT) not in _sys.path:
        _sys.path.insert(0, str(_REPO_ROOT))
    from dev.scripts.devctl.governance.script_catalog_registry import (  # type: ignore[no-redef]
        check_script_shell_command,
    )

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

# Explicit composition contract consumed by self-hosting DRY guards. Each
# listed tuple must stay repo-private, string-only, and reused by multiple
# bundle definitions.
COMPOSITION_LAYER_NAMES: Final[tuple[str, ...]] = (
    "_GUARD_CHECKS",
    "_SHARED_GOVERNANCE_CHECKS",
    "_ORCHESTRATE_COMMANDS",
)

# Guard checks shared across all non-bootstrap bundles.
_GUARD_CHECKS: Final[tuple[str, ...]] = (
    check_script_shell_command("active_plan_sync"),
    check_script_shell_command("system_picture_freshness"),
    check_script_shell_command("multi_agent_sync"),
    check_script_shell_command("cli_flags_parity"),
    check_script_shell_command("screenshot_integrity", "--stale-days", "120"),
    check_script_shell_command("code_shape"),
    check_script_shell_command("package_layout"),
    check_script_shell_command("python_subprocess_policy"),
    check_script_shell_command("mutation_bypass_graph_closure"),
    check_script_shell_command("workflow_shell_hygiene"),
    check_script_shell_command("workflow_action_pinning"),
    check_script_shell_command("ide_provider_isolation", "--fail-on-violations"),
    check_script_shell_command("compat_matrix"),
    check_script_shell_command("compat_matrix_smoke"),
    check_script_shell_command("naming_consistency"),
    check_script_shell_command("rust_test_shape"),
    check_script_shell_command("rust_lint_debt"),
    check_script_shell_command("rust_best_practices"),
    check_script_shell_command("rust_compiler_warnings"),
    check_script_shell_command("serde_compatibility"),
    check_script_shell_command("rust_runtime_panic_policy"),
    check_script_shell_command("facade_wrappers"),
    check_script_shell_command("god_class"),
    check_script_shell_command("mobile_relay_protocol"),
    check_script_shell_command("daemon_state_parity"),
    check_script_shell_command("nesting_depth"),
    check_script_shell_command("parameter_count"),
    check_script_shell_command("python_dict_schema"),
    check_script_shell_command("python_typed_seams"),
    check_script_shell_command("python_global_mutable"),
    check_script_shell_command("python_design_complexity"),
    check_script_shell_command("python_cyclic_imports"),
    check_script_shell_command("python_suppression_debt"),
    check_script_shell_command("structural_similarity"),
    "markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md",
    "find . -maxdepth 1 -type f -name '--*'",
)

_POST_PUSH_DIFF_GUARD_COMMANDS: Final[frozenset[str]] = frozenset(
    {
        check_script_shell_command("code_shape"),
        check_script_shell_command("package_layout"),
        check_script_shell_command("python_subprocess_policy"),
        check_script_shell_command("rust_test_shape"),
        check_script_shell_command("rust_lint_debt"),
        check_script_shell_command("rust_best_practices"),
        check_script_shell_command("rust_compiler_warnings"),
        check_script_shell_command("serde_compatibility"),
        check_script_shell_command("rust_runtime_panic_policy"),
        check_script_shell_command("facade_wrappers"),
        check_script_shell_command("god_class"),
        check_script_shell_command("mobile_relay_protocol"),
        check_script_shell_command("nesting_depth"),
        check_script_shell_command("parameter_count"),
        check_script_shell_command("python_dict_schema"),
        check_script_shell_command("python_typed_seams"),
        check_script_shell_command("python_global_mutable"),
        check_script_shell_command("python_design_complexity"),
        check_script_shell_command("python_cyclic_imports"),
        check_script_shell_command("python_suppression_debt"),
        check_script_shell_command("structural_similarity"),
    }
)

# Governance checks shared by tooling and release bundles.
_SHARED_GOVERNANCE_CHECKS: Final[tuple[str, ...]] = (
    check_script_shell_command("agents_contract"),
    check_script_shell_command("release_version_parity"),
    check_script_shell_command("repo_url_parity"),
    check_script_shell_command("guard_enforcement_inventory"),
    check_script_shell_command("architecture_surface_sync"),
    check_script_shell_command("review_snapshot_freshness"),
    check_script_shell_command("guide_contract_sync"),
    check_script_shell_command("instruction_surface_sync"),
    check_script_shell_command("bundle_registry_dry"),
    check_script_shell_command("bundle_workflow_parity"),
    check_script_shell_command("platform_layer_boundaries"),
    check_script_shell_command("platform_contract_closure"),
    check_script_shell_command("contract_connectivity"),
    check_script_shell_command("typed_enum_connectivity"),
    check_script_shell_command("platform_contract_sync"),
    check_script_shell_command("review_channel_bridge"),
    check_script_shell_command("orchestration_recommendation_closure"),
    check_script_shell_command("startup_authority_contract"),
    check_script_shell_command("review_surface_consistency"),
    check_script_shell_command("tandem_consistency"),
    check_script_shell_command("governance_closure"),
    check_script_shell_command(
        "package_layout",
        "--fail-on-baseline-debt",
        "--baseline-debt-root",
        "dev/scripts/devctl/commands",
    ),
)

# Orchestration status commands used by tooling, release, and post-push bundles.
_ORCHESTRATE_COMMANDS: Final[tuple[str, ...]] = (
    "python3 dev/scripts/devctl.py orchestrate-status --format md",
    "python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md",
)

# Host-side cleanup/audit step for repo-related stale/orphan process trees.
_HOST_PROCESS_HYGIENE_COMMAND: Final[str] = "python3 dev/scripts/devctl.py process-cleanup --verify --format md"
_RELEASE_HYGIENE_COMMAND: Final[str] = (
    "python3 dev/scripts/devctl.py hygiene --strict-release-warnings"
)
# Publication drift only hard-blocks release freshness on the configured
# release branch. Feature branches still render the stale state, but the
# explicit branch-aware gate keeps short-lived release-lane preflight from
# failing on unrelated external-site sync debt.
_RELEASE_PUBLICATION_SYNC_COMMAND: Final[str] = (
    check_script_shell_command("publication_sync", "--release-branch-aware")
)

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

@dataclass(frozen=True, slots=True)
class BundleSpec:
    """Typed bundle definition used to build the registry mapping."""

    name: str
    commands: tuple[str, ...]


_BUNDLE_SPECS: Final[tuple[BundleSpec, ...]] = (
    BundleSpec(
        "bundle.bootstrap",
        (
        "git status --short",
        "git branch --show-current",
        "git remote -v",
        "git log --oneline --decorate -n 10",
        "sed -n '1,220p' dev/active/INDEX.md",
        "python3 dev/scripts/devctl.py list",
        "find . -maxdepth 1 -type f -name '--*'",
        ),
    ),
    BundleSpec(
        "bundle.runtime",
        (
        "python3 dev/scripts/devctl.py check --profile ci",
        _HOST_PROCESS_HYGIENE_COMMAND,
        "python3 dev/scripts/devctl.py docs-check --user-facing",
        "python3 dev/scripts/devctl.py hygiene",
        *_GUARD_CHECKS,
        ),
    ),
    BundleSpec(
        "bundle.docs",
        (
        # --since-ref origin/develop aligned with bundle.post-push so the
        # docs-check "user-facing updates present" rule evaluates against
        # the full local-branch diff instead of only HEAD's most recent
        # commit. Without it, a receipt-refresh commit between a real
        # CHANGELOG update and HEAD hides the update from the checker and
        # push preflight false-negatives on a real CHANGELOG entry.
        # See LIVE_RUN.md Q18.
        "python3 dev/scripts/devctl.py docs-check --user-facing --since-ref origin/develop",
        "python3 dev/scripts/devctl.py hygiene",
        *_GUARD_CHECKS,
        ),
    ),
    BundleSpec(
        "bundle.tooling",
        (
        "python3 dev/scripts/devctl.py docs-check --strict-tooling",
        "python3 dev/scripts/devctl.py hygiene --strict-warnings --ignore-warning-source mutation_badge --ignore-warning-source publications",
        *_ORCHESTRATE_COMMANDS,
        *_SHARED_GOVERNANCE_CHECKS,
        *_GUARD_CHECKS,
        _OPERATOR_CONSOLE_TESTS_COMMAND,
        _HOST_PROCESS_HYGIENE_COMMAND,
        ),
    ),
    BundleSpec(
        "bundle.release",
        (
        "python3 dev/scripts/devctl.py check --profile release",
        "python3 dev/scripts/devctl.py docs-check --user-facing --strict-release",
        "python3 dev/scripts/devctl.py docs-check --strict-tooling",
        _RELEASE_HYGIENE_COMMAND,
        *_ORCHESTRATE_COMMANDS,
        *_SHARED_GOVERNANCE_CHECKS,
        _RELEASE_PUBLICATION_SYNC_COMMAND,
        check_script_shell_command(
            "coderabbit_gate",
            "--branch",
            "master",
            env={"CI": "1"},
        ),
        check_script_shell_command(
            "coderabbit_ralph_gate",
            "--branch",
            "master",
            env={"CI": "1"},
        ),
        *_GUARD_CHECKS,
        _HOST_PROCESS_HYGIENE_COMMAND,
        ),
    ),
    BundleSpec(
        "bundle.post-push",
        (
        "git status",
        "git log --oneline --decorate -n 10",
        "python3 dev/scripts/devctl.py status --ci --require-ci --format md",
        *_ORCHESTRATE_COMMANDS,
        "python3 dev/scripts/devctl.py docs-check --user-facing --since-ref origin/develop",
        "python3 dev/scripts/devctl.py hygiene",
        check_script_shell_command("active_plan_sync"),
        check_script_shell_command("review_channel_bridge"),
        *_POST_PUSH_GUARD_CHECKS[1:],
        _HOST_PROCESS_HYGIENE_COMMAND,
        ),
    ),
)

BUNDLE_REGISTRY: Final[dict[str, tuple[str, ...]]] = {
    spec.name: spec.commands for spec in _BUNDLE_SPECS
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
