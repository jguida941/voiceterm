"""Tests for `devctl governance-quality-feedback` command wiring, models, and scoring."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands import listing
from dev.scripts.devctl.commands.governance import quality_feedback
from dev.scripts.devctl.governance.quality_feedback.report_builder import (
    write_quality_feedback_artifact,
)
from dev.scripts.devctl.governance.quality_feedback.report_render import (
    render_quality_feedback_markdown,
)
from dev.scripts.devctl.governance.quality_feedback.fp_classifier import (
    classify_false_positive,
)
from dev.scripts.devctl.governance.quality_feedback.halstead import (
    analyze_file,
    summarize_halstead,
)
from dev.scripts.devctl.governance.quality_feedback.improvement_tracker import (
    compute_improvement_delta,
)
from dev.scripts.devctl.governance.quality_feedback.maintainability_score import (
    ScoreInputs,
    compute_maintainability_score,
)
from dev.scripts.devctl.governance.quality_feedback.models import (
    CheckQualityScore,
    FPAnalysis,
    HalsteadFileMetrics,
    HalsteadSummary,
    ImprovementDelta,
    MaintainabilityResult,
    QualityFeedbackSnapshot,
    Recommendation,
    SubScoreEntry,
)
from dev.scripts.devctl.governance.quality_feedback.per_check_score import (
    build_check_quality_scores,
)
from dev.scripts.devctl.governance.quality_feedback.recommendation_engine import (
    build_recommendations,
)
from dev.scripts.devctl.governance.quality_feedback.report_builder import (
    ReportBuilderConfig,
    build_quality_feedback_report,
)


class GovernanceQualityFeedbackParserTests(unittest.TestCase):
    """Parser registration and CLI wiring tests."""

    def test_cli_parser_accepts_governance_quality_feedback_command(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "governance-quality-feedback",
                "--repo-path",
                "/tmp/test-repo",
                "--repo-name",
                "test-repo",
                "--max-review-rows",
                "1000",
                "--max-external-rows",
                "2000",
                "--halstead-max-files",
                "500",
                "--previous-snapshot",
                "/tmp/prev.json",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "governance-quality-feedback")
        self.assertEqual(args.repo_path, "/tmp/test-repo")
        self.assertEqual(args.repo_name, "test-repo")
        self.assertEqual(args.max_review_rows, 1000)
        self.assertEqual(args.max_external_rows, 2000)
        self.assertEqual(args.halstead_max_files, 500)
        self.assertEqual(args.previous_snapshot, "/tmp/prev.json")
        self.assertEqual(args.format, "json")

    def test_command_handler_registered_in_router(self) -> None:
        self.assertIn("governance-quality-feedback", cli.COMMAND_HANDLERS)
        self.assertIs(
            cli.COMMAND_HANDLERS["governance-quality-feedback"],
            quality_feedback.run,
        )

    def test_command_listed_in_listing_commands(self) -> None:
        self.assertIn("governance-quality-feedback", listing.COMMANDS)


class HalsteadAnalysisTests(unittest.TestCase):
    """Halstead metric computation tests."""

    def test_halstead_python_file_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            py_file = Path(tmp_dir) / "sample.py"
            py_file.write_text(
                "def add(a, b):\n    return a + b\n\ndef mul(x, y):\n    return x * y\n",
                encoding="utf-8",
            )

            result = analyze_file(py_file)

            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result.language, "python")
            self.assertGreater(result.loc, 0)
            self.assertGreater(result.n1, 0)
            self.assertGreater(result.n2, 0)
            self.assertGreater(result.volume, 0.0)
            self.assertGreaterEqual(result.maintainability_index, 0.0)
            self.assertLessEqual(result.maintainability_index, 100.0)

    def test_halstead_summary_aggregation(self) -> None:
        metrics = [
            HalsteadFileMetrics(
                path="a.py",
                language="python",
                loc=50,
                n1=10,
                n2=20,
                big_n1=100,
                big_n2=200,
                vocabulary=30,
                program_length=300,
                volume=1500.0,
                difficulty=50.0,
                effort=75000.0,
                estimated_bugs=0.5,
                maintainability_index=65.0,
            ),
            HalsteadFileMetrics(
                path="b.py",
                language="python",
                loc=30,
                n1=8,
                n2=15,
                big_n1=80,
                big_n2=150,
                vocabulary=23,
                program_length=230,
                volume=1000.0,
                difficulty=40.0,
                effort=40000.0,
                estimated_bugs=0.3,
                maintainability_index=75.0,
            ),
        ]

        summary = summarize_halstead(metrics)

        self.assertEqual(summary.files_scanned, 2)
        self.assertEqual(summary.total_loc, 80)
        self.assertAlmostEqual(summary.avg_volume, 1250.0, places=1)
        self.assertAlmostEqual(summary.avg_difficulty, 45.0, places=1)
        self.assertAlmostEqual(summary.avg_maintainability_index, 70.0, places=1)
        self.assertAlmostEqual(summary.estimated_total_bugs, 0.8, places=2)
        self.assertIn("python", summary.by_language)


class FPClassifierTests(unittest.TestCase):
    """False-positive classification rule tests."""

    def test_fp_classifier_rules(self) -> None:
        # Known check_id maps to a specific root cause
        result = classify_false_positive(
            finding_id="f-001",
            check_id="probe_magic_numbers",
            file_path="src/config.py",
            verdict="false_positive",
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.root_cause, "threshold_noise")
        self.assertEqual(result.confidence, "high")

        # Style opinion from check_id
        result2 = classify_false_positive(
            finding_id="f-002",
            check_id="probe_stringly_typed",
            file_path="src/handler.py",
            verdict="false_positive",
        )
        self.assertIsNotNone(result2)
        assert result2 is not None
        self.assertEqual(result2.root_cause, "style_opinion")

        # Context-blind from check_id
        result3 = classify_false_positive(
            finding_id="f-003",
            check_id="probe_single_use_helpers",
            file_path="src/adapter.py",
            verdict="false_positive",
        )
        self.assertIsNotNone(result3)
        assert result3 is not None
        self.assertEqual(result3.root_cause, "context_blind")

        # Non-FP verdict returns None
        result_none = classify_false_positive(
            finding_id="f-004",
            check_id="probe_magic_numbers",
            file_path="src/config.py",
            verdict="fixed",
        )
        self.assertIsNone(result_none)


class MaintainabilityScoreTests(unittest.TestCase):
    """Composite maintainability score tests."""

    def test_maintainability_score_computation(self) -> None:
        inputs = ScoreInputs(
            avg_halstead_mi=70.0,
            halstead_mi_available=True,
            cleanup_rate_pct=80.0,
            cleanup_rate_available=True,
            open_guard_findings=2,
            guard_count=20,
            guard_issue_burden_available=True,
            open_positive_findings=3,
            total_source_files=100,
            finding_density_available=True,
        )

        result = compute_maintainability_score(inputs)

        self.assertIsInstance(result, MaintainabilityResult)
        self.assertGreater(result.overall, 0.0)
        self.assertLessEqual(result.overall, 100.0)
        self.assertIn(result.grade, ["A", "B", "C", "D", "F"])
        self.assertEqual(len(result.sub_scores), 7)

        # Verify sub-score weights sum to 1.0
        total_weight = sum(s.weight for s in result.sub_scores)
        self.assertAlmostEqual(total_weight, 1.0, places=2)


class PerCheckScoreTests(unittest.TestCase):
    """Per-check quality score computation tests."""

    def test_per_check_quality_scores(self) -> None:
        review_rows = [
            {
                "check_id": "check_code_shape",
                "signal_type": "guard",
                "verdict": "false_positive",
            },
            {
                "check_id": "check_code_shape",
                "signal_type": "guard",
                "verdict": "fixed",
            },
            {
                "check_id": "check_code_shape",
                "signal_type": "guard",
                "verdict": "confirmed_issue",
            },
            {
                "check_id": "probe_magic_numbers",
                "signal_type": "probe",
                "verdict": "false_positive",
            },
            {
                "check_id": "probe_magic_numbers",
                "signal_type": "probe",
                "verdict": "false_positive",
            },
        ]

        scores = build_check_quality_scores(review_rows)

        self.assertEqual(len(scores), 2)

        # Find check_code_shape score
        shape_score = next(
            (s for s in scores if s.check_id == "check_code_shape"), None
        )
        self.assertIsNotNone(shape_score)
        assert shape_score is not None
        self.assertEqual(shape_score.total_findings, 3)
        self.assertEqual(shape_score.true_positive_count, 2)
        self.assertEqual(shape_score.false_positive_count, 1)
        self.assertGreater(shape_score.precision_pct, 0.0)

        # Find probe_magic_numbers score
        magic_score = next(
            (s for s in scores if s.check_id == "probe_magic_numbers"), None
        )
        self.assertIsNotNone(magic_score)
        assert magic_score is not None
        self.assertEqual(magic_score.total_findings, 2)
        self.assertEqual(magic_score.false_positive_count, 2)
        self.assertAlmostEqual(magic_score.fp_rate_pct, 100.0, places=1)


class ImprovementDeltaTests(unittest.TestCase):
    """Delta computation between snapshots."""

    def test_improvement_delta_with_previous(self) -> None:
        current_checks = [
            CheckQualityScore(
                check_id="check_code_shape",
                signal_type="guard",
                total_findings=5,
                true_positive_count=4,
                false_positive_count=1,
                precision_pct=80.0,
                fp_rate_pct=20.0,
                cleanup_rate_pct=75.0,
            ),
        ]

        previous_snapshot = {
            "maintainability_score": {"overall": 60.0},
            "check_quality_scores": [
                {
                    "check_id": "check_code_shape",
                    "signal_type": "guard",
                    "precision_pct": 50.0,
                },
            ],
        }

        delta = compute_improvement_delta(
            current_score=75.0,
            current_check_scores=current_checks,
            previous_snapshot=previous_snapshot,
        )

        self.assertIsInstance(delta, ImprovementDelta)
        self.assertAlmostEqual(delta.overall_score_delta, 15.0, places=1)
        self.assertAlmostEqual(delta.previous_score, 60.0, places=1)
        self.assertAlmostEqual(delta.current_score, 75.0, places=1)
        self.assertGreaterEqual(len(delta.improved_checks), 1)

    def test_improvement_delta_without_previous(self) -> None:
        delta = compute_improvement_delta(
            current_score=70.0,
            current_check_scores=[],
            previous_snapshot=None,
        )

        self.assertAlmostEqual(delta.overall_score_delta, 0.0)
        self.assertIsNone(delta.previous_score)


class RecommendationEngineTests(unittest.TestCase):
    """Recommendation engine tests."""

    def test_recommendation_engine_fp_reduction(self) -> None:
        # Create a check with high FP rate to trigger fp_reduction recommendation
        maintainability = compute_maintainability_score(
            ScoreInputs(avg_halstead_mi=80.0, cleanup_rate_pct=90.0)
        )
        halstead_summary = HalsteadSummary(
            files_scanned=100,
            total_loc=5000,
            avg_volume=500.0,
            avg_difficulty=20.0,
            avg_effort=10000.0,
            avg_maintainability_index=75.0,
            estimated_total_bugs=1.5,
            by_language={"python": {"files_scanned": 100.0}},
        )
        check_scores = [
            CheckQualityScore(
                check_id="probe_magic_numbers",
                signal_type="probe",
                total_findings=10,
                true_positive_count=2,
                false_positive_count=8,
                precision_pct=20.0,
                fp_rate_pct=80.0,
                cleanup_rate_pct=50.0,
            ),
        ]

        from dev.scripts.devctl.governance.quality_feedback.models import (
            FPClassification,
        )

        fp_classifications = [
            FPClassification(
                finding_id=f"f-{i}",
                check_id="probe_magic_numbers",
                file_path=f"src/file_{i}.py",
                root_cause="threshold_noise",
                confidence="high",
                evidence="check_id maps to threshold_noise",
            )
            for i in range(8)
        ]

        recommendations = build_recommendations(
            maintainability=maintainability,
            halstead_summary=halstead_summary,
            check_scores=check_scores,
            fp_classifications=fp_classifications,
        )

        # Should have at least one fp_reduction recommendation
        fp_recs = [r for r in recommendations if r.category == "fp_reduction"]
        self.assertGreaterEqual(len(fp_recs), 1)
        self.assertEqual(fp_recs[0].check_id, "probe_magic_numbers")
        self.assertEqual(fp_recs[0].estimated_impact, "high")


class FullReportIntegrationTests(unittest.TestCase):
    """End-to-end report building tests."""

    def test_full_report_builder_integration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)

            # Create a minimal Python source file for Halstead scanning
            src_dir = repo_root / "src"
            src_dir.mkdir()
            (src_dir / "demo.py").write_text(
                "def greet(name):\n    return f'Hello, {name}!'\n",
                encoding="utf-8",
            )

            # Create empty governance logs (no findings)
            gov_dir = repo_root / "dev" / "reports" / "governance"
            gov_dir.mkdir(parents=True)
            review_log = gov_dir / "finding_reviews.jsonl"
            review_log.write_text("", encoding="utf-8")
            ext_log = gov_dir / "external_pilot_findings.jsonl"
            ext_log.write_text("", encoding="utf-8")

            snapshot = build_quality_feedback_report(
                repo_root=repo_root,
                repo_name="test-repo",
                config=ReportBuilderConfig(
                    governance_review_log=review_log,
                    external_finding_log=ext_log,
                    halstead_max_files=100,
                ),
            )

            self.assertIsInstance(snapshot, QualityFeedbackSnapshot)
            self.assertEqual(snapshot.repo_name, "test-repo")
            self.assertEqual(snapshot.contract_id, "QualityFeedbackSnapshot")
            self.assertEqual(snapshot.schema_version, 1)
            # With empty review logs only Halstead is available; score
            # must still be non-negative (0 when no dimensions are available
            # or positive when Halstead scans succeed).
            self.assertGreaterEqual(snapshot.maintainability.overall, 0.0)
            self.assertGreaterEqual(
                snapshot.halstead_summary.files_scanned, 1
            )
            self.assertIsNotNone(snapshot.improvement_delta)

            # Verify to_dict produces valid JSON
            payload = snapshot.to_dict()
            json_str = json.dumps(payload, indent=2)
            roundtripped = json.loads(json_str)
            self.assertEqual(
                roundtripped["contract_id"], "QualityFeedbackSnapshot"
            )

    def test_finding_density_is_stable_across_halstead_sample_caps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            src_dir = repo_root / "src"
            src_dir.mkdir()
            for index in range(4):
                (src_dir / f"mod_{index}.py").write_text(
                    f"def fn_{index}():\n    return {index}\n",
                    encoding="utf-8",
                )

            gov_dir = repo_root / "dev" / "reports" / "governance"
            gov_dir.mkdir(parents=True)
            review_log = gov_dir / "finding_reviews.jsonl"
            review_log.write_text(
                "\n".join(
                    (
                        json.dumps(
                            {
                                "finding_id": "f-1",
                                "check_id": "probe_identifier_density",
                                "signal_type": "probe",
                                "verdict": "confirmed_issue",
                                "file_path": "src/mod_0.py",
                            }
                        ),
                        json.dumps(
                            {
                                "finding_id": "f-2",
                                "check_id": "probe_blank_line_frequency",
                                "signal_type": "probe",
                                "verdict": "fixed",
                                "file_path": "src/mod_1.py",
                            }
                        ),
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            ext_log = gov_dir / "external_pilot_findings.jsonl"
            ext_log.write_text("", encoding="utf-8")

            tiny_snapshot = build_quality_feedback_report(
                repo_root=repo_root,
                repo_name="test-repo",
                config=ReportBuilderConfig(
                    governance_review_log=review_log,
                    external_finding_log=ext_log,
                    halstead_max_files=1,
                ),
            )
            full_snapshot = build_quality_feedback_report(
                repo_root=repo_root,
                repo_name="test-repo",
                config=ReportBuilderConfig(
                    governance_review_log=review_log,
                    external_finding_log=ext_log,
                    halstead_max_files=100,
                ),
            )

            tiny_density = next(
                entry
                for entry in tiny_snapshot.maintainability.sub_scores
                if entry.name == "finding_density"
            )
            full_density = next(
                entry
                for entry in full_snapshot.maintainability.sub_scores
                if entry.name == "finding_density"
            )

            self.assertTrue(tiny_density.available)
            self.assertTrue(full_density.available)
            self.assertEqual(tiny_density.value, full_density.value)

    def test_artifact_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)

            snapshot = _make_minimal_snapshot(repo_name="artifact-test")

            paths = write_quality_feedback_artifact(
                snapshot, repo_root=repo_root
            )

            self.assertIn("snapshot_path", paths)
            self.assertIn("summary_root", paths)

            json_path = Path(paths["snapshot_path"])

            self.assertTrue(json_path.exists())

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["contract_id"], "QualityFeedbackSnapshot")
            self.assertEqual(payload["repo_name"], "artifact-test")

    def test_markdown_render(self) -> None:
        snapshot = _make_minimal_snapshot(repo_name="render-test")

        md = render_quality_feedback_markdown(snapshot)

        self.assertIn("Governance Quality Feedback Report", md)
        self.assertIn("render-test", md)
        self.assertIn("Maintainability Score", md)
        self.assertIn("Halstead Summary", md)
        self.assertIn("False-Positive Analysis", md)


def _make_minimal_snapshot(
    *,
    repo_name: str = "test-repo",
) -> QualityFeedbackSnapshot:
    """Build a minimal valid snapshot for rendering/serialization tests."""
    maintainability = compute_maintainability_score(
        ScoreInputs(avg_halstead_mi=70.0, cleanup_rate_pct=50.0)
    )
    halstead_summary = HalsteadSummary(
        files_scanned=10,
        total_loc=500,
        avg_volume=300.0,
        avg_difficulty=15.0,
        avg_effort=4500.0,
        avg_maintainability_index=70.0,
        estimated_total_bugs=0.1,
        by_language={"python": {"files_scanned": 10.0}},
    )

    return QualityFeedbackSnapshot(
        schema_version=1,
        contract_id="QualityFeedbackSnapshot",
        command="governance-quality-feedback",
        generated_at_utc="2026-03-17T00:00:00Z",
        repo_name=repo_name,
        maintainability=maintainability,
        halstead_summary=halstead_summary,
        false_positive_analysis=FPAnalysis(
            total_fp_count=0,
            by_root_cause=(),
            classified_findings=(),
        ),
        check_quality_scores=(),
        improvement_delta=ImprovementDelta(
            overall_score_delta=0.0,
            previous_score=None,
            current_score=maintainability.overall,
            improved_checks=(),
            degraded_checks=(),
        ),
        recommendations=(),
    )


if __name__ == "__main__":
    unittest.main()
