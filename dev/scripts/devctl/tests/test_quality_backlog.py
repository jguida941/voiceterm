"""Tests for quality backlog scoring, models, and priority assembly."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.quality_backlog.models import (
    ABSOLUTE_CHECKS,
    CODE_SHAPE_REASON_WEIGHTS,
    COMPILER_WARNING_WEIGHTS,
    FACADE_WRAPPER_WEIGHTS,
    FUNCTION_DUPLICATION_WEIGHTS,
    LINT_DEBT_WEIGHTS,
    RUST_BEST_PRACTICE_WEIGHTS,
    SECURITY_FOOTGUN_WEIGHTS,
    SERDE_COMPATIBILITY_WEIGHTS,
    STRUCTURAL_SIMILARITY_WEIGHTS,
    SUGGESTIONS_BY_SIGNAL_PREFIX,
    InventoryRow,
    PriorityRow,
    severity_from_score,
)
from dev.scripts.devctl.quality_backlog.priorities import (
    add_signal,
    build_priorities,
    ensure_priority,
    ingest_code_shape_signals,
    ingest_compiler_warning_signals,
    ingest_growth_signals,
    ingest_inventory_signals,
)


class SeverityFromScoreTests(unittest.TestCase):
    def test_critical_at_700(self) -> None:
        self.assertEqual(severity_from_score(700), "critical")

    def test_critical_above_700(self) -> None:
        self.assertEqual(severity_from_score(1200), "critical")

    def test_high_at_350(self) -> None:
        self.assertEqual(severity_from_score(350), "high")

    def test_high_just_below_700(self) -> None:
        self.assertEqual(severity_from_score(699), "high")

    def test_medium_at_140(self) -> None:
        self.assertEqual(severity_from_score(140), "medium")

    def test_medium_just_below_350(self) -> None:
        self.assertEqual(severity_from_score(349), "medium")

    def test_low_below_140(self) -> None:
        self.assertEqual(severity_from_score(139), "low")

    def test_low_at_zero(self) -> None:
        self.assertEqual(severity_from_score(0), "low")


class PriorityRowTests(unittest.TestCase):
    def test_add_signal_accumulates_score(self) -> None:
        row = PriorityRow(path="src/main.rs", language=".rs")
        add_signal(row, signal="shape:hard", score=200)
        add_signal(row, signal="shape:soft", score=100)
        self.assertEqual(row.score, 300)
        self.assertEqual(row.signals, {"shape:hard", "shape:soft"})

    def test_add_signal_matches_suggestion_prefix(self) -> None:
        row = PriorityRow(path="src/main.rs", language=".rs")
        add_signal(row, signal="shape:hard", score=200)
        self.assertIn(
            "Split oversized file into focused modules and move unrelated responsibilities out.",
            row.suggested_fixes,
        )

    def test_add_signal_no_suggestion_for_unknown_prefix(self) -> None:
        row = PriorityRow(path="src/main.rs", language=".rs")
        add_signal(row, signal="unknown:test", score=50)
        self.assertEqual(row.suggested_fixes, set())

    def test_finalize_sets_severity(self) -> None:
        row = PriorityRow(path="src/main.rs", language=".rs", score=400)
        row.finalize()
        self.assertEqual(row.severity, "high")

    def test_to_dict_round_trip(self) -> None:
        row = PriorityRow(path="src/main.rs", language=".rs")
        add_signal(row, signal="shape:hard", score=500)
        row.finalize()
        d = row.to_dict()
        self.assertEqual(d["path"], "src/main.rs")
        self.assertEqual(d["score"], 500)
        self.assertEqual(d["severity"], "high")
        self.assertIn("shape:hard", d["signals"])


class EnsurePriorityTests(unittest.TestCase):
    def test_creates_new_row(self) -> None:
        priorities: dict[str, PriorityRow] = {}
        row = ensure_priority(priorities, "src/lib.rs")
        self.assertEqual(row.path, "src/lib.rs")
        self.assertEqual(row.language, ".rs")
        self.assertIn("src/lib.rs", priorities)

    def test_returns_existing_row(self) -> None:
        priorities: dict[str, PriorityRow] = {}
        row1 = ensure_priority(priorities, "src/lib.rs")
        row1.score = 100
        row2 = ensure_priority(priorities, "src/lib.rs")
        self.assertIs(row1, row2)
        self.assertEqual(row2.score, 100)


class IngestInventorySignalsTests(unittest.TestCase):
    def test_hard_limit_signal(self) -> None:
        priorities: dict[str, PriorityRow] = {}
        rows = [
            InventoryRow(
                path="src/big.rs", language=".rs", line_count=1500,
                soft_limit=900, hard_limit=1400, pressure_pct=107.1,
                status="exceeds_hard", score=320, policy_source=None,
            ),
        ]
        ingest_inventory_signals(priorities, rows)
        self.assertIn("src/big.rs", priorities)
        self.assertIn("shape:hard", priorities["src/big.rs"].signals)

    def test_zero_score_rows_skipped(self) -> None:
        priorities: dict[str, PriorityRow] = {}
        rows = [
            InventoryRow(
                path="src/ok.rs", language=".rs", line_count=100,
                soft_limit=900, hard_limit=1400, pressure_pct=11.1,
                status="ok", score=0, policy_source=None,
            ),
        ]
        ingest_inventory_signals(priorities, rows)
        self.assertEqual(len(priorities), 0)


class IngestCodeShapeSignalsTests(unittest.TestCase):
    def test_violation_scored(self) -> None:
        priorities: dict[str, PriorityRow] = {}
        report = {
            "violations": [
                {"path": "src/event_loop.rs", "reason": "crossed_hard_limit"},
            ],
        }
        ingest_code_shape_signals(priorities, report)
        self.assertIn("src/event_loop.rs", priorities)
        self.assertEqual(priorities["src/event_loop.rs"].score, 460)

    def test_unknown_reason_uses_default_weight(self) -> None:
        priorities: dict[str, PriorityRow] = {}
        report = {
            "violations": [
                {"path": "src/foo.rs", "reason": "never_seen_before"},
            ],
        }
        ingest_code_shape_signals(priorities, report)
        self.assertEqual(priorities["src/foo.rs"].score, 140)

    def test_empty_violations_no_crash(self) -> None:
        priorities: dict[str, PriorityRow] = {}
        ingest_code_shape_signals(priorities, {"violations": []})
        self.assertEqual(len(priorities), 0)
        ingest_code_shape_signals(priorities, {})
        self.assertEqual(len(priorities), 0)


class IngestGrowthSignalsTests(unittest.TestCase):
    def test_growth_counts_multiplied_by_weight(self) -> None:
        priorities: dict[str, PriorityRow] = {}
        report = {
            "violations": [
                {"path": "src/auth.rs", "growth": {"allow_attrs_growth": 3}},
            ],
        }
        ingest_growth_signals(
            priorities, report,
            signal_prefix="rust_lint_debt",
            category_weights=LINT_DEBT_WEIGHTS,
        )
        expected_score = 140 * 3
        self.assertEqual(priorities["src/auth.rs"].score, expected_score)

    def test_unknown_category_uses_default_weight(self) -> None:
        priorities: dict[str, PriorityRow] = {}
        report = {
            "violations": [
                {"path": "src/foo.rs", "growth": {"mystery_category": 2}},
            ],
        }
        ingest_growth_signals(
            priorities, report,
            signal_prefix="test",
            category_weights={},
        )
        self.assertEqual(priorities["src/foo.rs"].score, 120 * 2)

    def test_zero_count_skipped(self) -> None:
        priorities: dict[str, PriorityRow] = {}
        report = {
            "violations": [
                {"path": "src/foo.rs", "growth": {"some_cat": 0}},
            ],
        }
        ingest_growth_signals(
            priorities, report,
            signal_prefix="test",
            category_weights={},
        )
        self.assertEqual(len(priorities), 0)


class IngestCompilerWarningSignalsTests(unittest.TestCase):
    def test_warning_scored(self) -> None:
        priorities: dict[str, PriorityRow] = {}
        report = {
            "warnings": [
                {"path": "src/main.rs", "code": "unused_imports"},
            ],
        }
        ingest_compiler_warning_signals(priorities, report)
        self.assertEqual(priorities["src/main.rs"].score, 40)
        self.assertIn("rust_warning:unused_imports", priorities["src/main.rs"].signals)

    def test_unknown_code_uses_default_weight(self) -> None:
        priorities: dict[str, PriorityRow] = {}
        report = {
            "warnings": [
                {"path": "src/main.rs", "code": "new_lint"},
            ],
        }
        ingest_compiler_warning_signals(priorities, report)
        self.assertEqual(priorities["src/main.rs"].score, 50)


class BuildPrioritiesTests(unittest.TestCase):
    def test_severity_counts_populated(self) -> None:
        inventory_rows = [
            InventoryRow(
                path="src/big.rs", language=".rs", line_count=1500,
                soft_limit=900, hard_limit=1400, pressure_pct=107.1,
                status="exceeds_hard", score=500, policy_source=None,
            ),
        ]
        checks = {
            "code_shape": {
                "report": {
                    "violations": [
                        {"path": "src/big.rs", "reason": "crossed_hard_limit"},
                    ],
                },
            },
        }
        priorities, severity_counts = build_priorities(
            inventory_rows=inventory_rows,
            checks=checks,
            top_n=10,
        )
        self.assertTrue(len(priorities) > 0)
        total = sum(severity_counts.values())
        self.assertGreater(total, 0)

    def test_top_n_limits_results(self) -> None:
        rows = [
            InventoryRow(
                path=f"src/file_{i}.rs", language=".rs", line_count=1000 + i,
                soft_limit=900, hard_limit=1400, pressure_pct=90.0 + i,
                status="exceeds_soft", score=200 + i, policy_source=None,
            )
            for i in range(10)
        ]
        priorities, _ = build_priorities(
            inventory_rows=rows,
            checks={},
            top_n=3,
        )
        self.assertEqual(len(priorities), 3)

    def test_rows_sorted_by_descending_score(self) -> None:
        rows = [
            InventoryRow(
                path="src/low.rs", language=".rs", line_count=950,
                soft_limit=900, hard_limit=1400, pressure_pct=80.0,
                status="exceeds_soft", score=100, policy_source=None,
            ),
            InventoryRow(
                path="src/high.rs", language=".rs", line_count=1600,
                soft_limit=900, hard_limit=1400, pressure_pct=120.0,
                status="exceeds_hard", score=600, policy_source=None,
            ),
        ]
        priorities, _ = build_priorities(
            inventory_rows=rows,
            checks={},
            top_n=10,
        )
        self.assertEqual(priorities[0]["path"], "src/high.rs")
        self.assertGreater(priorities[0]["score"], priorities[1]["score"])


class WeightTablesTests(unittest.TestCase):
    """Verify weight table constants are internally consistent."""

    def test_absolute_checks_has_ten_entries(self) -> None:
        self.assertEqual(len(ABSOLUTE_CHECKS), 10)

    def test_all_check_keys_unique(self) -> None:
        keys = [check.key for check in ABSOLUTE_CHECKS]
        self.assertEqual(len(keys), len(set(keys)))

    def test_code_shape_weights_all_positive(self) -> None:
        for reason, weight in CODE_SHAPE_REASON_WEIGHTS.items():
            self.assertGreater(weight, 0, f"{reason} has non-positive weight")

    def test_security_footgun_weight_is_highest_growth_weight(self) -> None:
        all_growth_weights = [
            *LINT_DEBT_WEIGHTS.values(),
            *RUST_BEST_PRACTICE_WEIGHTS.values(),
            *STRUCTURAL_SIMILARITY_WEIGHTS.values(),
            *FACADE_WRAPPER_WEIGHTS.values(),
            *SERDE_COMPATIBILITY_WEIGHTS.values(),
            *FUNCTION_DUPLICATION_WEIGHTS.values(),
            *SECURITY_FOOTGUN_WEIGHTS.values(),
        ]
        max_weight = max(all_growth_weights)
        self.assertEqual(
            max_weight,
            SECURITY_FOOTGUN_WEIGHTS["footgun_growth"],
            "Security footgun should carry the highest growth weight",
        )

    def test_suggestions_cover_all_signal_families(self) -> None:
        suggestion_prefixes = {prefix for prefix, _ in SUGGESTIONS_BY_SIGNAL_PREFIX}
        expected = {
            "shape:hard", "shape:soft",
            "code_shape:function_exceeds_max_lines",
            "rust_best:result_string_types",
            "rust_panic:unallowlisted_panic_calls",
            "rust_warning:unused_imports",
            "rust_warning:deprecated",
            "structural_similarity",
            "facade_wrappers",
            "serde_compat",
            "function_dup",
            "security_footgun",
        }
        self.assertEqual(suggestion_prefixes, expected)


if __name__ == "__main__":
    unittest.main()
