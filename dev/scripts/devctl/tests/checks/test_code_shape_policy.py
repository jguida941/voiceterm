"""Tests for code-shape override warning policy."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.tests.conftest import load_repo_module, override_module_attrs

SCRIPT = load_repo_module(
    "code_shape_policy",
    "dev/scripts/checks/code_shape_policy.py",
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

        warnings = SCRIPT.validate_override_caps()
        warning_by_path = {warning["path"]: warning for warning in warnings}
        explicit_records = SCRIPT.collect_override_cap_records(
            overrides=overrides,
            language_policies=language_policies,
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


if __name__ == "__main__":
    unittest.main()
