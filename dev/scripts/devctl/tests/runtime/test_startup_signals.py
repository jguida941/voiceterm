"""Focused tests for startup quality-signal artifact loading."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from dev.scripts.devctl.runtime.startup_signals import (
    compact_startup_quality_signals,
    load_startup_quality_signals,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run_git(repo_root: Path, *args: str) -> None:
    env = dict(os.environ)
    env.update(
        {
            "GIT_AUTHOR_NAME": "Tests",
            "GIT_AUTHOR_EMAIL": "tests@example.com",
            "GIT_COMMITTER_NAME": "Tests",
            "GIT_COMMITTER_EMAIL": "tests@example.com",
        }
    )
    subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )


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


def test_load_startup_quality_signals_includes_contract_connectivity_debt(
    tmp_path: Path,
) -> None:
    _run_git(tmp_path, "init", "-q")
    _write(tmp_path / ".gitignore", "dev/reports/**\n")
    _write(
        tmp_path / "dev/scripts/devctl/runtime/orphan_contract.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class OrphanContract:
    isolated_owner: str
    isolated_state: str
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "dev/scripts/devctl/runtime/duplicate_a.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class DuplicateA:
    owner: str
    state: str
    receipt_id: str
""".strip()
        + "\n",
    )
    _write(
        tmp_path / "dev/scripts/devctl/platform/duplicate_b.py",
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class DuplicateB:
    owner: str
    state: str
    receipt_id: str
""".strip()
        + "\n",
    )
    _run_git(tmp_path, "add", "-A")
    _run_git(tmp_path, "commit", "-q", "-m", "baseline")

    signals = load_startup_quality_signals(tmp_path)
    contract_signal = signals["contract_connectivity"]

    assert contract_signal["mode"] == "working-tree"
    assert contract_signal["ok"] is True
    assert contract_signal["current_counts"]["orphaned"] == 1
    assert contract_signal["current_counts"]["duplicates"] == 1
    assert contract_signal["baseline_counts"]["orphaned"] == 1
    assert contract_signal["baseline_counts"]["duplicates"] == 1
    assert contract_signal["new_debt_count"] == 0
    assert contract_signal["severity"] == "medium"
    assert "Prioritize contract connectivity closure" in contract_signal["ai_instruction"]

    compact = compact_startup_quality_signals(signals)
    assert compact["contract_connectivity"]["current_counts"]["orphaned"] == 1
    assert compact["contract_connectivity"]["baseline_counts"]["duplicates"] == 1
    assert compact["contract_connectivity"]["ai_instruction"]

    cached_signals = load_startup_quality_signals(tmp_path)
    assert cached_signals["contract_connectivity"]["cache_state"] == "fresh"


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
    assert signals["finding_backlog"] == {
        "log_path": str(log_path),
        "total_findings": 3,
        "open_finding_count": 2,
        "open_by_severity": {
            "critical": 0,
            "high": 1,
            "medium": 1,
            "low": 0,
        },
        "top_open_findings": [
            {
                "finding_id": "f-high",
                "check_id": "probe_high",
                "severity": "high",
                "file_path": "pkg/high.py",
            },
            {
                "finding_id": "f-medium",
                "check_id": "probe_medium",
                "severity": "medium",
                "file_path": "pkg/medium.py",
            },
        ],
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
