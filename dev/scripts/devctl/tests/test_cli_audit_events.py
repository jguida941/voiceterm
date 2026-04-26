"""CLI-level audit event emission tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl import cli


class CliAuditEventTests(unittest.TestCase):
    def test_main_emits_audit_event_for_write_command(self) -> None:
        """Verify that non-read-only commands still emit audit events."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "devctl-events.jsonl"
            with patch.dict(
                "os.environ",
                {
                    "DEVCTL_AUDIT_EVENT_LOG": str(log_path),
                    "DEVCTL_AUDIT_CYCLE_ID": "unit-cycle",
                    "DEVCTL_EXECUTION_SOURCE": "script_only",
                    "DEVCTL_EXECUTION_ACTOR": "script",
                    "DEVCTL_DATA_SCIENCE_DISABLE": "1",
                },
                clear=False,
            ):
                with (
                    patch("sys.argv", ["devctl", "status", "--format", "json"]),
                    patch.object(
                        cli,
                        "maybe_auto_ingest_devctl_result",
                    ) as ingest_mock,
                ):
                    rc = cli.main()

            self.assertEqual(rc, 0)
            ingest_mock.assert_called_once()
            self.assertEqual(ingest_mock.call_args.kwargs["command"], "status")
            self.assertEqual(ingest_mock.call_args.kwargs["returncode"], 0)
            self.assertFalse(ingest_mock.call_args.kwargs["read_only"])
            rows = log_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(rows), 1)
            last_row = json.loads(rows[-1])
            self.assertEqual(last_row["cycle_id"], "unit-cycle")
            self.assertEqual(last_row["command"], "status")
            self.assertTrue(last_row["success"])
            self.assertEqual(last_row["step"], "devctl:status")


if __name__ == "__main__":
    unittest.main()
