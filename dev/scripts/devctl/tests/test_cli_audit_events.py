"""CLI-level audit event emission tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl import cli


class CliAuditEventTests(unittest.TestCase):
    def test_main_emits_audit_event_for_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "devctl-events.jsonl"
            with patch.dict(
                "os.environ",
                {
                    "DEVCTL_AUDIT_EVENT_LOG": str(log_path),
                    "DEVCTL_AUDIT_CYCLE_ID": "unit-cycle",
                    "DEVCTL_EXECUTION_SOURCE": "script_only",
                    "DEVCTL_EXECUTION_ACTOR": "script",
                },
                clear=False,
            ):
                with patch("sys.argv", ["devctl", "list"]):
                    rc = cli.main()

            self.assertEqual(rc, 0)
            rows = log_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(rows), 1)
            last_row = json.loads(rows[-1])
            self.assertEqual(last_row["cycle_id"], "unit-cycle")
            self.assertEqual(last_row["command"], "list")
            self.assertTrue(last_row["success"])
            self.assertEqual(last_row["step"], "devctl:list")


if __name__ == "__main__":
    unittest.main()
