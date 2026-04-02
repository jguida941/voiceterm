"""Tests for code-shape override warning policy."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from dev.scripts.devctl.tests.conftest import load_repo_module, override_module_attrs

SCRIPT = load_repo_module(
    "code_shape_policy",
    "dev/scripts/checks/code_shape/code_shape_policy.py",
)


class CodeShapePolicyTests(unittest.TestCase):
    def test_validate_override_caps_flags_soft_and_hard_thresholds(self) -> None:
        overrides = {
            "rust/src/bin/voiceterm/soft.rs": SCRIPT.ShapePolicy(
                soft_limit=2701,
                hard_limit=1400,
                oversize_growth_limit=0,
                hard_lock_growth_limit=0,
            ),
            "rust/src/bin/voiceterm/hard.rs": SCRIPT.ShapePolicy(
                soft_limit=900,
                hard_limit=2801,
                oversize_growth_limit=0,
                hard_lock_growth_limit=0,
            ),
        }
        language_policies = {
            ".rs": SCRIPT.ShapePolicy(
                soft_limit=900,
                hard_limit=1400,
                oversize_growth_limit=40,
                hard_lock_growth_limit=0,
            )
        }

        override_module_attrs(
            self,
            SCRIPT,
            PATH_POLICY_OVERRIDES=overrides,
            LANGUAGE_POLICIES=language_policies,
        )

        with TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            for relative in overrides:
                target = repo_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("// present\n", encoding="utf-8")

            warnings = SCRIPT.validate_override_caps(repo_root=repo_root)
            warning_by_path = {warning["path"]: warning for warning in warnings}
            explicit_records = SCRIPT.collect_override_cap_records(
                overrides=overrides,
                language_policies=language_policies,
                repo_root=repo_root,
            )

        self.assertEqual(len(warnings), 2)
        self.assertEqual(explicit_records, warnings)
        self.assertEqual(
            warning_by_path["rust/src/bin/voiceterm/soft.rs"]["triggered_caps"],
            ["soft_limit"],
        )
        self.assertGreater(warning_by_path["rust/src/bin/voiceterm/soft.rs"]["soft_ratio"], 3.0)
        self.assertIn("3.0x the soft cap", warning_by_path["rust/src/bin/voiceterm/soft.rs"]["detail"])
        self.assertEqual(
            warning_by_path["rust/src/bin/voiceterm/hard.rs"]["triggered_caps"],
            ["hard_limit"],
        )
        self.assertGreater(warning_by_path["rust/src/bin/voiceterm/hard.rs"]["hard_ratio"], 2.0)
        self.assertIn("2.0x the hard cap", warning_by_path["rust/src/bin/voiceterm/hard.rs"]["detail"])

    def test_policy_for_path_uses_stable_wrapper_override_for_package_target(self) -> None:
        wrapper = "dev/scripts/checks/check_code_shape.py"
        target = Path("dev/scripts/checks/code_shape/check_code_shape.py")
        overrides = {
            wrapper: SCRIPT.ShapePolicy(
                soft_limit=675,
                hard_limit=725,
                oversize_growth_limit=30,
                hard_lock_growth_limit=0,
            )
        }

        override_module_attrs(self, SCRIPT, PATH_POLICY_OVERRIDES=overrides)
        SCRIPT._compatibility_redirect_targets.cache_clear()
        self.addCleanup(SCRIPT._compatibility_redirect_targets.cache_clear)

        with patch.object(
            SCRIPT,
            "collect_compatibility_redirects",
            return_value=[
                {
                    "path": wrapper,
                    "resolved_target": target.as_posix(),
                }
            ],
        ):
            policy, source = SCRIPT.policy_for_path(target)

        self.assertIsNotNone(policy)
        self.assertEqual(source, f"path_override:{wrapper}")
        self.assertEqual(policy.soft_limit, 675)

    def test_collect_override_cap_records_skips_missing_paths(self) -> None:
        overrides = {
            "pkg/existing.py": SCRIPT.ShapePolicy(
                soft_limit=1400,
                hard_limit=1500,
                oversize_growth_limit=0,
                hard_lock_growth_limit=0,
            ),
            "pkg/missing.py": SCRIPT.ShapePolicy(
                soft_limit=1400,
                hard_limit=1500,
                oversize_growth_limit=0,
                hard_lock_growth_limit=0,
            ),
        }
        language_policies = {
            ".py": SCRIPT.ShapePolicy(
                soft_limit=350,
                hard_limit=650,
                oversize_growth_limit=25,
                hard_lock_growth_limit=0,
            )
        }

        with TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            existing = repo_root / "pkg" / "existing.py"
            existing.parent.mkdir(parents=True)
            existing.write_text("print('ok')\n", encoding="utf-8")

            warnings = SCRIPT.collect_override_cap_records(
                overrides=overrides,
                language_policies=language_policies,
                repo_root=repo_root,
            )

        self.assertEqual([warning["path"] for warning in warnings], ["pkg/existing.py"])

    def test_build_function_exception_key_uses_stable_wrapper_path(self) -> None:
        wrapper = "dev/scripts/checks/check_code_shape.py"
        target = Path("dev/scripts/checks/code_shape/check_code_shape.py")

        SCRIPT._compatibility_redirect_targets.cache_clear()
        self.addCleanup(SCRIPT._compatibility_redirect_targets.cache_clear)

        with patch.object(
            SCRIPT,
            "collect_compatibility_redirects",
            return_value=[
                {
                    "path": wrapper,
                    "resolved_target": target.as_posix(),
                }
            ],
        ):
            key = SCRIPT.build_function_exception_key(target, "main")

        self.assertEqual(key, f"{wrapper}::main")


if __name__ == "__main__":
    unittest.main()
