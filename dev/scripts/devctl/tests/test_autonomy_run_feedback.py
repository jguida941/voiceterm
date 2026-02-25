"""Tests for swarm_run feedback sizing helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.autonomy_run_feedback import (
    build_feedback_state,
    summarize_feedback_state,
    update_feedback_state,
)


def _args(**overrides) -> SimpleNamespace:
    defaults = {
        "feedback_sizing": True,
        "feedback_stall_rounds": 2,
        "feedback_no_signal_rounds": 2,
        "feedback_downshift_factor": 0.5,
        "feedback_upshift_rounds": 2,
        "feedback_upshift_factor": 1.25,
        "min_agents": 4,
        "max_agents": 20,
        "agents": 20,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _write_worker_report(
    path: Path, *, triage_reason: str, unresolved_count: int, resolved: bool = False
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "resolved": resolved,
        "reason": "max_rounds_reached",
        "rounds": [
            {
                "round": 1,
                "triage_reason": triage_reason,
                "unresolved_count": unresolved_count,
                "risk": "low",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _swarm_payload(
    root: Path,
    *,
    selected_agents: int,
    worker_agents: int,
    triage_reason: str,
    unresolved_count: int,
) -> dict:
    agents: list[dict] = []
    for index in range(1, worker_agents + 1):
        report_json = root / f"agent-{index}.json"
        _write_worker_report(
            report_json,
            triage_reason=triage_reason,
            unresolved_count=unresolved_count,
            resolved=unresolved_count == 0 and triage_reason == "resolved",
        )
        agents.append(
            {
                "agent": f"AGENT-{index}",
                "index": index,
                "ok": True,
                "resolved": unresolved_count == 0,
                "reason": "max_rounds_reached",
                "report_json": str(report_json),
            }
        )
    agents.append(
        {
            "agent": "AGENT-REVIEW",
            "index": worker_agents + 1,
            "ok": True,
            "resolved": True,
            "reason": "post_audit_ok",
            "report_json": "",
        }
    )
    return {
        "summary": {
            "selected_agents": selected_agents,
            "worker_agents": worker_agents,
            "reviewer_lane": True,
        },
        "agents": agents,
    }


class FeedbackSizingConfigTests(unittest.TestCase):
    def test_build_feedback_state_rejects_invalid_factors(self) -> None:
        state, warnings, errors = build_feedback_state(
            _args(feedback_downshift_factor=1.1, feedback_upshift_factor=1.0),
            continuous_enabled=True,
        )

        self.assertTrue(state["enabled"])
        self.assertFalse(warnings)
        self.assertTrue(errors)
        self.assertIn("--feedback-downshift-factor must be > 0 and < 1", errors)
        self.assertIn("--feedback-upshift-factor must be > 1", errors)

    def test_feedback_requested_without_continuous_is_warned_and_disabled(self) -> None:
        state, warnings, errors = build_feedback_state(
            _args(agents=None),
            continuous_enabled=False,
        )

        self.assertFalse(errors)
        self.assertFalse(state["enabled"])
        self.assertIn("feedback sizing ignored because --continuous is disabled", warnings)


class FeedbackSizingBehaviorTests(unittest.TestCase):
    def test_no_signal_streak_downshifts_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            state, warnings, errors = build_feedback_state(
                _args(agents=20),
                continuous_enabled=True,
            )
            self.assertFalse(warnings)
            self.assertFalse(errors)

            first = update_feedback_state(
                state,
                _swarm_payload(
                    root / "c1",
                    selected_agents=20,
                    worker_agents=19,
                    triage_reason="gh_unreachable_local_non_blocking",
                    unresolved_count=0,
                ),
            )
            second = update_feedback_state(
                state,
                _swarm_payload(
                    root / "c2",
                    selected_agents=20,
                    worker_agents=19,
                    triage_reason="gh_unreachable_local_non_blocking",
                    unresolved_count=0,
                ),
            )

            self.assertEqual(first["decision"], "hold")
            self.assertEqual(second["decision"], "downshift")
            self.assertEqual(second["trigger"], "no_signal_streak")
            self.assertEqual(second["next_agents"], 10)
            self.assertEqual(state["next_agents"], 10)

    def test_improve_streak_upshifts_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            state, warnings, errors = build_feedback_state(
                _args(
                    agents=6,
                    min_agents=2,
                    max_agents=12,
                    feedback_upshift_rounds=1,
                    feedback_upshift_factor=1.5,
                    feedback_stall_rounds=5,
                    feedback_no_signal_rounds=5,
                ),
                continuous_enabled=True,
            )
            self.assertFalse(warnings)
            self.assertFalse(errors)

            first = update_feedback_state(
                state,
                _swarm_payload(
                    root / "c1",
                    selected_agents=6,
                    worker_agents=5,
                    triage_reason="no fix command configured",
                    unresolved_count=6,
                ),
            )
            second = update_feedback_state(
                state,
                _swarm_payload(
                    root / "c2",
                    selected_agents=6,
                    worker_agents=5,
                    triage_reason="no fix command configured",
                    unresolved_count=2,
                ),
            )
            summary = summarize_feedback_state(state)

            self.assertEqual(first["decision"], "hold")
            self.assertEqual(second["decision"], "upshift")
            self.assertEqual(second["trigger"], "improve_streak")
            self.assertEqual(second["next_agents"], 9)
            self.assertEqual(summary["next_agents"], 9)
            self.assertEqual(len(summary["history"]), 2)


if __name__ == "__main__":
    unittest.main()
