"""Focused tests for startup quality-signal artifact loading."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.runtime.startup_signals import load_startup_quality_signals


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_startup_quality_signals_reads_probe_summary_from_latest_root(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path / "dev/reports/probes/summary.json",
        {
            "generated_at": "wrong-path",
            "summary": {
                "files_with_hints": 99,
                "risk_hints": 999,
                "top_files": [{"file": "wrong.py", "hint_count": 99}],
            },
        },
    )
    _write_json(
        tmp_path / "dev/reports/probes/latest/summary.json",
        {
            "generated_at": "2026-04-13T18:00:00Z",
            "summary": {
                "files_with_hints": 3,
                "risk_hints": 7,
                "top_files": [
                    {"file": "dev/scripts/devctl/runtime/startup_signals.py", "hint_count": 4}
                ],
            },
        },
    )

    signals = load_startup_quality_signals(tmp_path)

    assert signals["probe_report"]["generated_at"] == "2026-04-13T18:00:00Z"
    assert signals["probe_report"]["files_with_hints"] == 3
    assert signals["probe_report"]["risk_hints"] == 7
    assert signals["probe_report"]["top_files"] == [
        {
            "file": "dev/scripts/devctl/runtime/startup_signals.py",
            "hint_count": 4,
        }
    ]


def test_load_startup_quality_signals_includes_governance_severity_mix_and_clusters(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path / "dev/reports/probes/latest/summary.json",
        {
            "generated_at": "2026-04-13T18:00:00Z",
            "summary": {
                "files_with_hints": 1,
                "risk_hints": 1,
                "top_files": [{"file": "dev/scripts/devctl/runtime/startup_signals.py", "hint_count": 1}],
            },
            "risk_hints": [
                {
                    "file": "dev/scripts/devctl/runtime/startup_signals.py",
                    "risk_type": "mixed_concerns",
                    "severity": "medium",
                    "signals": ["3 independent function groups in one file"],
                    "ai_instruction": "Split each cluster into its own module.",
                },
                {
                    "file": "dev/scripts/devctl/runtime/work_intake.py",
                    "risk_type": "split_advisor",
                    "severity": "high",
                    "signals": ["context hotspot rank 1 at temperature 0.90"],
                    "ai_instruction": "Split work_intake.py into intake_scoring.py and intake_routing.py.",
                }
            ],
        },
    )
    _write_json(
        tmp_path / "dev/reports/governance/latest/review_summary.json",
        {
            "generated_at_utc": "2026-04-13T18:00:00Z",
            "stats": {
                "total_findings": 3,
                "open_finding_count": 2,
                "fixed_count": 1,
                "cleanup_rate_pct": 33.33,
            },
        },
    )
    log_path = tmp_path / "dev/reports/governance/finding_reviews.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "\n".join(
            (
                json.dumps(
                    {
                        "finding_id": "f-high",
                        "check_id": "probe_high",
                        "verdict": "confirmed_issue",
                        "signal_type": "probe",
                        "file_path": "pkg/high.py",
                        "severity": "high",
                        "repo_name": "codex-voice",
                        "repo_path": str(tmp_path),
                        "finding_class": "workflow_gap",
                        "prevention_surface": "contract",
                    }
                ),
                json.dumps(
                    {
                        "finding_id": "f-medium",
                        "check_id": "probe_medium",
                        "verdict": "confirmed_issue",
                        "signal_type": "probe",
                        "file_path": "pkg/medium.py",
                        "severity": "medium",
                        "repo_name": "codex-voice",
                        "repo_path": str(tmp_path),
                        "finding_class": "workflow_gap",
                        "prevention_surface": "contract",
                    }
                ),
                json.dumps(
                    {
                        "finding_id": "f-fixed",
                        "check_id": "probe_fixed",
                        "verdict": "fixed",
                        "signal_type": "probe",
                        "file_path": "pkg/fixed.py",
                        "severity": "low",
                        "repo_name": "codex-voice",
                        "repo_path": str(tmp_path),
                        "finding_class": "workflow_gap",
                        "prevention_surface": "contract",
                    }
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )

    signals = load_startup_quality_signals(tmp_path)

    assert signals["governance_review"]["open_by_severity"] == {
        "critical": 0,
        "high": 1,
        "medium": 1,
        "low": 0,
    }
    assert signals["code_shape_clusters"] == [
        {
            "file": "dev/scripts/devctl/runtime/startup_signals.py",
            "cluster_count": 3,
            "severity": "medium",
            "ai_instruction": "Split each cluster into its own module.",
        }
    ]
    assert signals["split_advisor"] == [
        {
            "file": "dev/scripts/devctl/runtime/work_intake.py",
            "severity": "high",
            "ai_instruction": "Split work_intake.py into intake_scoring.py and intake_routing.py.",
        }
    ]
