"""Tests for the ControlPlaneReadModel and its builder."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.runtime.control_plane_read_model import (
    CONTROL_PLANE_READ_MODEL_CONTRACT_ID,
    CONTROL_PLANE_READ_MODEL_SCHEMA_VERSION,
    ControlPlaneReadModel,
    build_control_plane_read_model,
    control_plane_read_model_from_mapping,
    _default_read_model,
)
from dev.scripts.devctl.runtime.control_plane_resolve import (
    resolve_blocker_and_action,
    resolve_daemon_state,
    resolve_pending_packets,
    resolve_quality,
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


class ControlPlaneReadModelDataclassTests(unittest.TestCase):
    """Verify frozen dataclass contract stability."""

    def test_frozen_prevents_mutation(self) -> None:
        model = _default_read_model()
        with self.assertRaises(AttributeError):
            model.branch = "other"  # type: ignore[misc]

    def test_to_dict_roundtrip(self) -> None:
        model = _default_read_model()
        d = model.to_dict()
        self.assertEqual(d["branch"], "unknown")
        self.assertEqual(d["resolved_phase"], "idle")
        self.assertEqual(d["check_details"], ())
        self.assertIsNone(d["coordination"])

    def test_all_fields_present(self) -> None:
        model = _default_read_model()
        expected_fields = {
            "timestamp", "branch", "head_sha", "worktree_clean",
            "ahead_of_upstream", "resolved_phase", "push_eligible",
            "implementation_blocked", "top_blocker", "next_action",
            "next_command", "reviewer_mode", "operator_interaction_mode",
            "reviewer_freshness", "review_accepted", "last_reviewed_sha",
            "attention_status",
            "attention_summary", "reviewer_observation",
            "publisher_running", "supervisor_running",
            "codex_conductor_alive", "claude_conductor_alive",
            "pending_action_requests", "last_guard_ok",
            "check_details", "coordination",
        }
        actual_fields = set(model.to_dict().keys())
        self.assertEqual(expected_fields, actual_fields)


class ContractIdTests(unittest.TestCase):
    """Verify contract ID and schema version stability."""

    def test_contract_id(self) -> None:
        self.assertEqual(CONTROL_PLANE_READ_MODEL_CONTRACT_ID, "ControlPlaneReadModel")

    def test_schema_version(self) -> None:
        self.assertEqual(CONTROL_PLANE_READ_MODEL_SCHEMA_VERSION, 1)


class BuildFromEmptySourcesTests(unittest.TestCase):
    """Build a read model from empty sources -- no artifacts on disk."""

    def test_build_with_no_artifacts(self) -> None:
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=_empty_sources(),
            git_override=_base_git(),
        )
        self.assertEqual(model.branch, "feature/test")
        self.assertEqual(model.head_sha, "abc1234")
        self.assertTrue(model.worktree_clean)
        self.assertEqual(model.resolved_phase, "idle")
        self.assertFalse(model.push_eligible)
        self.assertFalse(model.implementation_blocked)
        self.assertEqual(model.top_blocker, "none")
        self.assertEqual(model.reviewer_mode, "single_agent")
        self.assertTrue(model.last_guard_ok)
        self.assertEqual(model.check_details, ())

    def test_dirty_worktree_resolves_implementing(self) -> None:
        git = _base_git()
        git["clean"] = False
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=_empty_sources(),
            git_override=git,
        )
        self.assertFalse(model.worktree_clean)
        self.assertEqual(model.resolved_phase, "implementing")


class ReviewStatusDirThreadingTests(unittest.TestCase):
    """Verify caller-selected review bundles reach the shared source loader."""

    def test_builder_threads_review_status_dir_to_load_sources(self) -> None:
        repo_root = Path("/tmp/repo")
        review_status_dir = Path("/tmp/review-status")
        with patch(
            "dev.scripts.devctl.runtime.control_plane_read_model.load_sources",
            return_value=_empty_sources(),
        ) as load_sources_mock:
            build_control_plane_read_model(
                repo_root,
                git_override=_base_git(),
                review_status_dir=review_status_dir,
            )

        load_sources_mock.assert_called_once_with(
            repo_root,
            governance=None,
            review_status_dir=review_status_dir,
        )


class BuildWithReceiptTests(unittest.TestCase):
    """Build from a receipt with push decisions."""

    def test_push_eligible_from_receipt(self) -> None:
        sources = _empty_sources()
        sources["receipt"] = {"push_action": "run_devctl_push"}
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertTrue(model.push_eligible)
        self.assertEqual(model.resolved_phase, "pushing")
        self.assertEqual(model.next_action, "run_devctl_push")
        self.assertIn("push --execute", model.next_command)

    def test_await_checkpoint_blocks_push(self) -> None:
        sources = _empty_sources()
        sources["receipt"] = {"push_action": "await_checkpoint"}
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertFalse(model.push_eligible)
        self.assertEqual(model.next_action, "await_checkpoint")

    def test_implementation_blocked_from_receipt(self) -> None:
        sources = _empty_sources()
        sources["receipt"] = {"implementation_blocked": True}
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertTrue(model.implementation_blocked)
        self.assertEqual(model.resolved_phase, "reviewing")


class BuildWithReviewStateTests(unittest.TestCase):
    """Build from review_state.json data."""

    class _FrozenReviewState:
        def __init__(self, payload: dict[str, object]) -> None:
            self._payload = payload

        def to_dict(self) -> dict[str, object]:
            return dict(self._payload)

    def test_reviewer_mode_from_review_state(self) -> None:
        sources = _empty_sources()
        sources["review_state"] = {
            "bridge": {"reviewer_mode": "active_dual_agent"},
        }
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertEqual(model.reviewer_mode, "active_dual_agent")

    def test_review_accepted_from_verdict(self) -> None:
        sources = _empty_sources()
        sources["review_state"] = {
            "bridge": {},
            "reviewer_runtime": {
                "review_acceptance": {"current_verdict": "accepted"},
            },
        }
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertTrue(model.review_accepted)

    def test_attention_from_review_state(self) -> None:
        sources = _empty_sources()
        sources["review_state"] = {
            "attention": {"status": "needs_recovery", "summary": "conductor down"},
        }
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertEqual(model.attention_status, "needs_recovery")
        self.assertEqual(model.attention_summary, "conductor down")

    def test_typed_review_state_overrides_stale_loaded_payload(self) -> None:
        sources = _empty_sources()
        sources["review_state"] = {
            "attention": {"status": "stale_attention", "summary": "old"},
        }
        frozen = self._FrozenReviewState(
            {
                "attention": {"status": "fresh_attention", "summary": "new"},
            }
        )
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
            review_state=frozen,
        )
        self.assertEqual(model.attention_status, "fresh_attention")
        self.assertEqual(model.attention_summary, "new")

    def test_pending_packets_counted(self) -> None:
        sources = _empty_sources()
        sources["review_state"] = {
            "packets": [
                {"status": "pending", "packet_id": "p1"},
                {"status": "pending", "packet_id": "p2"},
                {"status": "acked", "packet_id": "p3"},
            ],
        }
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertEqual(model.pending_action_requests, 2)

    def test_coordination_extracted_from_typed_review_state(self) -> None:
        sources = _empty_sources()
        sources["review_state"] = {
            "coordination": {
                "contract_id": "CoordinationSnapshot",
                "current_slice": "Drive startup summary from shared coordination.",
                "declared_topology": "multi_agent_orchestrated",
                "observed_topology": "single_agent",
                "recommended_topology": "single_agent",
                "fanout_posture": "planned_scaffolding_only",
                "safe_to_fanout": False,
                "resync_required": True,
            }
        }
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertIsNotNone(model.coordination)
        assert model.coordination is not None
        self.assertEqual(
            model.coordination.current_slice,
            "Drive startup summary from shared coordination.",
        )
        self.assertTrue(model.coordination.resync_required)


class BuildWithPushReportTests(unittest.TestCase):
    """Build from push report data (quality gates)."""

    def test_guard_ok_when_preflight_passes(self) -> None:
        sources = _empty_sources()
        sources["push_report"] = {"preflight_step": {"returncode": 0}}
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertTrue(model.last_guard_ok)
        self.assertEqual(model.check_details, ())

    def test_guard_fails_with_violations(self) -> None:
        sources = _empty_sources()
        sources["push_report"] = {
            "preflight_step": {"returncode": 1},
            "violations": [
                {"step_name": "code_shape", "summary": "file too long"},
                {"step_name": "docs_check", "summary": "missing header"},
            ],
        }
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertFalse(model.last_guard_ok)
        self.assertEqual(len(model.check_details), 2)
        self.assertEqual(model.check_details[0]["check"], "code_shape")
        self.assertEqual(model.resolved_phase, "testing")


class BuildWithDaemonHeartbeatsTests(unittest.TestCase):
    """Build from daemon heartbeat data."""

    def test_publisher_running(self) -> None:
        sources = _empty_sources()
        sources["publisher_hb"] = {"pid": 123}
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertTrue(model.publisher_running)

    def test_publisher_stopped(self) -> None:
        sources = _empty_sources()
        sources["publisher_hb"] = {"pid": 123, "stopped_at_utc": "2026-01-01T00:00:00Z"}
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertFalse(model.publisher_running)

    def test_no_heartbeat_means_not_running(self) -> None:
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=_empty_sources(),
            git_override=_base_git(),
        )
        self.assertFalse(model.publisher_running)
        self.assertFalse(model.supervisor_running)
        self.assertFalse(model.codex_conductor_alive)
        self.assertFalse(model.claude_conductor_alive)


class ResolverUnitTests(unittest.TestCase):
    """Test individual resolver functions in isolation."""

    def test_resolve_quality_no_report(self) -> None:
        q = resolve_quality(None)
        self.assertTrue(q["last_guard_ok"])
        self.assertEqual(q["check_details"], ())

    def test_resolve_quality_pass(self) -> None:
        q = resolve_quality({"preflight_step": {"returncode": 0}})
        self.assertTrue(q["last_guard_ok"])

    def test_resolve_quality_fail(self) -> None:
        q = resolve_quality({
            "preflight_step": {"returncode": 1},
            "violations": [{"step_name": "check_x", "summary": "bad"}],
        })
        self.assertFalse(q["last_guard_ok"])
        self.assertEqual(len(q["check_details"]), 1)

    def test_resolve_reviewer_defaults(self) -> None:
        r = resolve_reviewer_state(None, None, None)
        self.assertEqual(r["reviewer_mode"], "single_agent")
        self.assertFalse(r["review_accepted"])
        self.assertEqual(r["attention_status"], "n/a")

    def test_resolve_daemon_all_none(self) -> None:
        d = resolve_daemon_state(_empty_sources())
        self.assertFalse(d["publisher_running"])
        self.assertFalse(d["supervisor_running"])
        self.assertFalse(d["codex_conductor_alive"])
        self.assertFalse(d["claude_conductor_alive"])

    def test_resolve_pending_packets_none(self) -> None:
        self.assertEqual(resolve_pending_packets(None), 0)

    def test_resolve_pending_packets_mixed(self) -> None:
        rs = {"packets": [
            {"status": "pending"}, {"status": "acked"}, {"status": "pending"},
        ]}
        self.assertEqual(resolve_pending_packets(rs), 2)

    def test_resolve_pending_packets_prefers_typed_queue_total(self) -> None:
        rs = {
            "queue": {"pending_total": 1},
            "packets": [{"status": "pending"}, {"status": "pending"}],
        }
        self.assertEqual(resolve_pending_packets(rs), 1)

    def test_resolve_pending_packets_fallback_ignores_stale_history(self) -> None:
        rs = {
            "packets": [
                {
                    "packet_id": "live",
                    "status": "pending",
                    "expires_at_utc": "2999-01-01T00:00:00Z",
                },
                {
                    "packet_id": "stale",
                    "status": "pending",
                    "expires_at_utc": "2000-01-01T00:00:00Z",
                },
            ],
        }
        self.assertEqual(resolve_pending_packets(rs), 1)

    def test_resolve_blocker_guard_fail(self) -> None:
        quality = {
            "last_guard_ok": False,
            "check_details": ({"check": "code_shape", "violation": "too long"},),
        }
        b = resolve_blocker_and_action(None, None, quality)
        self.assertIn("guard fail", b["top_blocker"])

    def test_resolve_blocker_none_when_green(self) -> None:
        quality = {"last_guard_ok": True, "check_details": ()}
        b = resolve_blocker_and_action(None, None, quality)
        self.assertEqual(b["top_blocker"], "none")

    def test_resolve_blocker_from_findings(self) -> None:
        quality = {"last_guard_ok": True, "check_details": ()}
        rs = {"current_session": {"open_findings": "- F1: bridge stale"}}
        b = resolve_blocker_and_action(None, rs, quality)
        self.assertIn("bridge stale", b["top_blocker"])


class DeserializationTests(unittest.TestCase):
    """Test control_plane_read_model_from_mapping."""

    def test_non_dict_returns_defaults(self) -> None:
        model = control_plane_read_model_from_mapping("not a dict")
        self.assertEqual(model.branch, "unknown")
        self.assertEqual(model.resolved_phase, "idle")

    def test_empty_dict_returns_defaults(self) -> None:
        model = control_plane_read_model_from_mapping({})
        self.assertEqual(model.branch, "unknown")
        self.assertTrue(model.worktree_clean)

    def test_full_roundtrip(self) -> None:
        original = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=_empty_sources(),
            git_override=_base_git(),
        )
        d = original.to_dict()
        restored = control_plane_read_model_from_mapping(d)
        self.assertEqual(restored.branch, original.branch)
        self.assertEqual(restored.head_sha, original.head_sha)
        self.assertEqual(restored.resolved_phase, original.resolved_phase)
        self.assertEqual(restored.push_eligible, original.push_eligible)
        self.assertEqual(restored.reviewer_mode, original.reviewer_mode)
        self.assertEqual(restored.last_guard_ok, original.last_guard_ok)
        self.assertEqual(restored.coordination, original.coordination)

    def test_check_details_roundtrip(self) -> None:
        sources = _empty_sources()
        sources["push_report"] = {
            "preflight_step": {"returncode": 1},
            "violations": [{"step_name": "check_a", "summary": "issue"}],
        }
        original = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        d = original.to_dict()
        restored = control_plane_read_model_from_mapping(d)
        self.assertEqual(len(restored.check_details), 1)
        self.assertEqual(restored.check_details[0]["check"], "check_a")


class IntegrationTests(unittest.TestCase):
    """Multi-source integration: verify resolved gates interact correctly."""

    def test_guard_fail_overrides_push_eligible(self) -> None:
        """Guard failure forces testing phase even with push-eligible receipt."""
        sources = _empty_sources()
        sources["receipt"] = {"push_action": "run_devctl_push"}
        sources["push_report"] = {"preflight_step": {"returncode": 1}}
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        # push_eligible reflects receipt, but phase reflects guard failure
        self.assertTrue(model.push_eligible)
        self.assertEqual(model.resolved_phase, "pushing")
        self.assertFalse(model.last_guard_ok)

    def test_all_green_path(self) -> None:
        """Clean worktree, passing guards, accepted review -> idle."""
        sources = _empty_sources()
        sources["receipt"] = {"push_action": "no_push_needed"}
        sources["push_report"] = {"preflight_step": {"returncode": 0}}
        sources["review_state"] = {
            "bridge": {"reviewer_mode": "active_dual_agent"},
            "reviewer_runtime": {
                "review_acceptance": {"current_verdict": "accepted"},
            },
            "attention": {"status": "healthy", "summary": "all good"},
        }
        sources["publisher_hb"] = {"pid": 100}
        sources["supervisor_hb"] = {"pid": 200}
        model = build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=_base_git(),
        )
        self.assertEqual(model.resolved_phase, "idle")
        self.assertTrue(model.last_guard_ok)
        self.assertTrue(model.review_accepted)
        self.assertTrue(model.publisher_running)
        self.assertTrue(model.supervisor_running)
        self.assertEqual(model.attention_status, "healthy")
        self.assertEqual(model.top_blocker, "none")


if __name__ == "__main__":
    unittest.main()
