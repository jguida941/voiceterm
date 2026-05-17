"""Tests for the packaged mutation-bypass graph closure command."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dev.scripts.checks.mutation_bypass_graph_closure.command import _render_md
from dev.scripts.devctl.governance_graph.mutation_bypass import build_report


class MutationBypassGraphClosureTests(unittest.TestCase):
    def test_report_flags_ungoverned_push_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            scope = (
                "pkg/runtime.py",
                "pkg/helper.py",
                "pkg/executor.py",
                "pkg/push.py",
            )
            (repo_root / "pkg").mkdir()
            (repo_root / "pkg/runtime.py").write_text(
                "def run_git_capture(args):\n    return args\n",
                encoding="utf-8",
            )
            (repo_root / "pkg/helper.py").write_text(
                "\n".join(
                    [
                        "from pkg.runtime import run_git_capture",
                        "",
                        "def helper_commit():",
                        "    return run_git_capture(['commit', '-m', 'msg'])",
                    ]
                ),
                encoding="utf-8",
            )
            (repo_root / "pkg/executor.py").write_text(
                "\n".join(
                    [
                        "from pkg.helper import helper_commit",
                        "",
                        "class GovernedVcsExecutor:",
                        "    def execute(self):",
                        "        return helper_commit()",
                    ]
                ),
                encoding="utf-8",
            )
            (repo_root / "pkg/push.py").write_text(
                "\n".join(
                    [
                        "from pkg.helper import helper_commit",
                        "",
                        "def run_push_action():",
                        "    return helper_commit()",
                    ]
                ),
                encoding="utf-8",
            )
            proof_path = repo_root / "proof.json"

            report = build_report(
                repo_root=repo_root,
                proof_output_path=proof_path,
                scope_paths=scope,
                entrypoint_pointers=(
                    "pkg/executor.py::GovernedVcsExecutor.execute",
                    "pkg/push.py::run_push_action",
                ),
                governed_anchor_pointer="pkg/executor.py::GovernedVcsExecutor.execute",
            )
            self.assertTrue(proof_path.is_file())

        self.assertFalse(report["ok"])
        self.assertEqual(len(report["bypasses"]), 1)

    def test_markdown_render_includes_bypass_section(self) -> None:
        report = {
            "ok": False,
            "proof_artifact": "dev/reports/governance/mutation_bypass_proof.json",
            "node_count": 3,
            "edge_count": 2,
            "bypasses": [
                {
                    "path": "pkg/push.py",
                    "line": 12,
                    "git_verb": "push",
                    "command_source": "run_cmd_fn",
                    "containing_function": "pkg/push.py::run_push_action",
                    "reachable_entrypoints": [
                        {
                            "path": [
                                "pkg/push.py::run_push_action",
                                "pkg/helper.py::helper_push",
                            ]
                        }
                    ],
                }
            ],
            "parse_errors": [],
            "classified_debt": {"hook_owned": [], "test_helpers": []},
        }
        rendered = _render_md(report)
        self.assertIn("Ungoverned Paths", rendered)
        self.assertIn("pkg/push.py:12", rendered)
