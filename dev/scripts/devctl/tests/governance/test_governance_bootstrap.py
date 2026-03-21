"""Tests for governance pilot bootstrap helpers and CLI wiring."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl import cli, governance_bootstrap_support
from dev.scripts.devctl.commands.governance import bootstrap as governance_bootstrap
from dev.scripts.devctl.governance.bootstrap_policy import build_starter_repo_policy


class GovernanceBootstrapTests(unittest.TestCase):
    def test_bootstrap_reinitializes_broken_git_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "copied-repo"
            repo_root.mkdir()
            (repo_root / ".git").write_text(
                "gitdir: ../../.git/modules/integrations/ci-cd-hub\n",
                encoding="utf-8",
            )
            (repo_root / "README.md").write_text("pilot\n", encoding="utf-8")

            result = governance_bootstrap_support.bootstrap_governance_pilot_repo(
                repo_root
            )

            self.assertEqual(result.git_state, "reinitialized")
            self.assertTrue(result.repaired_git_file)
            self.assertTrue(result.initialized_git_repo)
            self.assertTrue((repo_root / ".git").is_dir())
            self.assertTrue(result.starter_policy_written)
            self.assertTrue(
                (repo_root / "dev" / "config" / "devctl_repo_policy.json").exists()
            )
            self.assertTrue(result.starter_setup_guide_written)
            self.assertTrue(
                (
                    repo_root / "dev" / "guides" / "PORTABLE_GOVERNANCE_SETUP.md"
                ).exists()
            )

    def test_bootstrap_keeps_valid_git_repo_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "valid-repo"
            repo_root.mkdir()
            (repo_root / "README.md").write_text("pilot\n", encoding="utf-8")
            governance_bootstrap_support._run_git(repo_root, ["git", "init"])

            result = governance_bootstrap_support.bootstrap_governance_pilot_repo(
                repo_root
            )

            self.assertEqual(result.git_state, "valid")
            self.assertFalse(result.repaired_git_file)
            self.assertFalse(result.initialized_git_repo)
            self.assertTrue(result.starter_policy_written)
            self.assertTrue(
                result.starter_policy_path.endswith("devctl_repo_policy.json")
            )
            self.assertTrue(
                result.starter_setup_guide_path.endswith("PORTABLE_GOVERNANCE_SETUP.md")
            )
            self.assertTrue(result.next_steps)

    def test_bootstrap_preserves_existing_policy_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "existing-policy-repo"
            repo_root.mkdir(parents=True)
            (repo_root / "README.md").write_text("pilot\n", encoding="utf-8")
            governance_bootstrap_support._run_git(repo_root, ["git", "init"])
            policy_path = repo_root / "dev" / "config" / "devctl_repo_policy.json"
            policy_path.parent.mkdir(parents=True, exist_ok=True)
            policy_path.write_text('{"repo_name":"keep-me"}\n', encoding="utf-8")
            guide_path = repo_root / "dev" / "guides" / "PORTABLE_GOVERNANCE_SETUP.md"
            guide_path.parent.mkdir(parents=True, exist_ok=True)
            guide_path.write_text("# keep me\n", encoding="utf-8")

            result = governance_bootstrap_support.bootstrap_governance_pilot_repo(
                repo_root
            )

            self.assertFalse(result.starter_policy_written)
            self.assertFalse(result.starter_setup_guide_written)
            self.assertEqual(
                policy_path.read_text(encoding="utf-8"),
                '{"repo_name":"keep-me"}\n',
            )
            self.assertEqual(
                guide_path.read_text(encoding="utf-8"),
                "# keep me\n",
            )

    def test_starter_policy_includes_surface_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "surface-repo"
            repo_root.mkdir()
            (repo_root / "README.md").write_text("pilot\n", encoding="utf-8")

            payload, _preset, _warnings, _capabilities = build_starter_repo_policy(
                repo_root
            )

        surface_generation = payload["repo_governance"]["surface_generation"]
        self.assertEqual(
            surface_generation["repo_pack_metadata"]["pack_id"],
            "surface-repo",
        )
        self.assertIn(
            "render-surfaces",
            surface_generation["context"]["key_commands_block"],
        )
        self.assertIn(
            "Run the task-class bundle",
            surface_generation["context"]["post_edit_verification_steps"][0],
        )
        self.assertEqual(
            [entry["id"] for entry in surface_generation["surfaces"]],
            [
                "claude_instructions",
                "portable_pre_commit_hook_stub",
                "portable_pre_push_hook_stub",
                "portable_tooling_workflow_stub",
            ],
        )
        self.assertEqual(
            surface_generation["surfaces"][0]["required_contains"],
            [
                "## Mandatory post-edit verification (blocking)",
                "After EVERY file create/edit, you MUST run the repo-required verification before",
                "Done means the required guards/tests passed.",
            ],
        )
        push_governance = payload["repo_governance"]["push"]
        self.assertEqual(push_governance["default_remote"], "origin")
        self.assertEqual(surface_generation["context"]["development_branch"], "main")
        self.assertEqual(surface_generation["context"]["branch_policy"], "`main` (default branch)")

    def test_bootstrap_next_steps_include_render_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "valid-repo"
            repo_root.mkdir()
            (repo_root / "README.md").write_text("pilot\n", encoding="utf-8")
            governance_bootstrap_support._run_git(repo_root, ["git", "init"])

            result = governance_bootstrap_support.bootstrap_governance_pilot_repo(
                repo_root
            )

        self.assertIn(
            "python3 dev/scripts/devctl.py render-surfaces --write --format md",
            result.next_steps,
        )

    def test_bootstrap_seeds_presets_and_quality_scopes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "python-repo"
            repo_root.mkdir()
            (repo_root / "README.md").write_text("pilot\n", encoding="utf-8")
            (repo_root / "cihub").mkdir()
            (repo_root / "cihub" / "__init__.py").write_text("", encoding="utf-8")
            governance_bootstrap_support._run_git(repo_root, ["git", "init"])

            result = governance_bootstrap_support.bootstrap_governance_pilot_repo(
                repo_root
            )

            policy_path = repo_root / "dev" / "config" / "devctl_repo_policy.json"
            payload = json.loads(policy_path.read_text(encoding="utf-8"))
            self.assertTrue(result.starter_policy_written)
            self.assertTrue(
                (repo_root / "dev" / "config" / "quality_presets" / "portable_python.json").exists()
            )
            self.assertEqual(
                payload["quality_scopes"]["python_probe_roots"],
                ["cihub"],
            )


class GovernanceBootstrapParserTests(unittest.TestCase):
    def test_cli_accepts_governance_bootstrap_command(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "governance-bootstrap",
                "--target-repo",
                "/tmp/portable-pilot",
                "--force-starter-policy",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "governance-bootstrap")
        self.assertEqual(args.target_repo, "/tmp/portable-pilot")
        self.assertTrue(args.write_starter_policy)
        self.assertTrue(args.force_starter_policy)
        self.assertEqual(args.format, "json")
        self.assertIs(
            cli.COMMAND_HANDLERS["governance-bootstrap"],
            governance_bootstrap.run,
        )


if __name__ == "__main__":
    unittest.main()
