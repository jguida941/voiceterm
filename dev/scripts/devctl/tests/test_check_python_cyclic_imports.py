"""Tests for check_python_cyclic_imports guard."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, patch

from dev.scripts.devctl.tests.conftest import (
    REPO_ROOT,
    init_python_guard_repo_root,
    load_repo_module,
    override_module_attrs,
)

SCRIPT = load_repo_module(
    "check_python_cyclic_imports",
    "dev/scripts/checks/check_python_cyclic_imports.py",
)


class CheckPythonCyclicImportsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_python_guard_repo_root(self)

    def test_report_flags_new_cycle_for_changed_files(self) -> None:
        report = SCRIPT.build_report(
            repo_root=self.root,
            inputs=SCRIPT.CycleReportInputs(
                candidate_paths=[Path("dev/scripts/a.py"), Path("dev/scripts/b.py")],
                graph_inputs=SCRIPT.CycleGraphInputs(
                    base_paths=[Path("dev/scripts/a.py"), Path("dev/scripts/b.py")],
                    current_paths=[Path("dev/scripts/a.py"), Path("dev/scripts/b.py")],
                    base_map={
                        Path("dev/scripts/a.py"): Path("dev/scripts/a.py"),
                        Path("dev/scripts/b.py"): Path("dev/scripts/b.py"),
                    },
                ),
                base_text_by_path={
                    "dev/scripts/a.py": "import json\n",
                    "dev/scripts/b.py": "import os\n",
                },
                current_text_by_path={
                    "dev/scripts/a.py": "from dev.scripts import b\n",
                    "dev/scripts/b.py": "from dev.scripts import a\n",
                },
                mode="working-tree",
                target_roots=SCRIPT.TARGET_ROOTS,
            ),
            resolve_guard_config_fn=SCRIPT._resolve_guard_config,
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["totals"]["cyclic_imports_growth"], 1)
        self.assertEqual(len(report["cycles"]), 1)
        self.assertEqual(len(report["violations"]), 2)

    def test_report_allows_cycle_that_already_exists_in_base(self) -> None:
        cycle_text = {
            "dev/scripts/a.py": "from dev.scripts import b\n",
            "dev/scripts/b.py": "from dev.scripts import a\n",
        }

        report = SCRIPT.build_report(
            repo_root=self.root,
            inputs=SCRIPT.CycleReportInputs(
                candidate_paths=[Path("dev/scripts/a.py")],
                graph_inputs=SCRIPT.CycleGraphInputs(
                    base_paths=[Path("dev/scripts/a.py"), Path("dev/scripts/b.py")],
                    current_paths=[Path("dev/scripts/a.py"), Path("dev/scripts/b.py")],
                    base_map={Path("dev/scripts/a.py"): Path("dev/scripts/a.py")},
                ),
                base_text_by_path=cycle_text,
                current_text_by_path=cycle_text,
                mode="working-tree",
                target_roots=SCRIPT.TARGET_ROOTS,
            ),
            resolve_guard_config_fn=SCRIPT._resolve_guard_config,
        )

        self.assertTrue(report["ok"], report["cycles"])
        self.assertEqual(report["totals"]["cyclic_imports_growth"], 0)

    def test_report_ignores_cycles_that_do_not_touch_changed_paths(self) -> None:
        report = SCRIPT.build_report(
            repo_root=self.root,
            inputs=SCRIPT.CycleReportInputs(
                candidate_paths=[Path("dev/scripts/c.py")],
                graph_inputs=SCRIPT.CycleGraphInputs(
                    base_paths=[
                        Path("dev/scripts/a.py"),
                        Path("dev/scripts/b.py"),
                        Path("dev/scripts/c.py"),
                    ],
                    current_paths=[
                        Path("dev/scripts/a.py"),
                        Path("dev/scripts/b.py"),
                        Path("dev/scripts/c.py"),
                    ],
                    base_map={Path("dev/scripts/c.py"): Path("dev/scripts/c.py")},
                ),
                base_text_by_path={
                    "dev/scripts/a.py": "import json\n",
                    "dev/scripts/b.py": "import os\n",
                    "dev/scripts/c.py": "import json\n",
                },
                current_text_by_path={
                    "dev/scripts/a.py": "from dev.scripts import b\n",
                    "dev/scripts/b.py": "from dev.scripts import a\n",
                    "dev/scripts/c.py": "import json\n",
                },
                mode="working-tree",
                target_roots=SCRIPT.TARGET_ROOTS,
            ),
            resolve_guard_config_fn=SCRIPT._resolve_guard_config,
        )

        self.assertTrue(report["ok"], report["cycles"])
        self.assertEqual(report["totals"]["cyclic_imports_growth"], 0)

    def test_ignored_cycles_config_suppresses_known_cycle(self) -> None:
        override_module_attrs(
            self,
            SCRIPT,
            resolve_guard_config=lambda script_id, repo_root: {
                "ignored_cycles": [["dev/scripts/a.py", "dev/scripts/b.py"]]
            },
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            inputs=SCRIPT.CycleReportInputs(
                candidate_paths=[Path("dev/scripts/a.py"), Path("dev/scripts/b.py")],
                graph_inputs=SCRIPT.CycleGraphInputs(
                    base_paths=[Path("dev/scripts/a.py"), Path("dev/scripts/b.py")],
                    current_paths=[Path("dev/scripts/a.py"), Path("dev/scripts/b.py")],
                    base_map={
                        Path("dev/scripts/a.py"): Path("dev/scripts/a.py"),
                        Path("dev/scripts/b.py"): Path("dev/scripts/b.py"),
                    },
                ),
                base_text_by_path={
                    "dev/scripts/a.py": "import json\n",
                    "dev/scripts/b.py": "import os\n",
                },
                current_text_by_path={
                    "dev/scripts/a.py": "from dev.scripts import b\n",
                    "dev/scripts/b.py": "from dev.scripts import a\n",
                },
                mode="working-tree",
                target_roots=SCRIPT.TARGET_ROOTS,
            ),
            resolve_guard_config_fn=SCRIPT._resolve_guard_config,
        )

        self.assertTrue(report["ok"], report["cycles"])
        self.assertEqual(report["ignored_cycle_count"], 1)

    def test_main_adoption_scan_reads_worktree_without_ref_graph(self) -> None:
        args = Namespace(
            since_ref="__DEVCTL_EMPTY_TREE_BASE__",
            head_ref="__DEVCTL_WORKTREE_HEAD__",
            format="json",
        )
        guard = Mock()
        guard.read_text_from_ref.side_effect = AssertionError(
            "adoption scan should not read graph inputs from git refs"
        )
        guard.read_text_from_worktree.side_effect = [
            "from dev.scripts import b\n",
            "from dev.scripts import a\n",
        ]
        expected_paths = [Path("dev/scripts/a.py"), Path("dev/scripts/b.py")]

        def _build_cycle_report(*, repo_root, inputs, resolve_guard_config_fn):
            self.assertEqual(repo_root, SCRIPT.REPO_ROOT)
            self.assertEqual(inputs.mode, "adoption-scan")
            self.assertEqual(inputs.graph_inputs.base_paths, [])
            self.assertEqual(inputs.graph_inputs.current_paths, expected_paths)
            self.assertEqual(inputs.base_text_by_path, {})
            self.assertEqual(
                inputs.current_text_by_path,
                {
                    "dev/scripts/a.py": "from dev.scripts import b\n",
                    "dev/scripts/b.py": "from dev.scripts import a\n",
                },
            )
            self.assertIs(resolve_guard_config_fn, SCRIPT._resolve_guard_config)
            return {
                "ok": True,
                "mode": inputs.mode,
                "files_changed": 2,
                "files_considered": 2,
                "files_skipped_non_python": 0,
                "files_skipped_tests": 0,
                "graph_python_files_base": 0,
                "graph_python_files_current": 2,
                "cycles_scanned": 0,
                "violations": [],
                "cycles": [],
                "ignored_cycle_count": 0,
                "ignored_paths": [],
                "totals": {"cyclic_imports_growth": 0},
            }

        override_module_attrs(
            self,
            SCRIPT,
            guard=guard,
            _build_parser=Mock(return_value=Mock(parse_args=Mock(return_value=args))),
            list_changed_paths_with_base_map=Mock(
                return_value=(expected_paths, {path: path for path in expected_paths})
            ),
            coerce_ignored_paths=Mock(return_value=[]),
            list_python_paths_from_ref=Mock(
                side_effect=AssertionError("adoption scan should not use ref graph enumeration")
            ),
            list_python_paths_from_worktree=Mock(return_value=expected_paths),
            build_cycle_report=_build_cycle_report,
        )

        with patch("builtins.print") as mock_print:
            rc = SCRIPT.main()

        self.assertEqual(rc, 0)
        self.assertEqual(guard.validate_ref.call_count, 2)
        self.assertEqual(guard.read_text_from_worktree.call_count, 2)
        self.assertEqual(guard.read_text_from_ref.call_count, 0)
        payload = json.loads(mock_print.call_args.args[0])
        self.assertEqual(payload["mode"], "adoption-scan")
        self.assertIsNone(payload["since_ref"])
        self.assertIsNone(payload["head_ref"])

    def test_script_help_works_in_local_script_mode(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "dev/scripts/checks/check_python_cyclic_imports.py"),
                "--help",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
