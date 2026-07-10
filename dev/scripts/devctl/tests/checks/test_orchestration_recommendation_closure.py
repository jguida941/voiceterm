"""Tests for check_orchestration_recommendation_closure guard."""

from __future__ import annotations

from dev.scripts.checks.orchestration_recommendation_closure.command import (
    build_report,
)


def test_orchestration_recommendation_closure_passes_complete_signal() -> None:
    report = build_report(
        report_override={
            "orchestration": {
                "signals": [
                    {
                        "source": "agent-loop",
                        "signal_id": "codex:dashboard",
                        "source_surface": "agent-loop",
                        "severity": "high",
                        "recommended_action": "continue_to_goal",
                        "closure_check_command": (
                            "python3 dev/scripts/devctl.py agent-loop --format json"
                        ),
                    }
                ]
            }
        }
    )

    assert report["ok"] is True
    assert report["violations"] == []


def test_orchestration_recommendation_closure_fails_missing_fields() -> None:
    report = build_report(
        report_override={
            "orchestration": {
                "signals": [
                    {
                        "source": "system-picture",
                        "signal_id": "graph",
                        "recommended_action": "refresh_context_graph",
                    }
                ]
            }
        }
    )

    assert report["ok"] is False
    assert report["violations"][0]["reason"] == "missing_required_signal_fields"
    assert "closure_check_command" in report["violations"][0]["missing_fields"]
