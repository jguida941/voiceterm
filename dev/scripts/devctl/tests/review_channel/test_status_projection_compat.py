"""Focused tests for bridge-backed compat projection helpers."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.review_channel.status_projection_compat import (
    CompatProjectionInputs,
    build_bridge_compat_projection,
)


class StatusProjectionCompatTests(unittest.TestCase):
    def test_build_bridge_compat_projection_includes_push_enforcement(self) -> None:
        compat = build_bridge_compat_projection(
            inputs=CompatProjectionInputs(
                project_id="demo",
                bridge_text="",
                bridge_liveness={
                    "push_enforcement": {
                        "checkpoint_required": True,
                        "recommended_action": "checkpoint_before_continue",
                    }
                },
                reduced_runtime=None,
                service_identity={},
                attach_auth_policy={},
                legacy_agents=[],
                current_session={},
                reviewer_runtime={},
                bridge_state={},
                doctor={},
            )
        )

        self.assertEqual(
            compat["push_enforcement"]["recommended_action"],
            "checkpoint_before_continue",
        )
        self.assertTrue(compat["push_enforcement"]["checkpoint_required"])


if __name__ == "__main__":
    unittest.main()
