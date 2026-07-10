"""Tests for the governance quality-feedback package."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from dev.scripts.devctl.governance.quality_feedback.per_check_score import (
    build_check_quality_scores,
)
from dev.scripts.devctl.governance.quality_feedback.improvement_tracker import (
    compute_improvement_delta,
)
from dev.scripts.devctl.governance.quality_feedback.halstead import (
    analyze_file,
    analyze_directory,
    summarize_halstead,
)
from dev.scripts.devctl.governance.quality_feedback.models import (
    CheckQualityScore,
    HalsteadFileMetrics,
    QUALITY_FEEDBACK_CONTRACT_ID,
    QUALITY_FEEDBACK_SCHEMA_VERSION,
)


class TestPerCheckScore(unittest.TestCase):
    """Tests for per-check quality scoring."""

    def test_groups_by_check_id_and_signal_type(self) -> None:
        """Two rows with the same check_id but different signal_types must
        produce two separate CheckQualityScore entries, not one merged bucket.
        """
        rows: list[dict[str, Any]] = [
            {"check_id": "probe_magic_numbers", "signal_type": "probe", "verdict": "fixed"},
            {"check_id": "probe_magic_numbers", "signal_type": "probe", "verdict": "false_positive"},
            {"check_id": "probe_magic_numbers", "signal_type": "guard", "verdict": "fixed"},
        ]
        scores = build_check_quality_scores(rows)
        self.assertEqual(len(scores), 2)
        probe_score = next(s for s in scores if s.signal_type == "probe")
        guard_score = next(s for s in scores if s.signal_type == "guard")
        self.assertEqual(probe_score.total_findings, 2)
        self.assertEqual(probe_score.false_positive_count, 1)
        self.assertEqual(guard_score.total_findings, 1)
        self.assertEqual(guard_score.false_positive_count, 0)

    def test_empty_input_returns_empty(self) -> None:
        scores = build_check_quality_scores([])
        self.assertEqual(scores, [])

    def test_precision_and_fp_rate(self) -> None:
        rows: list[dict[str, Any]] = [
            {"check_id": "c1", "signal_type": "probe", "verdict": "fixed"},
            {"check_id": "c1", "signal_type": "probe", "verdict": "fixed"},
            {"check_id": "c1", "signal_type": "probe", "verdict": "false_positive"},
        ]
        scores = build_check_quality_scores(rows)
        self.assertEqual(len(scores), 1)
        s = scores[0]
        self.assertEqual(s.true_positive_count, 2)
        self.assertEqual(s.false_positive_count, 1)
        self.assertAlmostEqual(s.precision_pct, 66.67, places=1)
        self.assertAlmostEqual(s.fp_rate_pct, 33.33, places=1)
        self.assertEqual(s.cleanup_rate_pct, 100.0)


class TestImprovementTracker(unittest.TestCase):
    """Tests for snapshot delta computation."""

    def test_no_previous_snapshot_returns_zero_delta(self) -> None:
        delta = compute_improvement_delta(
            current_score=75.0,
            current_check_scores=[],
            previous_snapshot=None,
        )
        self.assertEqual(delta.overall_score_delta, 0.0)
        self.assertIsNone(delta.previous_score)
        self.assertEqual(delta.current_score, 75.0)

    def test_delta_uses_composite_key(self) -> None:
        """Delta lookup must key by (check_id, signal_type) so two different
        signal families with the same check_id do not merge incorrectly.
        """
        previous: dict[str, Any] = {
            "maintainability_score": {"overall": 70.0},
            "check_quality_scores": [
                {"check_id": "c1", "signal_type": "probe", "precision_pct": 80.0},
                {"check_id": "c1", "signal_type": "guard", "precision_pct": 50.0},
            ],
        }
        current_scores = [
            CheckQualityScore(
                check_id="c1",
                signal_type="probe",
                total_findings=10,
                true_positive_count=9,
                false_positive_count=1,
                precision_pct=90.0,
                fp_rate_pct=10.0,
                cleanup_rate_pct=100.0,
            ),
            CheckQualityScore(
                check_id="c1",
                signal_type="guard",
                total_findings=5,
                true_positive_count=3,
                false_positive_count=2,
                precision_pct=40.0,
                fp_rate_pct=40.0,
                cleanup_rate_pct=66.67,
            ),
        ]
        delta = compute_improvement_delta(
            current_score=80.0,
            current_check_scores=current_scores,
            previous_snapshot=previous,
        )
        self.assertEqual(delta.overall_score_delta, 10.0)
        self.assertEqual(len(delta.improved_checks), 1)
        self.assertEqual(delta.improved_checks[0]["check_id"], "c1")
        self.assertEqual(len(delta.degraded_checks), 1)
        self.assertEqual(delta.degraded_checks[0]["check_id"], "c1")


class TestHalstead(unittest.TestCase):
    """Tests for Halstead metrics computation."""

    def test_analyze_python_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            py_file = root / "sample.py"
            py_file.write_text("def hello():\n    return 42\n", encoding="utf-8")
            metrics = analyze_file(py_file)
            self.assertIsNotNone(metrics)
            self.assertGreater(metrics.loc, 0)
            self.assertGreater(metrics.vocabulary, 0)

    def test_analyze_file_with_relative_to_emits_repo_relative_path(self) -> None:
        """When relative_to is given, the stored path must be repo-relative
        POSIX, not an absolute filesystem path.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subdir = root / "src"
            subdir.mkdir()
            py_file = subdir / "mod.py"
            py_file.write_text("x = 1\n", encoding="utf-8")
            metrics = analyze_file(py_file, relative_to=root)
            self.assertIsNotNone(metrics)
            self.assertEqual(metrics.path, "src/mod.py")
            self.assertFalse(metrics.path.startswith("/"))

    def test_analyze_directory_passes_relative_to(self) -> None:
        """analyze_directory should produce repo-relative paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            py_file = root / "app.py"
            py_file.write_text("print('hello')\n", encoding="utf-8")
            results = analyze_directory(root)
            self.assertTrue(len(results) >= 1)
            for m in results:
                self.assertFalse(m.path.startswith("/"), f"absolute path leaked: {m.path}")

    def test_summarize_empty(self) -> None:
        summary = summarize_halstead([])
        self.assertEqual(summary.files_scanned, 0)
        self.assertEqual(summary.total_loc, 0)

    def test_unsupported_extension_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = Path(tmpdir) / "readme.txt"
            txt_file.write_text("hello", encoding="utf-8")
            self.assertIsNone(analyze_file(txt_file))


class TestMaintainabilityScore(unittest.TestCase):
    """Tests for composite score correctness."""

    def test_unavailable_dimensions_do_not_inflate_score(self) -> None:
        """When no evidence is loaded, unavailable dimensions must not
        contribute default-perfect values to the composite score.
        """
        from dev.scripts.devctl.governance.quality_feedback.maintainability_score import (
            ScoreInputs,
            compute_maintainability_score,
        )
        # All dimensions unavailable — score should be 0, not 100.
        inputs = ScoreInputs()
        result = compute_maintainability_score(inputs)
        self.assertEqual(result.overall, 0.0)

    def test_only_available_dimensions_participate(self) -> None:
        """Only dimensions marked available should contribute."""
        from dev.scripts.devctl.governance.quality_feedback.maintainability_score import (
            ScoreInputs,
            compute_maintainability_score,
        )
        inputs = ScoreInputs(
            avg_halstead_mi=80.0,
            halstead_mi_available=True,
            cleanup_rate_pct=60.0,
            cleanup_rate_available=True,
        )
        result = compute_maintainability_score(inputs)
        # Only halstead_mi (80 * 0.20) and cleanup_rate (60 * 0.15) are available.
        # Renormalized: (80*0.20 + 60*0.15) / (0.20 + 0.15) = (16+9) / 0.35 = 71.43
        self.assertAlmostEqual(result.overall, 71.43, places=1)
        self.assertGreater(result.overall, 0.0)
        self.assertLess(result.overall, 100.0)

    def test_finding_density_uses_open_positive_findings(self) -> None:
        """The finding_density sub-score should use open_positive_findings
        (not a field called high_findings) to measure real open issues.
        """
        from dev.scripts.devctl.governance.quality_feedback.maintainability_score import (
            ScoreInputs,
            compute_maintainability_score,
        )
        inputs = ScoreInputs(
            open_positive_findings=10,
            total_source_files=100,
            finding_density_available=True,
        )
        result = compute_maintainability_score(inputs)
        finding_entry = next(e for e in result.sub_scores if e.name == "finding_density")
        self.assertGreater(finding_entry.value, 0.0)
        self.assertLess(finding_entry.value, 100.0)

    def test_sub_score_weights_use_finding_density_key(self) -> None:
        """SUB_SCORE_WEIGHTS must use 'finding_density', not 'probe_density'."""
        from dev.scripts.devctl.governance.quality_feedback.models import SUB_SCORE_WEIGHTS
        self.assertIn("finding_density", SUB_SCORE_WEIGHTS)
        self.assertNotIn("probe_density", SUB_SCORE_WEIGHTS)

    def test_guard_issue_burden_unavailable_when_no_guard_checks(self) -> None:
        """guard_issue_burden must be unavailable when zero guard-type findings exist."""
        from dev.scripts.devctl.governance.quality_feedback.report_builder import (
            _build_score_inputs,
        )
        from unittest.mock import MagicMock

        review_stats = MagicMock()
        review_stats.total_findings = 0
        review_stats.cleanup_rate_pct = 0.0
        review_stats.positive_finding_count = 0
        review_stats.open_finding_count = 0
        review_stats.fixed_count = 0
        review_stats.by_check_id = []
        review_stats.by_signal_type = []

        ext_stats = MagicMock()
        halstead = MagicMock()
        halstead.files_scanned = 10
        halstead.avg_maintainability_index = 50.0

        inputs = _build_score_inputs(
            repo_root=Path("."),
            review_stats=review_stats,
            ext_stats=ext_stats,
            halstead_summary=halstead,
        )
        self.assertFalse(inputs.guard_issue_burden_available)
        self.assertFalse(inputs.finding_density_available)
        self.assertFalse(inputs.cleanup_rate_available)
        self.assertTrue(inputs.halstead_mi_available)


class TestLensScores(unittest.TestCase):
    """Tests for the 3-lens quality model."""

    def test_lenses_are_produced(self) -> None:
        from dev.scripts.devctl.governance.quality_feedback.maintainability_score import (
            ScoreInputs,
            compute_maintainability_score,
        )
        inputs = ScoreInputs(
            avg_halstead_mi=60.0, halstead_mi_available=True,
            cleanup_rate_pct=80.0, cleanup_rate_available=True,
            open_guard_findings=2, guard_count=10, guard_issue_burden_available=True,
        )
        result = compute_maintainability_score(inputs)
        self.assertEqual(len(result.lenses), 3)
        lens_names = [l.lens for l in result.lenses]
        self.assertIn("code_health", lens_names)
        self.assertIn("governance_quality", lens_names)
        self.assertIn("operability", lens_names)

    def test_unavailable_lens_has_no_score(self) -> None:
        from dev.scripts.devctl.governance.quality_feedback.maintainability_score import (
            ScoreInputs,
            compute_maintainability_score,
        )
        inputs = ScoreInputs(
            avg_halstead_mi=70.0, halstead_mi_available=True,
        )
        result = compute_maintainability_score(inputs)
        code_health = next(l for l in result.lenses if l.lens == "code_health")
        operability = next(l for l in result.lenses if l.lens == "operability")
        governance = next(l for l in result.lenses if l.lens == "governance_quality")
        self.assertTrue(code_health.available)
        self.assertGreater(code_health.score, 0.0)
        self.assertFalse(operability.available)
        self.assertEqual(operability.grade, "n/a")
        self.assertFalse(governance.available)

    def test_lens_to_dict(self) -> None:
        from dev.scripts.devctl.governance.quality_feedback.models import LensScore
        lens = LensScore(
            lens="test_lens", score=75.0, grade="C",
            available=True, sub_scores=(),
        )
        d = lens.to_dict()
        self.assertEqual(d["lens"], "test_lens")
        self.assertEqual(d["score"], 75.0)
        self.assertTrue(d["available"])


class TestModelContracts(unittest.TestCase):
    """Tests for contract constants and serialization."""

    def test_contract_constants(self) -> None:
        self.assertEqual(QUALITY_FEEDBACK_CONTRACT_ID, "QualityFeedbackSnapshot")
        self.assertEqual(QUALITY_FEEDBACK_SCHEMA_VERSION, 1)

    def test_check_quality_score_to_dict(self) -> None:
        score = CheckQualityScore(
            check_id="probe_x",
            signal_type="probe",
            total_findings=10,
            true_positive_count=8,
            false_positive_count=2,
            precision_pct=80.0,
            fp_rate_pct=20.0,
            cleanup_rate_pct=100.0,
        )
        d = score.to_dict()
        self.assertEqual(d["check_id"], "probe_x")
        self.assertEqual(d["signal_type"], "probe")
        self.assertEqual(d["total_findings"], 10)


if __name__ == "__main__":
    unittest.main()
