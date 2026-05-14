"""Contract tests for canonical devctl bundle registry."""

from __future__ import annotations

from unittest import TestCase

from dev.scripts.devctl.bundle_registry import (
    BUNDLE_REGISTRY,
    bundle_names,
    get_bundle_commands,
    render_all_bundle_reference_markdown,
)


class BundleRegistryContractTests(TestCase):
    """Protect bundle registration and required governance commands."""

    def test_required_bundles_are_registered(self) -> None:
        required = {
            "bundle.bootstrap",
            "bundle.runtime",
            "bundle.docs",
            "bundle.tooling",
            "bundle.release",
            "bundle.post-push",
        }
        self.assertEqual(set(bundle_names()), required)

    def test_each_bundle_has_commands(self) -> None:
        for bundle_name in bundle_names():
            commands = get_bundle_commands(bundle_name)
            self.assertGreater(
                len(commands), 0, msg=f"bundle `{bundle_name}` unexpectedly empty"
            )

    def test_tooling_bundle_keeps_required_tooling_gates(self) -> None:
        commands = set(get_bundle_commands("bundle.tooling"))
        required_commands = {
            "python3 dev/scripts/devctl.py docs-check --strict-tooling",
            "python3 dev/scripts/devctl.py hygiene --strict-warnings --ignore-warning-source mutation_badge --ignore-warning-source publications",
            "python3 dev/scripts/checks/check_agents_contract.py",
            "python3 dev/scripts/checks/check_bundle_registry_dry.py",
            "python3 dev/scripts/checks/check_architecture_surface_sync.py",
            "python3 dev/scripts/checks/check_guide_contract_sync.py",
            "python3 dev/scripts/checks/check_instruction_surface_sync.py",
            "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
            "python3 dev/scripts/checks/check_guard_enforcement_inventory.py",
            "python3 dev/scripts/checks/check_mutation_bypass_graph_closure.py",
            "python3 dev/scripts/checks/check_python_broad_except.py",
            "python3 dev/scripts/checks/check_python_subprocess_policy.py",
            "python3 dev/scripts/checks/check_pytest_runtime_policy.py",
            "python3 dev/scripts/checks/check_command_source_validation.py",
            "python3 dev/scripts/checks/check_registry_path_integrity.py",
            "python3 dev/scripts/checks/check_runtime_spine_closure.py",
            "python3 dev/scripts/checks/check_provider_list_parity_graph.py",
            "python3 dev/scripts/checks/check_repo_url_parity.py",
            "python3 dev/scripts/checks/check_release_version_parity.py",
            "python3 dev/scripts/checks/check_systemmap_covers_contract_registry.py",
            "python3 dev/scripts/checks/check_review_channel_bridge.py",
            "python3 dev/scripts/checks/check_bridge_projection_only.py",
            "python3 dev/scripts/checks/check_serde_compatibility.py",
            "python3 dev/scripts/checks/check_structural_complexity.py",
            "python3 dev/scripts/checks/check_duplicate_types.py",
        }
        self.assertTrue(required_commands.issubset(commands))
        self.assertNotIn(
            "python3 dev/scripts/devctl.py test-python --suite operator-console",
            commands,
        )
        self.assertNotIn("python3 dev/scripts/checks/check_publication_sync.py", commands)

    def test_release_bundle_keeps_required_release_gates(self) -> None:
        commands = set(get_bundle_commands("bundle.release"))
        required_commands = {
            "python3 dev/scripts/devctl.py check --profile release",
            "python3 dev/scripts/devctl.py docs-check --strict-tooling",
            "python3 dev/scripts/devctl.py hygiene --strict-release-warnings",
            "CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master",
            "CI=1 python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master",
            "python3 dev/scripts/checks/check_architecture_surface_sync.py",
            "python3 dev/scripts/checks/check_guide_contract_sync.py",
            "python3 dev/scripts/checks/check_instruction_surface_sync.py",
            "python3 dev/scripts/checks/check_bundle_registry_dry.py",
            "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
            "python3 dev/scripts/checks/check_guard_enforcement_inventory.py",
            "python3 dev/scripts/checks/check_bridge_projection_only.py",
            "python3 dev/scripts/checks/check_publication_sync.py --release-branch-aware",
            "python3 dev/scripts/checks/check_python_subprocess_policy.py",
            "python3 dev/scripts/checks/check_repo_url_parity.py",
            "python3 dev/scripts/checks/check_systemmap_covers_contract_registry.py",
            "python3 dev/scripts/checks/check_serde_compatibility.py",
        }
        self.assertTrue(required_commands.issubset(commands))

    def test_post_push_bundle_does_not_hard_block_on_publication_sync(self) -> None:
        commands = set(get_bundle_commands("bundle.post-push"))
        self.assertNotIn("python3 dev/scripts/checks/check_publication_sync.py", commands)

    def test_post_push_bundle_only_ranges_range_aware_guards(self) -> None:
        commands = set(get_bundle_commands("bundle.post-push"))
        non_range_guards = {
            "python3 dev/scripts/checks/check_registry_path_integrity.py",
            "python3 dev/scripts/checks/check_runtime_spine_closure.py",
            "python3 dev/scripts/checks/check_provider_list_parity_graph.py",
        }
        range_guards = {
            "python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop",
            "python3 dev/scripts/checks/check_command_source_validation.py --since-ref origin/develop",
        }

        self.assertTrue(non_range_guards.issubset(commands))
        for command in commands:
            if any(guard in command for guard in non_range_guards):
                self.assertNotIn("--since-ref", command)
        self.assertTrue(range_guards.issubset(commands))

    def test_reference_renderer_includes_all_bundles(self) -> None:
        markdown = render_all_bundle_reference_markdown()
        for bundle_name in BUNDLE_REGISTRY:
            self.assertIn(f"### `{bundle_name}`", markdown)
            self.assertIn("```bash", markdown)
