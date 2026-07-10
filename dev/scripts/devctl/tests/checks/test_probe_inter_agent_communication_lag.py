"""Tests for inter-agent communication lag probe."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from dev.scripts.checks.review_probes.probe_inter_agent_communication_lag import (
    communication_lag_hints,
)
from dev.scripts.devctl import script_catalog


class InterAgentCommunicationLagProbeTests(unittest.TestCase):
    def test_pending_peer_packet_over_threshold_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "review_state.json"
            path.write_text(
                json.dumps(
                    {
                        "packets": [
                            {
                                "packet_id": "rev_pkt_1",
                                "from_agent": "claude",
                                "to_agent": "codex",
                                "status": "pending",
                                "posted_at": "2026-05-01T17:00:00Z",
                                "latest_event_id": "rev_evt_1",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            hints = communication_lag_hints(
                path,
                now=datetime(2026, 5, 1, 17, 10, tzinfo=timezone.utc),
                lag_seconds=300,
            )

        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0].symbol, "rev_pkt_1")
        self.assertEqual(hints[0].risk_type, "inter_agent_packet_pending_lag")

    def test_recent_packet_is_not_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "review_state.json"
            path.write_text(
                json.dumps(
                    {
                        "packets": [
                            {
                                "packet_id": "rev_pkt_recent",
                                "from_agent": "claude",
                                "to_agent": "codex",
                                "status": "pending",
                                "posted_at": "2026-05-01T17:09:00Z",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            hints = communication_lag_hints(
                path,
                now=datetime(2026, 5, 1, 17, 10, tzinfo=timezone.utc),
                lag_seconds=300,
            )

        self.assertEqual(hints, [])

    def test_probe_is_registered(self) -> None:
        self.assertIn(
            "probe_inter_agent_communication_lag",
            script_catalog.PROBE_SCRIPT_FILES,
        )


if __name__ == "__main__":
    unittest.main()
