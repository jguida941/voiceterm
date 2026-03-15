"""Tests for machine-friendly output artifact helpers."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from pathlib import Path

from dev.scripts.devctl.runtime.machine_output import (
    ArtifactOutputOptions,
    clear_machine_output_metrics,
    consume_machine_output_metrics,
    emit_machine_artifact_output,
)


class MachineOutputTests(unittest.TestCase):
    def tearDown(self) -> None:
        clear_machine_output_metrics()

    def test_json_output_path_emits_compact_receipt_and_records_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "report.json"
            args = SimpleNamespace(
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                rc = emit_machine_artifact_output(
                    args,
                    command="platform-contracts",
                    json_payload={"ok": True, "items": ["a", "b"]},
                    human_output="# ignored\n",
                    options=ArtifactOutputOptions(summary={"item_count": 2}),
                )

            self.assertEqual(rc, 0)
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                '{"command":"platform-contracts","items":["a","b"],"ok":true}',
            )
            receipt = json.loads(stdout.getvalue().strip())
            self.assertEqual(receipt["command"], "platform-contracts")
            self.assertTrue(receipt["ok"])
            self.assertEqual(receipt["summary"]["item_count"], 2)
            self.assertEqual(receipt["artifact"]["path"], str(output_path))
            self.assertGreater(receipt["artifact"]["size_bytes"], 0)
            self.assertGreater(receipt["artifact"]["estimated_tokens"], 0)
            self.assertLess(len(stdout.getvalue().strip().encode("utf-8")), 512)
            metrics = consume_machine_output_metrics()
            self.assertIsNotNone(metrics)
            self.assertEqual(metrics["path"], str(output_path))
            self.assertEqual(metrics["delivery"], "file")
            self.assertGreater(metrics["stdout_receipt_size_bytes"], 0)

    def test_json_stdout_only_records_stdout_metrics(self) -> None:
        args = SimpleNamespace(
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            rc = emit_machine_artifact_output(
                args,
                command="loop-packet",
                json_payload={"ok": True, "risk": "low"},
                human_output="# ignored\n",
            )

        self.assertEqual(rc, 0)
        self.assertEqual(
            stdout.getvalue().strip(),
            '{"command":"loop-packet","ok":true,"risk":"low"}',
        )
        metrics = consume_machine_output_metrics()
        self.assertIsNotNone(metrics)
        self.assertIsNone(metrics["path"])
        self.assertEqual(metrics["delivery"], "stdout")


if __name__ == "__main__":
    unittest.main()
