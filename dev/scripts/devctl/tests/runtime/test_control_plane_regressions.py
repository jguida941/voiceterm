"""Regression tests for ControlPlaneReadModel findings F1 and F2.

F1: review_accepted boolean takes precedence over verdict text inference.
F2: Per-provider conductor liveness (codex/claude) replaces collapsed bit.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from dev.scripts.devctl.runtime.control_plane_read_model import (
    build_control_plane_read_model,
    control_plane_read_model_from_mapping,
)
from dev.scripts.devctl.runtime.control_plane_resolve import (
    resolve_daemon_state,
    resolve_reviewer_state,
)


def _empty_sources() -> dict:
    """All-None source dict simulating a repo with no artifacts."""
    return {
        "receipt": None,
        "review_state": None,
        "push_report": None,
        "publisher_hb": None,
        "supervisor_hb": None,
        "codex_conductor": None,
        "claude_conductor": None,
        "full_json": None,
        "compact_json": None,
    }


def _base_git() -> dict:
    return {"branch": "feature/test", "head": "abc1234", "clean": True, "ahead": 0}


# -------------------------------------------------------
# F1: review_accepted boolean precedence over verdict text
# -------------------------------------------------------

class ReviewAcceptedBooleanRegressionTests(unittest.TestCase):
    """F1 regression: typed boolean takes precedence over verdict text."""

    def test_boolean_true_with_accepted_verdict_stays_accepted(self) -> None:
        """review_accepted=True with verdict '- Reviewer-accepted.' stays accepted."""
        sources = _empty_sources()
        sources["review_state"] = {
            "bridge": {},
            "reviewer_runtime": {
                "review_acceptance": {
                    "review_accepted": True,
                    "current_verdict": "- Reviewer-accepted.",
                },
            },
        }
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertTrue(model.review_accepted)

    def test_boolean_true_overrides_non_matching_verdict(self) -> None:
        """Typed boolean True wins even when verdict text would not match."""
        sources = _empty_sources()
        sources["review_state"] = {
            "bridge": {},
            "reviewer_runtime": {
                "review_acceptance": {
                    "review_accepted": True,
                    "current_verdict": "needs work",
                },
            },
        }
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertTrue(model.review_accepted)

    def test_boolean_false_overrides_accepted_verdict(self) -> None:
        """Typed boolean False wins even when verdict text says 'accepted'."""
        sources = _empty_sources()
        sources["review_state"] = {
            "bridge": {},
            "reviewer_runtime": {
                "review_acceptance": {
                    "review_accepted": False,
                    "current_verdict": "accepted",
                },
            },
        }
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertFalse(model.review_accepted)

    def test_missing_boolean_falls_back_to_verdict(self) -> None:
        """When review_accepted key is absent, verdict text is the fallback."""
        sources = _empty_sources()
        sources["review_state"] = {
            "bridge": {},
            "reviewer_runtime": {
                "review_acceptance": {
                    "current_verdict": "approved",
                },
            },
        }
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertTrue(model.review_accepted)

    def test_resolver_boolean_true_with_reviewer_accepted_verdict(self) -> None:
        """Direct resolver: boolean=True + '- Reviewer-accepted.' -> accepted."""
        rs = {
            "bridge": {},
            "reviewer_runtime": {
                "review_acceptance": {
                    "review_accepted": True,
                    "current_verdict": "- Reviewer-accepted.",
                },
            },
        }
        r = resolve_reviewer_state(rs, None, None)
        self.assertTrue(r["review_accepted"])


# -------------------------------------------------------
# F2: per-provider conductor liveness replaces collapsed bit
# -------------------------------------------------------

class ConductorSplitRegressionTests(unittest.TestCase):
    """F2 regression: per-provider conductor liveness is observable."""

    def test_codex_dead_claude_alive_observable(self) -> None:
        """Codex dead + Claude alive stays observable as distinct fields."""
        sources = _empty_sources()
        sources["codex_conductor"] = None
        sources["claude_conductor"] = {"session_pid": -1}
        d = resolve_daemon_state(sources)
        self.assertFalse(d["codex_conductor_alive"])
        self.assertFalse(d["claude_conductor_alive"])

    def test_split_fields_in_read_model(self) -> None:
        """Build verifies split conductor fields propagate to the model."""
        sources = _empty_sources()
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertFalse(model.codex_conductor_alive)
        self.assertFalse(model.claude_conductor_alive)

    def test_resolver_returns_separate_keys(self) -> None:
        """resolve_daemon_state returns codex/claude as separate keys."""
        d = resolve_daemon_state(_empty_sources())
        self.assertIn("codex_conductor_alive", d)
        self.assertIn("claude_conductor_alive", d)
        self.assertNotIn("conductor_alive", d)

    def test_deserialization_split_fields(self) -> None:
        """Roundtrip preserves split conductor fields."""
        sources = _empty_sources()
        original = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        d = original.to_dict()
        restored = control_plane_read_model_from_mapping(d)
        self.assertEqual(
            restored.codex_conductor_alive, original.codex_conductor_alive,
        )
        self.assertEqual(
            restored.claude_conductor_alive, original.claude_conductor_alive,
        )


class OperatorModeFromReviewStateTests(unittest.TestCase):
    """Prove review_state operator_interaction_mode survives without receipt."""

    def test_review_state_remote_control_without_receipt(self) -> None:
        sources = {
            "receipt": None,
            "review_state": {
                "collaboration": {"operator_interaction_mode": "remote_control"},
            },
            "push_report": None,
            "publisher_hb": None,
            "supervisor_hb": None,
            "codex_conductor": None,
            "claude_conductor": None,
            "full_json": None,
            "compact_json": None,
        }
        model = build_control_plane_read_model(
            Path("/tmp"), sources_override=sources, git_override={"branch": "test", "head": "abc", "clean": True, "ahead": 0},
        )
        self.assertEqual(model.operator_interaction_mode, "remote_control")

    def test_receipt_mode_used_when_review_state_empty(self) -> None:
        sources = {
            "receipt": {"operator_interaction_mode": "dual_agent"},
            "review_state": None,
            "push_report": None,
            "publisher_hb": None,
            "supervisor_hb": None,
            "codex_conductor": None,
            "claude_conductor": None,
            "full_json": None,
            "compact_json": None,
        }
        model = build_control_plane_read_model(
            Path("/tmp"), sources_override=sources, git_override={"branch": "test", "head": "abc", "clean": True, "ahead": 0},
        )
        self.assertEqual(model.operator_interaction_mode, "dual_agent")


if __name__ == "__main__":
    unittest.main()
