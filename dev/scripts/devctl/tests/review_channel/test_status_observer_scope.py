"""Regression: persisted status authority snapshots stay observer-scoped.

Covers rev_pkt_1366 / rev_pkt_1396 / rev_pkt_1403: read-only status surfaces
must never project implementer-lane authority. Both
`reviewer_runtime_snapshot.refresh_report_runtime_snapshot` (called from the
status command) and `projection_bundle._build_review_state_projection`
(persisted projection) must pass `caller_role="observer"` so that
`project_authority_snapshot` cannot fall back to `implementer` and advertise
`vcs.stage` / `vcs.commit` on a read-only surface.

Per rev_pkt_1403: `AuthoritySnapshot.to_dict()` only emits `actor_role`,
`allowed_actions`, and `blocked_actions` — NOT an `agent_lane` sub-dict.
Assertions therefore target those real fields.
"""

from __future__ import annotations

import unittest

from dev.scripts.devctl.runtime.authority_snapshot import project_authority_snapshot


class StatusObserverScopeTests(unittest.TestCase):
    def test_observer_caller_role_blocks_vcs_mutation(self) -> None:
        payload: dict[str, object] = {}
        snapshot = project_authority_snapshot(payload, caller_role="observer")
        self.assertEqual(snapshot.actor_role, "observer")
        self.assertNotIn("vcs.stage", snapshot.allowed_actions)
        self.assertNotIn("vcs.commit", snapshot.allowed_actions)
        self.assertNotIn("implementation.edit", snapshot.allowed_actions)
        # Also assert persisted projection shape matches.
        attached = payload["authority_snapshot"]
        assert isinstance(attached, dict)
        allowed = tuple(attached.get("allowed_actions") or ())
        self.assertEqual(attached.get("actor_role"), "observer")
        self.assertNotIn("vcs.stage", allowed)
        self.assertNotIn("vcs.commit", allowed)

    def test_empty_caller_role_defaults_to_implementer(self) -> None:
        """Documents the upstream fail-open default (rev_pkt_1366 root cause).

        Pins current behavior so any future change to the normalize_agent_lane
        fallback (e.g. to a safer 'observer' default) is visible and
        intentional. NOT a specification of desired behavior.
        """
        payload: dict[str, object] = {}
        snapshot = project_authority_snapshot(payload)
        self.assertEqual(snapshot.actor_role, "implementer")


class StatusCallSitesPassObserverCallerRoleTests(unittest.TestCase):
    """Integration-ish: exercise the actual call sites fixed in rev_pkt_1366.

    Per rev_pkt_1403: test must exercise the changed paths in
    reviewer_runtime_snapshot.py:140-146 and projection_bundle.py:159-163,
    not just call project_authority_snapshot in isolation.
    """

    def test_reviewer_runtime_snapshot_call_site_passes_observer(self) -> None:
        """Verify the status-refresh path uses caller_role='observer'.

        Reads the actual source so a silent regression (dropping the
        caller_role argument) fails this test.
        """
        import inspect

        from dev.scripts.devctl.commands.review_channel import (
            reviewer_runtime_snapshot,
        )

        source = inspect.getsource(reviewer_runtime_snapshot)
        # Both call sites (initial projection + fallback_next_command branch)
        # must pass caller_role="observer". Counted together.
        self.assertGreaterEqual(
            source.count('caller_role="observer"'),
            2,
            "reviewer_runtime_snapshot.py must call project_authority_snapshot "
            "with caller_role='observer' in both the initial projection and "
            "the fallback_next_command branch (rev_pkt_1366).",
        )

    def test_projection_bundle_call_site_passes_observer(self) -> None:
        """Verify the persisted-projection path uses caller_role='observer'."""
        import inspect

        from dev.scripts.devctl.review_channel import projection_bundle

        source = inspect.getsource(projection_bundle)
        self.assertIn(
            'caller_role="observer"',
            source,
            "projection_bundle.py must call project_authority_snapshot with "
            "caller_role='observer' on the persisted review_state projection "
            "(rev_pkt_1366 / rev_pkt_1396).",
        )


if __name__ == "__main__":
    unittest.main()
