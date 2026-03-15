"""Tests for docs-check and git status collection behavior."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl import collect
from dev.scripts.devctl.config import REPO_ROOT, get_repo_root, set_repo_root
from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import docs_check
from dev.scripts.devctl.commands.docs.check_runtime import StrictToolingGateState
from dev.scripts.devctl.quality_scan_mode import ADOPTION_BASE_REF, WORKTREE_HEAD_REF


class CollectGitStatusTests(unittest.TestCase):
    """Validate git collection for worktree and commit-range modes."""

    @patch("dev.scripts.devctl.collect.shutil.which", return_value="/usr/bin/git")
    @patch("dev.scripts.devctl.collect.subprocess.check_output")
    def test_collect_git_status_uses_worktree_porcelain(self, mock_check_output, _mock_git) -> None:
        mock_check_output.side_effect = [
            "feature/test\n",
            " M guides/USAGE.md\nA  dev/CHANGELOG.md\n",
        ]

        report = collect.collect_git_status()

        self.assertEqual(report["branch"], "feature/test")
        self.assertIsNone(report["since_ref"])
        self.assertEqual(report["head_ref"], "HEAD")
        self.assertTrue(report["changelog_updated"])
        self.assertEqual(
            report["changes"],
            [
                {"status": "M", "path": "guides/USAGE.md"},
                {"status": "A", "path": "dev/CHANGELOG.md"},
            ],
        )
        self.assertEqual(
            mock_check_output.call_args_list[1].args[0],
            ["git", "status", "--porcelain", "--untracked-files=all"],
        )

    @patch("dev.scripts.devctl.collect.shutil.which", return_value="/usr/bin/git")
    @patch("dev.scripts.devctl.collect.subprocess.check_output")
    def test_collect_git_status_uses_commit_range_diff(self, mock_check_output, _mock_git) -> None:
        mock_check_output.side_effect = [
            "feature/test\n",
            "M\tguides/USAGE.md\nR100\told.md\tdev/CHANGELOG.md\n",
        ]

        report = collect.collect_git_status("HEAD~1", "HEAD")

        self.assertEqual(report["since_ref"], "HEAD~1")
        self.assertEqual(report["head_ref"], "HEAD")
        self.assertTrue(report["changelog_updated"])
        self.assertEqual(
            report["changes"],
            [
                {"status": "M", "path": "guides/USAGE.md"},
                {"status": "R100", "path": "dev/CHANGELOG.md"},
            ],
        )
        self.assertEqual(
            mock_check_output.call_args_list[1].args[0],
            ["git", "diff", "--name-status", "HEAD~1...HEAD"],
        )

    @patch("dev.scripts.devctl.collect.shutil.which", return_value="/usr/bin/git")
    @patch("dev.scripts.devctl.collect.subprocess.check_output")
    def test_collect_git_status_supports_adoption_scan(self, mock_check_output, _mock_git) -> None:
        mock_check_output.side_effect = [
            "HEAD\n",
            "README.md\ndev/scripts/devctl.py\n",
            "scratch.py\n",
        ]

        report = collect.collect_git_status(ADOPTION_BASE_REF, WORKTREE_HEAD_REF)

        self.assertEqual(report["mode"], "adoption-scan")
        self.assertIsNone(report["since_ref"])
        self.assertIsNone(report["head_ref"])
        self.assertEqual(
            report["changes"],
            [
                {"status": "A", "path": "README.md"},
                {"status": "A", "path": "dev/scripts/devctl.py"},
                {"status": "??", "path": "scratch.py"},
            ],
        )

    @patch("dev.scripts.devctl.collect.shutil.which", return_value="/usr/bin/git")
    @patch("dev.scripts.devctl.collect.subprocess.check_output")
    def test_collect_git_status_uses_runtime_repo_root(self, mock_check_output, _mock_git) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            mock_check_output.side_effect = [
                "feature/external\n",
                " M README.md\n",
            ]
            previous_root = get_repo_root()
            try:
                set_repo_root(repo_root)
                report = collect.collect_git_status()
            finally:
                set_repo_root(previous_root)

        self.assertEqual(report["branch"], "feature/external")
        for call in mock_check_output.call_args_list:
            self.assertEqual(Path(call.kwargs["cwd"]).resolve(), repo_root.resolve())
        self.assertEqual(get_repo_root(), REPO_ROOT)


class DocsCheckCommandTests(unittest.TestCase):
    """Validate docs-check command wiring for commit-range mode."""

    def test_cli_accepts_quality_policy_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "docs-check",
                "--strict-tooling",
                "--quality-policy",
                "/tmp/docs-policy.json",
            ]
        )

        self.assertEqual(args.command, "docs-check")
        self.assertTrue(args.strict_tooling)
        self.assertEqual(args.quality_policy, "/tmp/docs-policy.json")

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_forwards_commit_range(
        self,
        mock_collect_git_status,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "changes": [
                {"status": "M", "path": "dev/CHANGELOG.md"},
                {"status": "M", "path": "guides/USAGE.md"},
            ]
        }
        args = SimpleNamespace(
            user_facing=True,
            strict=False,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref="origin/develop",
            head_ref="HEAD",
            strict_tooling=False,
        )

        code = docs_check.run(args)

        self.assertEqual(code, 0)
        mock_collect_git_status.assert_called_once_with("origin/develop", "HEAD")

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_fails_when_tooling_changes_without_tooling_docs(
        self,
        mock_collect_git_status,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "changes": [
                {"status": "M", "path": "Makefile"},
            ]
        }
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=False,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref="HEAD~1",
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_requires_canonical_platform_plan_for_platform_scope(
        self,
        mock_collect_git_status,
        _mock_scan_deprecated,
        mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "changes": [
                {"status": "M", "path": "dev/scripts/devctl/runtime/control_state.py"},
                {"status": "M", "path": "AGENTS.md"},
                {"status": "M", "path": "dev/guides/DEVELOPMENT.md"},
                {"status": "M", "path": "dev/scripts/README.md"},
                {"status": "M", "path": "dev/active/MASTER_PLAN.md"},
            ]
        }
        policy_payload = {
            "schema_version": 1,
            "repo_governance": {
                "docs_check": {
                    "tooling_doc_requirement_rules": [
                        {
                            "id": "ai_governance_platform_plan",
                            "trigger_prefixes": [
                                "dev/scripts/devctl/runtime/",
                            ],
                            "required_docs": [
                                "dev/active/ai_governance_platform.md",
                            ],
                        }
                    ]
                }
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.json"
            policy_path.write_text(json.dumps(policy_payload), encoding="utf-8")
            args = SimpleNamespace(
                user_facing=False,
                strict=False,
                strict_tooling=False,
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
                since_ref=None,
                head_ref="HEAD",
                quality_policy=str(policy_path),
            )

            code = docs_check.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(mock_write_output.call_args.args[0])
        self.assertEqual(
            payload["missing_triggered_tooling_docs"],
            ["dev/active/ai_governance_platform.md"],
        )
        self.assertEqual(
            payload["matched_tooling_doc_requirement_rules"],
            ["ai_governance_platform_plan"],
        )

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_accepts_platform_scope_when_canonical_plan_is_updated(
        self,
        mock_collect_git_status,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "changes": [
                {"status": "M", "path": "dev/scripts/devctl/runtime/control_state.py"},
                {"status": "M", "path": "dev/active/ai_governance_platform.md"},
                {"status": "M", "path": "AGENTS.md"},
                {"status": "M", "path": "dev/guides/DEVELOPMENT.md"},
                {"status": "M", "path": "dev/scripts/README.md"},
                {"status": "M", "path": "dev/active/MASTER_PLAN.md"},
            ]
        }
        policy_payload = {
            "schema_version": 1,
            "repo_governance": {
                "docs_check": {
                    "tooling_doc_requirement_rules": [
                        {
                            "id": "ai_governance_platform_plan",
                            "trigger_prefixes": [
                                "dev/scripts/devctl/runtime/",
                            ],
                            "required_docs": [
                                "dev/active/ai_governance_platform.md",
                            ],
                        }
                    ]
                }
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.json"
            policy_path.write_text(json.dumps(policy_payload), encoding="utf-8")
            args = SimpleNamespace(
                user_facing=False,
                strict=False,
                strict_tooling=False,
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
                since_ref=None,
                head_ref="HEAD",
                quality_policy=str(policy_path),
            )

            code = docs_check.run(args)

        self.assertEqual(code, 0)

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_strict_tooling_gates")
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_reports_instruction_surface_gate_failure(
        self,
        mock_collect_git_status,
        mock_collect_gates,
        _mock_scan_deprecated,
        mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "changes": [
                {
                    "status": "M",
                    "path": "dev/scripts/devctl/commands/governance/render_surfaces.py",
                },
                {"status": "M", "path": "AGENTS.md"},
                {"status": "M", "path": "dev/guides/DEVELOPMENT.md"},
                {"status": "M", "path": "dev/scripts/README.md"},
                {"status": "M", "path": "dev/active/MASTER_PLAN.md"},
                {"status": "M", "path": "dev/history/ENGINEERING_EVOLUTION.md"},
                {"status": "M", "path": "dev/active/ai_governance_platform.md"},
            ]
        }
        mock_collect_gates.return_value = StrictToolingGateState(
            active_plan_sync_ok=True,
            active_plan_sync_report={"ok": True},
            multi_agent_sync_ok=True,
            multi_agent_sync_report={"ok": True},
            legacy_path_audit_ok=True,
            legacy_path_audit_report={"ok": True},
            markdown_metadata_header_ok=True,
            markdown_metadata_header_report={"ok": True},
            workflow_shell_hygiene_ok=True,
            workflow_shell_hygiene_report={"ok": True},
            bundle_workflow_parity_ok=True,
            bundle_workflow_parity_report={"ok": True},
            agents_bundle_render_ok=True,
            agents_bundle_render_report={"ok": True},
            instruction_surface_sync_ok=False,
            instruction_surface_sync_report={
                "ok": False,
                "error": "surface drift",
            },
        )
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref=None,
            head_ref="HEAD",
            quality_policy=None,
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(mock_write_output.call_args.args[0])
        self.assertFalse(payload["instruction_surface_sync_ok"])
        self.assertIn(
            "Instruction surface sync gate failed: surface drift",
            payload["failure_reasons"],
        )
        self.assertIn(
            "Regenerate policy-owned instruction/starter surfaces: `python3 dev/scripts/devctl.py render-surfaces --write --format md` or inspect `python3 dev/scripts/checks/check_instruction_surface_sync.py --format md`.",
            payload["next_actions"],
        )

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_user_facing_commit_range_no_changes_is_noop_pass(
        self,
        mock_collect_git_status,
        _mock_scan_deprecated,
        mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"changes": []}
        args = SimpleNamespace(
            user_facing=True,
            strict=True,
            strict_tooling=False,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref="origin/develop",
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 0)
        payload = json.loads(mock_write_output.call_args.args[0])
        self.assertTrue(payload["empty_commit_range"])

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_json_includes_failure_reasons_and_next_actions(
        self,
        mock_collect_git_status,
        _mock_scan_deprecated,
        mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"changes": []}
        args = SimpleNamespace(
            user_facing=True,
            strict=True,
            strict_tooling=False,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref=None,
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)
        output = mock_write_output.call_args.args[0]
        payload = json.loads(output)
        self.assertIn("failure_reasons", payload)
        self.assertIn("next_actions", payload)
        self.assertTrue(
            any("Missing required `dev/CHANGELOG.md` update" in reason for reason in payload["failure_reasons"])
        )
        self.assertTrue(any("triage" in action for action in payload["next_actions"]))

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch("dev.scripts.devctl.commands.docs_check._scan_deprecated_references")
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_fails_on_deprecated_reference_violations(
        self,
        mock_collect_git_status,
        mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"changes": []}
        mock_scan_deprecated.return_value = [
            {
                "file": "AGENTS.md",
                "line": 1,
                "pattern": "release-script",
                "replacement": "python3 dev/scripts/devctl.py release --version <version>",
                "line_text": "./dev/scripts/release.sh 1.2.3",
            }
        ]
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=False,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref=None,
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_markdown_metadata_header_gate",
        return_value={
            "ok": True,
            "mode": "check",
            "changed_paths": [],
        },
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_workflow_shell_hygiene_gate",
        return_value={"ok": True, "violations": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_agents_bundle_render_gate",
        return_value={"ok": True, "changed": False, "wrote": False},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_instruction_surface_sync_gate",
        return_value={"ok": True, "surfaces": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_bundle_workflow_parity_gate",
        return_value={"ok": True, "targets": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_multi_agent_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_active_plan_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check.scan_legacy_path_references",
        return_value={
            "ok": True,
            "checked_file_count": 10,
            "excluded_prefixes": ["dev/archive/"],
            "rules": {},
            "violations": [],
        },
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_strict_tooling_requires_engineering_evolution_update(
        self,
        mock_collect_git_status,
        _mock_path_audit,
        _mock_active_plan_sync,
        _mock_multi_agent_sync,
        _mock_instruction_surface_sync,
        _mock_agents_bundle_render,
        _mock_bundle_workflow_parity,
        _mock_workflow_shell_hygiene,
        _mock_metadata_header,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "changes": [
                {"status": "M", "path": ".github/workflows/tooling_control_plane.yml"},
                {"status": "M", "path": "AGENTS.md"},
                {"status": "M", "path": "dev/guides/DEVELOPMENT.md"},
                {"status": "M", "path": "dev/scripts/README.md"},
                {"status": "M", "path": "dev/active/MASTER_PLAN.md"},
            ]
        }
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref="HEAD~1",
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_markdown_metadata_header_gate",
        return_value={
            "ok": True,
            "mode": "check",
            "changed_paths": [],
        },
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_workflow_shell_hygiene_gate",
        return_value={"ok": True, "violations": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_agents_bundle_render_gate",
        return_value={"ok": True, "changed": False, "wrote": False},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_instruction_surface_sync_gate",
        return_value={"ok": True, "surface_count": 5},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_bundle_workflow_parity_gate",
        return_value={"ok": True, "targets": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_multi_agent_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_active_plan_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check.scan_legacy_path_references",
        return_value={
            "ok": True,
            "checked_file_count": 10,
            "excluded_prefixes": ["dev/archive/"],
            "rules": {},
            "violations": [],
        },
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_strict_tooling_passes_with_engineering_evolution_update(
        self,
        mock_collect_git_status,
        _mock_path_audit,
        _mock_active_plan_sync,
        _mock_multi_agent_sync,
        _mock_bundle_workflow_parity,
        _mock_instruction_surface_sync,
        _mock_agents_bundle_render,
        _mock_workflow_shell_hygiene,
        _mock_metadata_header,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "changes": [
                {"status": "M", "path": ".github/workflows/tooling_control_plane.yml"},
                {"status": "M", "path": "AGENTS.md"},
                {"status": "M", "path": "dev/guides/DEVELOPMENT.md"},
                {"status": "M", "path": "dev/scripts/README.md"},
                {"status": "M", "path": "dev/active/MASTER_PLAN.md"},
                {"status": "M", "path": "dev/history/ENGINEERING_EVOLUTION.md"},
            ]
        }
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref="HEAD~1",
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 0)

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_markdown_metadata_header_gate",
        return_value={
            "ok": True,
            "mode": "check",
            "changed_paths": [],
        },
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_workflow_shell_hygiene_gate",
        return_value={"ok": True, "violations": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_agents_bundle_render_gate",
        return_value={"ok": True, "changed": False, "wrote": False},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_instruction_surface_sync_gate",
        return_value={"ok": True, "surfaces": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_bundle_workflow_parity_gate",
        return_value={"ok": True, "targets": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_multi_agent_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_active_plan_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check.scan_legacy_path_references",
        return_value={
            "ok": True,
            "checked_file_count": 10,
            "excluded_prefixes": ["dev/archive/"],
            "rules": {},
            "violations": [],
        },
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_strict_tooling_rejects_legacy_development_bridge_path(
        self,
        mock_collect_git_status,
        _mock_path_audit,
        _mock_active_plan_sync,
        _mock_multi_agent_sync,
        _mock_agents_bundle_render,
        _mock_instruction_surface_sync,
        _mock_bundle_workflow_parity,
        _mock_workflow_shell_hygiene,
        _mock_metadata_header,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "changes": [
                {"status": "M", "path": ".github/workflows/tooling_control_plane.yml"},
                {"status": "M", "path": "AGENTS.md"},
                {"status": "M", "path": "dev/DEVELOPMENT.md"},
                {"status": "M", "path": "dev/scripts/README.md"},
                {"status": "M", "path": "dev/active/MASTER_PLAN.md"},
                {"status": "M", "path": "dev/history/ENGINEERING_EVOLUTION.md"},
            ]
        }
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref="HEAD~1",
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_markdown_metadata_header_gate",
        return_value={
            "ok": True,
            "mode": "check",
            "changed_paths": [],
        },
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_workflow_shell_hygiene_gate",
        return_value={"ok": True, "violations": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_agents_bundle_render_gate",
        return_value={"ok": True, "changed": False, "wrote": False},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_bundle_workflow_parity_gate",
        return_value={"ok": True, "targets": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_multi_agent_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_active_plan_sync_gate",
        return_value={"ok": False, "errors": ["missing master-plan link"]},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check.scan_legacy_path_references",
        return_value={
            "ok": True,
            "checked_file_count": 10,
            "excluded_prefixes": ["dev/archive/"],
            "rules": {},
            "violations": [],
        },
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_strict_tooling_fails_when_active_plan_sync_fails(
        self,
        mock_collect_git_status,
        _mock_path_audit,
        _mock_active_plan_sync,
        _mock_multi_agent_sync,
        _mock_agents_bundle_render,
        _mock_bundle_workflow_parity,
        _mock_workflow_shell_hygiene,
        _mock_metadata_header,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"changes": []}
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref=None,
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_markdown_metadata_header_gate",
        return_value={
            "ok": True,
            "mode": "check",
            "changed_paths": [],
        },
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_workflow_shell_hygiene_gate",
        return_value={"ok": True, "violations": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_agents_bundle_render_gate",
        return_value={"ok": True, "changed": False, "wrote": False},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_bundle_workflow_parity_gate",
        return_value={"ok": True, "targets": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_multi_agent_sync_gate",
        return_value={"ok": False, "errors": ["AGENT-2 mismatch"]},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_active_plan_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check.scan_legacy_path_references",
        return_value={
            "ok": True,
            "checked_file_count": 10,
            "excluded_prefixes": ["dev/archive/"],
            "rules": {},
            "violations": [],
        },
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_strict_tooling_fails_when_multi_agent_sync_fails(
        self,
        mock_collect_git_status,
        _mock_path_audit,
        _mock_active_plan_sync,
        _mock_multi_agent_sync,
        _mock_agents_bundle_render,
        _mock_bundle_workflow_parity,
        _mock_workflow_shell_hygiene,
        _mock_metadata_header,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"changes": []}
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref=None,
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_markdown_metadata_header_gate",
        return_value={
            "ok": True,
            "mode": "check",
            "changed_paths": [],
        },
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_workflow_shell_hygiene_gate",
        return_value={"ok": True, "violations": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_agents_bundle_render_gate",
        return_value={"ok": True, "changed": False, "wrote": False},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_bundle_workflow_parity_gate",
        return_value={"ok": True, "targets": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_multi_agent_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_active_plan_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check.scan_legacy_path_references",
        return_value={
            "ok": False,
            "checked_file_count": 10,
            "excluded_prefixes": ["dev/archive/"],
            "rules": {"dev/scripts/" + "check_agents_contract.py": "dev/scripts/checks/check_agents_contract.py"},
            "violations": [
                {
                    "file": "AGENTS.md",
                    "line": 1,
                    "legacy_path": "dev/scripts/" + "check_agents_contract.py",
                    "replacement_path": "dev/scripts/checks/check_agents_contract.py",
                    "line_text": "python3 dev/scripts/" + "check_agents_contract.py",
                }
            ],
        },
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_strict_tooling_fails_when_legacy_path_audit_fails(
        self,
        mock_collect_git_status,
        _mock_path_audit,
        _mock_active_plan_sync,
        _mock_multi_agent_sync,
        _mock_agents_bundle_render,
        _mock_bundle_workflow_parity,
        _mock_workflow_shell_hygiene,
        _mock_metadata_header,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"changes": []}
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref=None,
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_markdown_metadata_header_gate",
        return_value={
            "ok": False,
            "mode": "check",
            "changed_paths": ["dev/integrations/EXTERNAL_REPOS.md"],
        },
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_workflow_shell_hygiene_gate",
        return_value={"ok": True, "violations": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_agents_bundle_render_gate",
        return_value={"ok": True, "changed": False, "wrote": False},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_bundle_workflow_parity_gate",
        return_value={"ok": True, "targets": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_multi_agent_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_active_plan_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check.scan_legacy_path_references",
        return_value={
            "ok": True,
            "checked_file_count": 10,
            "excluded_prefixes": ["dev/archive/"],
            "rules": {},
            "violations": [],
        },
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_strict_tooling_fails_when_metadata_header_gate_fails(
        self,
        mock_collect_git_status,
        _mock_path_audit,
        _mock_active_plan_sync,
        _mock_multi_agent_sync,
        _mock_agents_bundle_render,
        _mock_bundle_workflow_parity,
        _mock_workflow_shell_hygiene,
        _mock_metadata_header,
        _mock_scan_deprecated,
        mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"changes": []}
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref=None,
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(mock_write_output.call_args.args[0])
        self.assertFalse(payload["markdown_metadata_header_ok"])
        self.assertTrue(any("Markdown metadata header gate failed" in reason for reason in payload["failure_reasons"]))

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_markdown_metadata_header_gate",
        return_value={"ok": True, "mode": "check", "changed_paths": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_workflow_shell_hygiene_gate",
        return_value={
            "ok": False,
            "violations": [
                {
                    "file": ".github/workflows/mutation-testing.yml",
                    "line": 84,
                    "rule": "find-pipe-head",
                    "line_text": "OUTCOME_PATH=$(find mutants.out -name outcomes.json | head -n 1)",
                }
            ],
        },
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_agents_bundle_render_gate",
        return_value={"ok": True, "changed": False, "wrote": False},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_bundle_workflow_parity_gate",
        return_value={"ok": True, "targets": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_multi_agent_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_active_plan_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check.scan_legacy_path_references",
        return_value={
            "ok": True,
            "checked_file_count": 10,
            "excluded_prefixes": ["dev/archive/"],
            "rules": {},
            "violations": [],
        },
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_strict_tooling_fails_when_workflow_shell_hygiene_fails(
        self,
        mock_collect_git_status,
        _mock_path_audit,
        _mock_active_plan_sync,
        _mock_multi_agent_sync,
        _mock_agents_bundle_render,
        _mock_bundle_workflow_parity,
        _mock_workflow_shell_hygiene,
        _mock_metadata_header,
        _mock_scan_deprecated,
        mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"changes": []}
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref=None,
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(mock_write_output.call_args.args[0])
        self.assertFalse(payload["workflow_shell_hygiene_ok"])
        self.assertTrue(any("Workflow shell hygiene gate failed" in reason for reason in payload["failure_reasons"]))

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_markdown_metadata_header_gate",
        return_value={"ok": True, "mode": "check", "changed_paths": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_workflow_shell_hygiene_gate",
        return_value={"ok": True, "violations": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_agents_bundle_render_gate",
        return_value={"ok": True, "changed": False, "wrote": False},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_bundle_workflow_parity_gate",
        return_value={
            "ok": False,
            "targets": [
                {
                    "bundle": "bundle.tooling",
                    "workflow": ".github/workflows/tooling_control_plane.yml",
                    "missing_commands": ["python3 dev/scripts/checks/check_naming_consistency.py"],
                }
            ],
        },
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_multi_agent_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_active_plan_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check.scan_legacy_path_references",
        return_value={
            "ok": True,
            "checked_file_count": 10,
            "excluded_prefixes": ["dev/archive/"],
            "rules": {},
            "violations": [],
        },
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_strict_tooling_fails_when_bundle_workflow_parity_fails(
        self,
        mock_collect_git_status,
        _mock_path_audit,
        _mock_active_plan_sync,
        _mock_multi_agent_sync,
        _mock_agents_bundle_render,
        _mock_bundle_workflow_parity,
        _mock_workflow_shell_hygiene,
        _mock_metadata_header,
        _mock_scan_deprecated,
        mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"changes": []}
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref=None,
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(mock_write_output.call_args.args[0])
        self.assertFalse(payload["bundle_workflow_parity_ok"])
        self.assertTrue(any("Bundle/workflow parity gate failed" in reason for reason in payload["failure_reasons"]))

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch(
        "dev.scripts.devctl.commands.docs_check._scan_deprecated_references",
        return_value=[],
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_markdown_metadata_header_gate",
        return_value={"ok": True, "mode": "check", "changed_paths": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_workflow_shell_hygiene_gate",
        return_value={"ok": True, "violations": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_agents_bundle_render_gate",
        return_value={"ok": False, "changed": True, "diff_preview": ["@@ sample @@"]},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_bundle_workflow_parity_gate",
        return_value={"ok": True, "targets": []},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_multi_agent_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check._run_active_plan_sync_gate",
        return_value={"ok": True},
    )
    @patch(
        "dev.scripts.devctl.commands.docs_check.scan_legacy_path_references",
        return_value={
            "ok": True,
            "checked_file_count": 10,
            "excluded_prefixes": ["dev/archive/"],
            "rules": {},
            "violations": [],
        },
    )
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_strict_tooling_fails_when_agents_bundle_render_fails(
        self,
        mock_collect_git_status,
        _mock_path_audit,
        _mock_active_plan_sync,
        _mock_multi_agent_sync,
        _mock_bundle_workflow_parity,
        _mock_agents_bundle_render,
        _mock_workflow_shell_hygiene,
        _mock_metadata_header,
        _mock_scan_deprecated,
        mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"changes": []}
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref=None,
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(mock_write_output.call_args.args[0])
        self.assertFalse(payload["agents_bundle_render_ok"])
        self.assertTrue(any("AGENTS bundle render gate failed" in reason for reason in payload["failure_reasons"]))


if __name__ == "__main__":
    unittest.main()
