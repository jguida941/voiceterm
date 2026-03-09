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
            "python3 dev/scripts/devctl.py hygiene --strict-warnings",
            "python3 dev/scripts/checks/check_agents_contract.py",
            "python3 dev/scripts/checks/check_bundle_registry_dry.py",
            "python3 dev/scripts/checks/check_architecture_surface_sync.py",
            "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
            "python3 dev/scripts/checks/check_guard_enforcement_inventory.py",
            "python3 dev/scripts/checks/check_python_subprocess_policy.py",
            "python3 dev/scripts/checks/check_repo_url_parity.py",
            "python3 dev/scripts/checks/check_release_version_parity.py",
            "python3 dev/scripts/checks/check_review_channel_bridge.py",
            "python3 -m pytest app/operator_console/tests/ -q --tb=short",
        }
        self.assertTrue(required_commands.issubset(commands))
        self.assertNotIn("python3 dev/scripts/checks/check_publication_sync.py", commands)

    def test_release_bundle_keeps_required_release_gates(self) -> None:
        commands = set(get_bundle_commands("bundle.release"))
        required_commands = {
            "python3 dev/scripts/devctl.py check --profile release",
            "python3 dev/scripts/devctl.py docs-check --strict-tooling",
            "CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master",
            "CI=1 python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master",
            "python3 dev/scripts/checks/check_architecture_surface_sync.py",
            "python3 dev/scripts/checks/check_bundle_registry_dry.py",
            "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
            "python3 dev/scripts/checks/check_guard_enforcement_inventory.py",
            "python3 dev/scripts/checks/check_publication_sync.py",
            "python3 dev/scripts/checks/check_python_subprocess_policy.py",
            "python3 dev/scripts/checks/check_repo_url_parity.py",
        }
        self.assertTrue(required_commands.issubset(commands))

    def test_post_push_bundle_does_not_hard_block_on_publication_sync(self) -> None:
        commands = set(get_bundle_commands("bundle.post-push"))
        self.assertNotIn("python3 dev/scripts/checks/check_publication_sync.py", commands)

    def test_reference_renderer_includes_all_bundles(self) -> None:
        markdown = render_all_bundle_reference_markdown()
        for bundle_name in BUNDLE_REGISTRY:
            self.assertIn(f"### `{bundle_name}`", markdown)
            self.assertIn("```bash", markdown)
