"""Tests for devctl audit event emission helpers."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl import audit_events


class AuditEventsPolicyTests(unittest.TestCase):
    def test_resolve_event_log_path_prefers_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            policy_path = Path(tmp_dir) / "policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "audit_metrics": {
                            "event_log_path": "dev/reports/audits/from-policy.jsonl"
                        }
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(audit_events, "POLICY_PATH", policy_path):
                with patch.dict("os.environ", {}, clear=False):
                    resolved = audit_events.resolve_event_log_path()

        self.assertEqual(
            resolved,
            (audit_events.REPO_ROOT / "dev/reports/audits/from-policy.jsonl").resolve(),
        )

    def test_env_override_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            override = Path(tmp_dir) / "override.jsonl"
            with patch.dict(
                "os.environ",
                {"DEVCTL_AUDIT_EVENT_LOG": str(override)},
                clear=False,
            ):
                resolved = audit_events.resolve_event_log_path()
        self.assertEqual(os.path.realpath(resolved), os.path.realpath(override))


class AuditEventsPayloadTests(unittest.TestCase):
    def test_build_payload_uses_defaults_and_success(self) -> None:
        args = SimpleNamespace(profile="ci")
        with patch.dict("os.environ", {}, clear=False):
            payload = audit_events.build_audit_event_payload(
                command="check",
                args=args,
                returncode=0,
                duration_seconds=1.23,
                argv=["check", "--profile", "ci"],
            )
        self.assertEqual(payload["area"], "governance")
        self.assertEqual(payload["step"], "devctl:check:ci")
        self.assertTrue(payload["success"])
        self.assertEqual(payload["execution_source"], "script_only")
        self.assertEqual(payload["argv"], ["check", "--profile", "ci"])

    def test_emit_event_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "events.jsonl"
            with patch.dict(
                "os.environ",
                {
                    "DEVCTL_AUDIT_EVENT_LOG": str(output_path),
                    "DEVCTL_AUDIT_CYCLE_ID": "baseline-cycle",
                    "DEVCTL_EXECUTION_SOURCE": "ai_assisted",
                    "DEVCTL_EXECUTION_ACTOR": "ai",
                },
                clear=False,
            ):
                audit_events.emit_devctl_audit_event(
                    command="triage-loop",
                    args=SimpleNamespace(profile=None),
                    returncode=1,
                    duration_seconds=3.4,
                    argv=["triage-loop", "--mode", "report-only"],
                )
            lines = output_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            row = json.loads(lines[0])
            self.assertEqual(row["cycle_id"], "baseline-cycle")
            self.assertEqual(row["command"], "triage-loop")
            self.assertEqual(row["execution_source"], "ai_assisted")
            self.assertFalse(row["success"])


if __name__ == "__main__":
    unittest.main()
