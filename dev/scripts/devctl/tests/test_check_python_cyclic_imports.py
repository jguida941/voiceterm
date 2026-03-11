"""Tests for check_python_cyclic_imports guard."""

from __future__ import annotations

import unittest
from pathlib import Path

from dev.scripts.devctl.tests.conftest import (
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


if __name__ == "__main__":
    unittest.main()
