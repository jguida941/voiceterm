"""Regression: persisted status authority snapshots stay observer-scoped.

Covers the rev_pkt_1366 / rev_pkt_1396 contract: read-only status surfaces
must never project implementer-lane permissions (vcs.stage / vcs.commit).
Both `reviewer_runtime_snapshot.refresh_report_runtime_snapshot` (called from
the status command) and `projection_bundle._build_review_state_projection`
(persisted projection) must pass `caller_role="observer"` so
`project_authority_snapshot` cannot fall back to `implementer`.
"""

from __future__ import annotations

import unittest

from dev.scripts.devctl.runtime.authority_snapshot import project_authority_snapshot


class StatusObserverScopeTests(unittest.TestCase):
    def test_observer_caller_role_blocks_vcs_mutation(self) -> None:
        payload: dict[str, object] = {}
        snapshot = project_authority_snapshot(payload, caller_role="observer")
        self.assertEqual(snapshot.actor_role, "observer")
        attached = payload["authority_snapshot"]
        assert isinstance(attached, dict)
        agent_lane = attached.get("agent_lane") or {}
        perms = tuple(agent_lane.get("permissions") or ())
        self.assertNotIn("vcs.stage", perms)
        self.assertNotIn("vcs.commit", perms)
        # Observer surface is read-only: no mutation permissions at all.
        self.assertNotIn("implementation.edit", perms)

    def test_empty_caller_role_still_defaults_to_implementer(self) -> None:
        """Documents the upstream fail-open default (rev_pkt_1366 root cause).

        This test is NOT a specification of desired behavior — it pins the
        current default so that if normalize_agent_lane's fallback changes to
        a safer value (e.g. observer), the change is visible and intentional.
        """
        payload: dict[str, object] = {}
        snapshot = project_authority_snapshot(payload)
        self.assertEqual(snapshot.actor_role, "implementer")


if __name__ == "__main__":
    unittest.main()
