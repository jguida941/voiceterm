"""Tests for the canonical startup-blocker decision reducer."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.runtime.startup_blocker_decision import (
    BlockerSnapshot,
    derive_blocker_decision,
)


class DeriveBlockerDecisionTests(unittest.TestCase):
    """Verify the canonical reducer's priority ordering and evidence trail.

    The reducer replaces three independent producers that previously
    derived ``top_blocker`` in parallel (dashboard, control-plane
    read model, startup-context). Every rule must stay deterministic so
    the consumers of ``StartupContext.blocker`` never diverge.
    """

    def test_quality_failing_list_wins(self) -> None:
        snapshot = derive_blocker_decision(
            quality={"failing": ["dev/scripts/devctl/common_io.py"]},
            doctor={"blocked_reason": "pipeline_down"},
            session={"open_findings": "- F1: something else"},
            push_action="await_checkpoint",
        )
        self.assertEqual(snapshot.blocker_source, "quality")
        self.assertIn("common_io.py", snapshot.top_blocker)
        self.assertEqual(snapshot.next_action, "await_checkpoint")
        self.assertTrue(
            any("quality.failing" in line for line in snapshot.derivation_evidence)
        )

    def test_last_guard_ok_false_with_check_details(self) -> None:
        snapshot = derive_blocker_decision(
            quality={
                "last_guard_ok": False,
                "check_details": [{"check": "code_shape"}],
            },
            doctor={},
            session={},
        )
        self.assertEqual(snapshot.blocker_source, "quality")
        self.assertIn("code_shape", snapshot.top_blocker)

    def test_last_guard_ok_false_without_details(self) -> None:
        snapshot = derive_blocker_decision(
            quality={"last_guard_ok": False},
            doctor={},
            session={},
        )
        self.assertEqual(snapshot.blocker_source, "quality")
        self.assertEqual(snapshot.top_blocker, "code-shape debt")

    def test_doctor_blocked_reason_promoted(self) -> None:
        snapshot = derive_blocker_decision(
            quality={"failing": []},
            doctor={"blocked_reason": "reviewer_runtime_stopped"},
            session={"open_findings": "- F1: minor"},
        )
        self.assertEqual(snapshot.blocker_source, "doctor")
        self.assertEqual(snapshot.top_blocker, "reviewer_runtime_stopped")

    def test_doctor_pipeline_unavailable_is_ignored(self) -> None:
        snapshot = derive_blocker_decision(
            quality={"failing": []},
            doctor={"blocked_reason": "pipeline_unavailable"},
            session={"open_findings": "- F1: real finding"},
        )
        # The sentinel ``pipeline_unavailable`` is treated as "no doctor
        # signal", so the reducer should fall through to session findings.
        self.assertEqual(snapshot.blocker_source, "session")
        self.assertIn("real finding", snapshot.top_blocker)

    def test_session_open_findings_clipped(self) -> None:
        long_finding = "- F1: " + ("x" * 200)
        snapshot = derive_blocker_decision(
            quality={},
            doctor={},
            session={"open_findings": long_finding},
        )
        self.assertEqual(snapshot.blocker_source, "session")
        self.assertTrue(snapshot.top_blocker.endswith("..."))
        self.assertLessEqual(len(snapshot.top_blocker), 63)

    def test_none_when_all_clean(self) -> None:
        snapshot = derive_blocker_decision(
            quality={"failing": []},
            doctor={"blocked_reason": ""},
            session={"open_findings": "none"},
        )
        self.assertEqual(snapshot.blocker_source, "none")
        self.assertEqual(snapshot.top_blocker, "none")
        self.assertIn("no_blocker_detected", snapshot.derivation_evidence)

    def test_default_snapshot_shape(self) -> None:
        snapshot = BlockerSnapshot()
        payload = snapshot.to_dict()
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["contract_id"], "BlockerSnapshot")
        self.assertEqual(payload["top_blocker"], "none")
        self.assertEqual(payload["next_action"], "")
        self.assertEqual(payload["blocker_source"], "none")
        self.assertEqual(payload["derivation_evidence"], [])

    def test_none_inputs_do_not_crash(self) -> None:
        snapshot = derive_blocker_decision(
            quality=None,
            doctor=None,
            session=None,
        )
        self.assertEqual(snapshot.blocker_source, "none")
        self.assertEqual(snapshot.top_blocker, "none")

    def test_push_action_threads_into_next_action(self) -> None:
        snapshot = derive_blocker_decision(
            quality={"failing": ["x.py"]},
            doctor={},
            session={},
            push_action="run_devctl_push",
        )
        self.assertEqual(snapshot.next_action, "run_devctl_push")


if __name__ == "__main__":
    unittest.main()
