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
