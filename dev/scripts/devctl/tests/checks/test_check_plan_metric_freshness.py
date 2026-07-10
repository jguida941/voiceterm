from __future__ import annotations

from pathlib import Path

from dev.scripts.checks.plan_metric_freshness.command import (
    MetricDefinition,
    build_report,
    collect_metric_claims,
    render_markdown,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_collect_metric_claims_reads_true_count_lines(tmp_path: Path) -> None:
    _write(
        tmp_path / "dev/active/MASTER_PLAN.md",
        "- P140 TRUE COUNT = 2 is the current scoped metric.\n",
    )

    claims = collect_metric_claims(tmp_path, ("P140",))

    assert len(claims) == 1
    assert claims[0].cited_count == 2


def test_collect_metric_claims_ignores_retracted_wrong_claims(tmp_path: Path) -> None:
    _write(
        tmp_path / "dev/active/MASTER_PLAN.md",
        "- P140 R349 A3 428 claim WRONG.\n",
    )

    claims = collect_metric_claims(tmp_path, ("P140",))

    assert claims == []


def test_collect_metric_claims_preserves_true_count_with_wrong_claim_note(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "dev/active/MASTER_PLAN.md",
        "- P140 TRUE COUNT = 2; R349 A3 428 claim WRONG.\n",
    )

    claims = collect_metric_claims(tmp_path, ("P140",))

    assert len(claims) == 1
    assert claims[0].cited_count == 2


def test_build_report_passes_within_threshold(tmp_path: Path) -> None:
    token = "_from" "_mapping"
    _write(tmp_path / "dev/active/MASTER_PLAN.md", "- P140 TRUE COUNT = 10.\n")
    _write(tmp_path / "dev/scripts/a.py", f"{token}\n" * 9)
    metric = MetricDefinition(
        metric_id="P140",
        label="fixture metric",
        token=token,
        roots=("dev/scripts",),
        threshold_ratio=0.20,
    )

    report = build_report(tmp_path, metrics=(metric,))

    assert report["ok"] is True
    assert report["claims"][0]["actual_count"] == 9


def test_build_report_fails_when_drift_exceeds_threshold(tmp_path: Path) -> None:
    token = "_from" "_mapping"
    _write(tmp_path / "dev/active/MASTER_PLAN.md", "- P140 TRUE COUNT = 4.\n")
    _write(tmp_path / "dev/scripts/a.py", f"{token}\n" * 10)
    metric = MetricDefinition(
        metric_id="P140",
        label="fixture metric",
        token=token,
        roots=("dev/scripts",),
        threshold_ratio=0.10,
    )

    report = build_report(tmp_path, metrics=(metric,))

    assert report["ok"] is False
    assert report["violations"][0]["cited_count"] == 4
    assert report["violations"][0]["actual_count"] == 10


def test_render_markdown_names_stale_metric() -> None:
    rendered = render_markdown({
        "ok": False,
        "metric_count": 1,
        "claim_count": 1,
        "metrics": [{
            "metric_id": "P140",
            "label": "fixture metric",
            "roots": ["dev/scripts"],
            "actual_count": 10,
            "threshold_ratio": 0.10,
        }],
        "violations": [{
            "metric_id": "P140",
            "source_path": "dev/active/MASTER_PLAN.md",
            "line": 7,
            "cited_count": 4,
            "actual_count": 10,
            "drift_ratio": 0.60,
            "threshold_ratio": 0.10,
        }],
    })

    assert "# check_plan_metric_freshness" in rendered
    assert "dev/active/MASTER_PLAN.md:7" in rendered
    assert "60.0% drift" in rendered
