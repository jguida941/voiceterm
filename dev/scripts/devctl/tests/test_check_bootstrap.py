"""Tests for shared check bootstrap helpers."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from dev.scripts.checks import check_bootstrap


class CheckBootstrapTests(unittest.TestCase):
    """Protect shared helper behavior used by standalone check scripts."""

    def test_utc_timestamp_uses_z_suffix(self) -> None:
        timestamp = check_bootstrap.utc_timestamp()
        self.assertTrue(timestamp.endswith("Z"))
        self.assertNotIn("+00:00", timestamp)

    def test_emit_runtime_error_json_uses_utc_timestamp(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            rc = check_bootstrap.emit_runtime_error("demo-check", "json", "boom")

        self.assertEqual(rc, 2)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["command"], "demo-check")
        self.assertEqual(payload["error"], "boom")
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["timestamp"].endswith("Z"))


if __name__ == "__main__":
    unittest.main()
