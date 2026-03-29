"""Tests for the package-layout shim-debt review probe."""

from __future__ import annotations

import runpy
import sys
from types import ModuleType
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from dev.scripts.devctl.tests.conftest import (
    REPO_ROOT,
    init_temp_repo_root,
    load_repo_module,
)

SCRIPT = load_repo_module(
    "package_layout_probe_compatibility_shims",
    "dev/scripts/checks/package_layout/probe_compatibility_shims.py",
)


class ProbeCompatibilityShimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_temp_repo_root(
            self,
            "dev/scripts/devctl",
            "dev/scripts/devctl/autonomy",
            "dev/scripts/devctl/commands",
            "dev/scripts/devctl/commands/check",
        )

    def _write(self, relative_path: str, text: str = "") -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text or "pass\n", encoding="utf-8")
        return path

    def _root_rules(self, *, max_shims: int = 12) -> tuple[object, ...]:
        return (
            SCRIPT.ShimRootRule(
                root=Path("dev/scripts/devctl"),
                include_globs=("*.py",),
                required_metadata_fields=SCRIPT.STANDARD_SHIM_METADATA_FIELDS,
                max_shims=max_shims,
            ),
        )

    def _family_rules(self, *, max_shims: int = 1) -> tuple[object, ...]:
        return (
            SCRIPT.ShimFamilyRule(
                root=Path("dev/scripts/devctl/commands"),
                flat_prefix="check_",
                namespace_subdir="check",
                required_metadata_fields=SCRIPT.STANDARD_SHIM_METADATA_FIELDS,
                max_shims=max_shims,
            ),
        )

    def _policy(
        self,
        *,
        root_rules: tuple[object, ...] = (),
        family_rules: tuple[object, ...] = (),
        public_contracts: tuple[object, ...] = (),
        usage_scan_exclude_roots: tuple[Path, ...] = (),
    ) -> object:
        return SCRIPT.ShimProbePolicy(
            root_rules=root_rules,
            family_rules=family_rules,
            public_contracts=public_contracts,
            usage_scan_exclude_roots=usage_scan_exclude_roots,
        )

    def _public_contracts(self, *paths: str, glob: str = "") -> tuple[object, ...]:
        contracts = [
            SCRIPT.PublicShimContract(
                path=Path(path),
                reason="stable public shim",
            )
            for path in paths
        ]
        if glob:
            contracts.append(
                SCRIPT.PublicShimContract(
                    glob=glob,
                    reason="stable public shim family",
                )
            )
        return tuple(contracts)

    def test_flags_missing_canonical_metadata(self) -> None:
        path = self._write(
            "dev/scripts/devctl/legacy_run_plan.py",
            (
                '"""Backward-compat shim -- use devctl.autonomy.run_plan instead."""\n'
                "from .autonomy.run_plan import *  # noqa: F401,F403\n"
            ),
        )
        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            current_text_by_path={},
            mode="working-tree",
            policy=self._policy(root_rules=self._root_rules()),
        )

        self.assertEqual(report.files_scanned, 1)
        self.assertEqual(len(report.risk_hints), 1)
        self.assertEqual(report.risk_hints[0].severity, "medium")
        self.assertIn("missing canonical metadata", report.risk_hints[0].signals[0])

    def test_flags_expired_shim(self) -> None:
        self._write("dev/scripts/devctl/autonomy/run_plan.py")
        path = self._write(
            "dev/scripts/devctl/legacy_run_plan.py",
            (
                '"""Backward-compat shim -- use devctl.autonomy.run_plan instead."""\n'
                "# shim-owner: tooling\n"
                "# shim-reason: staged split\n"
                "# shim-expiry: 2026-01-01\n"
                "# shim-target: dev/scripts/devctl/autonomy/run_plan.py\n"
                "from .autonomy.run_plan import *  # noqa: F401,F403\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            current_text_by_path={},
            mode="working-tree",
            policy=self._policy(root_rules=self._root_rules()),
        )

        self.assertTrue(
            any(
                hint.severity == "high" and "past" in hint.signals[0]
                for hint in report.risk_hints
            )
        )

    def test_flags_invalid_expiry(self) -> None:
        self._write("dev/scripts/devctl/autonomy/run_plan.py")
        path = self._write(
            "dev/scripts/devctl/legacy_run_plan.py",
            (
                '"""Backward-compat shim -- use devctl.autonomy.run_plan instead."""\n'
                "# shim-owner: tooling\n"
                "# shim-reason: staged split\n"
                "# shim-expiry: 2026/12/31\n"
                "# shim-target: dev/scripts/devctl/autonomy/run_plan.py\n"
                "from .autonomy.run_plan import *  # noqa: F401,F403\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            current_text_by_path={},
            mode="working-tree",
            policy=self._policy(root_rules=self._root_rules()),
        )

        self.assertTrue(
            any(
                hint.severity == "medium" and "YYYY-MM-DD" in hint.signals[0]
                for hint in report.risk_hints
            )
        )

    def test_flags_unresolved_shim_target(self) -> None:
        path = self._write(
            "dev/scripts/devctl/legacy_run_plan.py",
            (
                '"""Backward-compat shim -- use devctl.autonomy.run_plan instead."""\n'
                "# shim-owner: tooling\n"
                "# shim-reason: staged split\n"
                "# shim-expiry: 2026-12-31\n"
                "# shim-target: dev/scripts/devctl/autonomy/missing.py\n"
                "from .autonomy.run_plan import *  # noqa: F401,F403\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            current_text_by_path={},
            mode="working-tree",
            policy=self._policy(root_rules=self._root_rules()),
        )

        self.assertTrue(
            any(
                hint.severity == "medium" and "does not resolve" in hint.signals[0]
                for hint in report.risk_hints
            )
        )

    def test_flags_shim_heavy_root(self) -> None:
        for idx in range(2):
            self._write(f"dev/scripts/devctl/autonomy/run_plan_{idx}.py")
            self._write(
                f"dev/scripts/devctl/legacy_run_plan_{idx}.py",
                (
                    '"""Backward-compat shim -- use devctl.autonomy.run_plan instead."""\n'
                    "# shim-owner: tooling\n"
                    "# shim-reason: staged split\n"
                    "# shim-expiry: 2026-12-31\n"
                    f"# shim-target: dev/scripts/devctl/autonomy/run_plan_{idx}.py\n"
                    f"from .autonomy.run_plan_{idx} import *  # noqa: F401,F403\n"
                ),
            )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[Path("dev/scripts/devctl/legacy_run_plan_0.py")],
            current_text_by_path={},
            mode="working-tree",
            policy=self._policy(root_rules=self._root_rules(max_shims=1)),
        )

        self.assertTrue(
            any(
                hint.file == "dev/scripts/devctl"
                and "exceed the budget" in hint.signals[0]
                for hint in report.risk_hints
            )
        )

    def test_flags_shim_heavy_family(self) -> None:
        for idx in range(2):
            self._write(f"dev/scripts/devctl/commands/check/legacy_{idx}.py")
            self._write(
                f"dev/scripts/devctl/commands/check_legacy_{idx}.py",
                (
                    '"""Backward-compat shim -- use devctl.commands.check instead."""\n'
                    "# shim-owner: tooling\n"
                    "# shim-reason: staged split\n"
                    "# shim-expiry: 2026-12-31\n"
                    f"# shim-target: dev/scripts/devctl/commands/check/legacy_{idx}.py\n"
                    f"from .check.legacy_{idx} import *  # noqa: F401,F403\n"
                ),
            )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[Path("dev/scripts/devctl/commands/check_legacy_0.py")],
            current_text_by_path={},
            mode="working-tree",
            policy=self._policy(family_rules=self._family_rules(max_shims=1)),
        )

        self.assertEqual(len(report.risk_hints), 1)
        self.assertEqual(report.risk_hints[0].symbol, "check_")
        self.assertIn("family budget", report.risk_hints[0].signals[0])

    def test_build_report_adoption_scan_triggers_root_rules_without_changed_paths(self) -> None:
        self._write("dev/scripts/devctl/autonomy/run_plan.py")
        self._write(
            "dev/scripts/devctl/legacy_run_plan.py",
            (
                '"""Backward-compat shim -- use devctl.autonomy.run_plan instead."""\n'
                "# shim-owner: tooling\n"
                "# shim-reason: staged split\n"
                "# shim-expiry: 2026-01-01\n"
                "# shim-target: dev/scripts/devctl/autonomy/run_plan.py\n"
                "from .autonomy.run_plan import *  # noqa: F401,F403\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[],
            current_text_by_path={},
            mode="adoption-scan",
            policy=self._policy(root_rules=self._root_rules()),
        )

        self.assertEqual(report.mode, "adoption-scan")
        self.assertEqual(report.files_scanned, 1)
        self.assertTrue(any(hint.severity == "high" for hint in report.risk_hints))

    def test_build_report_adoption_scan_triggers_family_rules_without_changed_paths(self) -> None:
        for idx in range(2):
            self._write(f"dev/scripts/devctl/commands/check/legacy_{idx}.py")
            self._write(
                f"dev/scripts/devctl/commands/check_legacy_{idx}.py",
                (
                    '"""Backward-compat shim -- use devctl.commands.check instead."""\n'
                    "# shim-owner: tooling\n"
                    "# shim-reason: staged split\n"
                    "# shim-expiry: 2026-12-31\n"
                    f"# shim-target: dev/scripts/devctl/commands/check/legacy_{idx}.py\n"
                    f"from .check.legacy_{idx} import *  # noqa: F401,F403\n"
                ),
            )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[],
            current_text_by_path={},
            mode="adoption-scan",
            policy=self._policy(family_rules=self._family_rules(max_shims=1)),
        )

        self.assertEqual(report.mode, "adoption-scan")
        self.assertEqual(report.files_scanned, 2)
        self.assertEqual(len(report.risk_hints), 1)
        self.assertEqual(report.risk_hints[0].symbol, "check_")

    def test_build_report_ignores_non_shim_files(self) -> None:
        path = self._write(
            "dev/scripts/devctl/helper.py",
            "def real_implementation() -> str:\n    return 'live code'\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            current_text_by_path={},
            mode="working-tree",
            policy=self._policy(root_rules=self._root_rules()),
        )

        self.assertEqual(report.files_scanned, 0)
        self.assertEqual(report.files_with_hints, 0)
        self.assertEqual(report.risk_hints, [])

    def test_flags_temporary_shim_with_repo_visible_callers(self) -> None:
        self._write("dev/scripts/devctl/autonomy/run_plan.py")
        path = self._write(
            "dev/scripts/devctl/legacy_run_plan.py",
            (
                '"""Backward-compat shim -- use devctl.autonomy.run_plan instead."""\n'
                "# shim-owner: tooling\n"
                "# shim-reason: staged split\n"
                "# shim-expiry: 2026-12-31\n"
                "# shim-target: dev/scripts/devctl/autonomy/run_plan.py\n"
                "from .autonomy.run_plan import *\n"
            ),
        )
        self._write(
            "dev/scripts/devctl/consumer.py",
            "from .legacy_run_plan import run_plan\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            current_text_by_path={},
            mode="working-tree",
            policy=self._policy(root_rules=self._root_rules()),
        )

        self.assertEqual(len(report.risk_hints), 1)
        self.assertEqual(report.risk_hints[0].severity, "medium")
        self.assertIn("repo-visible caller/reference", report.risk_hints[0].signals[0])

    def test_flags_temporary_shim_with_no_repo_visible_callers(self) -> None:
        self._write("dev/scripts/devctl/autonomy/run_plan.py")
        path = self._write(
            "dev/scripts/devctl/legacy_run_plan.py",
            (
                '"""Backward-compat shim -- use devctl.autonomy.run_plan instead."""\n'
                "# shim-owner: tooling\n"
                "# shim-reason: staged split\n"
                "# shim-expiry: 2026-12-31\n"
                "# shim-target: dev/scripts/devctl/autonomy/run_plan.py\n"
                "from .autonomy.run_plan import *\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            current_text_by_path={},
            mode="working-tree",
            policy=self._policy(root_rules=self._root_rules()),
        )

        self.assertEqual(len(report.risk_hints), 1)
        self.assertEqual(report.risk_hints[0].severity, "high")
        self.assertIn("no repo-visible callers", report.risk_hints[0].signals[0])

    def test_public_allowlist_excludes_stable_shims_from_temporary_budget(self) -> None:
        for idx in range(2):
            self._write(f"dev/scripts/devctl/public/public_entry_{idx}.py")
            self._write(
                f"dev/scripts/devctl/public_entry_{idx}.py",
                (
                    '"""Backward-compat shim -- use devctl.public.public_entry instead."""\n'
                    "# shim-owner: tooling\n"
                    "# shim-reason: stable public seam\n"
                    "# shim-expiry: 2026-12-31\n"
                    f"# shim-target: dev/scripts/devctl/public/public_entry_{idx}.py\n"
                    f"from .public.public_entry_{idx} import *\n"
                ),
            )
        self._write("dev/scripts/devctl/autonomy/run_plan.py")
        path = self._write(
            "dev/scripts/devctl/legacy_run_plan.py",
            (
                '"""Backward-compat shim -- use devctl.autonomy.run_plan instead."""\n'
                "# shim-owner: tooling\n"
                "# shim-reason: staged split\n"
                "# shim-expiry: 2026-12-31\n"
                "# shim-target: dev/scripts/devctl/autonomy/run_plan.py\n"
                "from .autonomy.run_plan import *\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            current_text_by_path={},
            mode="working-tree",
            policy=self._policy(
                root_rules=self._root_rules(max_shims=1),
                public_contracts=self._public_contracts(
                    glob="dev/scripts/devctl/public_entry_*.py"
                ),
            ),
        )

        self.assertEqual(len(report.risk_hints), 1)
        self.assertFalse(
            any("exceed the budget" in hint.signals[0] for hint in report.risk_hints)
        )
        self.assertIn("no repo-visible callers", report.risk_hints[0].signals[0])

    def test_usage_scan_exclude_roots_ignore_generated_report_refs(self) -> None:
        self._write("dev/scripts/devctl/autonomy/run_plan.py")
        path = self._write(
            "dev/scripts/devctl/legacy_run_plan.py",
            (
                '"""Backward-compat shim -- use devctl.autonomy.run_plan instead."""\n'
                "# shim-owner: tooling\n"
                "# shim-reason: staged split\n"
                "# shim-expiry: 2026-12-31\n"
                "# shim-target: dev/scripts/devctl/autonomy/run_plan.py\n"
                "from .autonomy.run_plan import *\n"
            ),
        )
        self._write(
            "dev/reports/probes/latest.md",
            "See dev/scripts/devctl/legacy_run_plan.py for legacy callers.\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            current_text_by_path={},
            mode="working-tree",
            policy=self._policy(
                root_rules=self._root_rules(),
                usage_scan_exclude_roots=(Path("dev/reports"),),
            ),
        )

        self.assertEqual(len(report.risk_hints), 1)
        self.assertEqual(report.risk_hints[0].severity, "high")
        self.assertIn("no repo-visible callers", report.risk_hints[0].signals[0])

    def test_root_wrapper_entrypoint_runs_package_module_main(self) -> None:
        checks_dir = REPO_ROOT / "dev/scripts/checks"
        checks_dir_text = str(checks_dir)
        if checks_dir_text not in sys.path:
            sys.path.insert(0, checks_dir_text)
            self.addCleanup(sys.path.remove, checks_dir_text)
        __import__("package_layout")

        fake_module = ModuleType("package_layout.probe_compatibility_shims")
        fake_main = MagicMock(return_value=7)
        fake_module.main = fake_main

        with patch.dict(
            sys.modules,
            {"package_layout.probe_compatibility_shims": fake_module},
            clear=False,
        ):
            with self.assertRaises(SystemExit) as exc:
                runpy.run_path(
                    str(REPO_ROOT / "dev/scripts/checks/probe_compatibility_shims.py"),
                    run_name="__main__",
                )
            wrapper = load_repo_module(
                "probe_compatibility_shims_wrapper",
                "dev/scripts/checks/probe_compatibility_shims.py",
                register_in_sys_modules=False,
            )

        fake_main.assert_called_once_with()
        self.assertEqual(exc.exception.code, 7)
        self.assertIs(wrapper.main, fake_main)


if __name__ == "__main__":
    unittest.main()
