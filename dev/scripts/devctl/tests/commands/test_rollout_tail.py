"""Tests for devctl ``rollout-tail`` command and typed event parsing."""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import COMMAND_HANDLERS, build_parser
from dev.scripts.devctl.commands import rollout_tail
from dev.scripts.devctl.commands.rollout_tail import (
    PROVIDER_CLAUDE,
    PROVIDER_CODEX,
    classify_event,
    discover_latest_session,
    parse_rollout_file,
    render_json,
    render_markdown,
    render_terminal,
    resolve_session_file,
)
from dev.scripts.devctl.runtime.rollout_event import RolloutEvent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _escalation_line(timestamp: str = "2026-04-09T15:23:52.555Z") -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "arguments": json.dumps(
                    {
                        "cmd": "python3 dev/scripts/devctl.py check --profile release",
                        "sandbox_permissions": "require_escalated",
                        "justification": (
                            "Do you want me to rerun the release-profile check "
                            "outside the sandbox?"
                        ),
                    }
                ),
                "call_id": "call_TEST",
            },
        }
    )


def _error_line(timestamp: str = "2026-04-09T15:24:00.000Z") -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "type": "error",
            "payload": {
                "type": "error",
                "message": "simulated agent crash",
            },
        }
    )


def _normal_message_line(timestamp: str = "2026-04-09T15:23:40.000Z") -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "Running check now."}],
            },
        }
    )


def _write_codex_session(
    root: Path,
    session_id: str = "019d-test-0000-0000-000000000001",
    *,
    mtime: float | None = None,
    lines: list[str] | None = None,
) -> Path:
    year_dir = root / "2026" / "04" / "09"
    year_dir.mkdir(parents=True, exist_ok=True)
    rollout_path = year_dir / f"rollout-2026-04-09T11-15-01-{session_id}.jsonl"
    content = "\n".join(
        lines
        if lines is not None
        else [_normal_message_line(), _escalation_line(), _error_line()]
    )
    rollout_path.write_text(content + "\n", encoding="utf-8")
    if mtime is not None:
        import os

        os.utime(rollout_path, (mtime, mtime))
    return rollout_path


def _write_claude_session(root: Path, session_id: str = "deadbeef") -> Path:
    project_dir = root / "-some-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    path = project_dir / f"{session_id}.jsonl"
    content = "\n".join(
        [
            json.dumps(
                {
                    "type": "user",
                    "message": {
                        "content": [{"type": "text", "text": "hello claude"}],
                    },
                }
            ),
            json.dumps({"type": "error", "message": "boom"}),
        ]
    )
    path.write_text(content + "\n", encoding="utf-8")
    return path


def _make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "provider": PROVIDER_CODEX,
        "session_id": None,
        "follow": False,
        "limit": 50,
        "sessions_root": None,
        "format": "terminal",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Parser wiring
# ---------------------------------------------------------------------------


class RolloutTailParserTests(unittest.TestCase):
    def test_cli_accepts_rollout_tail_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "rollout-tail",
                "--provider",
                "codex",
                "--session-id",
                "abcd-1234",
                "--follow",
                "--limit",
                "10",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "rollout-tail")
        self.assertEqual(args.provider, "codex")
        self.assertEqual(args.session_id, "abcd-1234")
        self.assertTrue(args.follow)
        self.assertEqual(args.limit, 10)
        self.assertEqual(args.format, "json")

    def test_cli_dispatch_maps_rollout_tail_handler(self) -> None:
        self.assertIs(COMMAND_HANDLERS["rollout-tail"], rollout_tail.run)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


class RolloutEventClassificationTests(unittest.TestCase):
    def test_escalation_flagged_on_codex_function_call(self) -> None:
        raw = json.loads(_escalation_line())
        event = classify_event(raw, provider=PROVIDER_CODEX, session_id="s1")
        self.assertTrue(event.is_escalation_request)
        self.assertFalse(event.is_error)
        self.assertIn("ESCALATION", event.summary)
        self.assertEqual(event.event_type, "response_item:function_call")

    def test_error_flagged_on_codex_error(self) -> None:
        raw = json.loads(_error_line())
        event = classify_event(raw, provider=PROVIDER_CODEX, session_id="s1")
        self.assertTrue(event.is_error)
        self.assertFalse(event.is_escalation_request)

    def test_normal_message_not_flagged(self) -> None:
        raw = json.loads(_normal_message_line())
        event = classify_event(raw, provider=PROVIDER_CODEX, session_id="s1")
        self.assertFalse(event.is_escalation_request)
        self.assertFalse(event.is_error)
        self.assertIn("message[assistant]", event.summary)

    def test_claude_error_flagged(self) -> None:
        raw = {"type": "error", "message": "boom"}
        event = classify_event(raw, provider=PROVIDER_CLAUDE, session_id="s1")
        self.assertTrue(event.is_error)
        self.assertFalse(event.is_escalation_request)


# ---------------------------------------------------------------------------
# Session discovery
# ---------------------------------------------------------------------------


class SessionDiscoveryTests(unittest.TestCase):
    def test_discover_latest_session_picks_newest_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older = _write_codex_session(
                root, session_id="aaaa-0001", mtime=time.time() - 3600
            )
            newer = _write_codex_session(
                root, session_id="bbbb-0002", mtime=time.time()
            )
            picked = discover_latest_session(PROVIDER_CODEX, root=root)
            self.assertEqual(picked, newer)
            self.assertNotEqual(picked, older)

    def test_resolve_session_file_by_id_substring(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_codex_session(root, session_id="aaaa-0001")
            target = _write_codex_session(root, session_id="bbbb-9999")
            resolved = resolve_session_file(
                PROVIDER_CODEX, session_id="bbbb-9999", root=root
            )
            self.assertEqual(resolved, target)

    def test_resolve_session_file_returns_none_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(
                resolve_session_file(
                    PROVIDER_CODEX, session_id="not-there", root=Path(tmp)
                )
            )


# ---------------------------------------------------------------------------
# Parsing from file
# ---------------------------------------------------------------------------


class ParseRolloutFileTests(unittest.TestCase):
    def test_parse_file_limits_and_classifies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_codex_session(root)
            events = parse_rollout_file(path, provider=PROVIDER_CODEX, limit=10)
            self.assertEqual(len(events), 3)
            kinds = [
                (e.is_escalation_request, e.is_error) for e in events
            ]
            self.assertIn((True, False), kinds)
            self.assertIn((False, True), kinds)
            self.assertIn((False, False), kinds)

    def test_parse_file_respects_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_codex_session(root)
            events = parse_rollout_file(path, provider=PROVIDER_CODEX, limit=1)
            self.assertEqual(len(events), 1)
            # Tail limit=1 should always be the most recent line - the error.
            self.assertTrue(events[0].is_error)

    def test_parse_file_claude_error_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_claude_session(root)
            events = parse_rollout_file(path, provider=PROVIDER_CLAUDE, limit=10)
            self.assertEqual(len(events), 2)
            self.assertTrue(events[-1].is_error)

    def test_parse_file_skips_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_codex_session(
                root,
                lines=[_normal_message_line(), "not json at all", _error_line()],
            )
            events = parse_rollout_file(path, provider=PROVIDER_CODEX, limit=10)
            self.assertEqual(len(events), 2)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


class RenderingTests(unittest.TestCase):
    def _sample_events(self) -> list[RolloutEvent]:
        return [
            RolloutEvent(
                timestamp="2026-04-09T15:23:52.555Z",
                provider=PROVIDER_CODEX,
                session_id="abc",
                event_type="response_item:function_call",
                raw_payload={"type": "response_item"},
                is_escalation_request=True,
                summary="ESCALATION: rerun outside sandbox",
            ),
            RolloutEvent(
                timestamp="2026-04-09T15:23:40.000Z",
                provider=PROVIDER_CODEX,
                session_id="abc",
                event_type="response_item:message",
                raw_payload={"type": "response_item"},
                summary="message[assistant]: hello",
            ),
        ]

    def test_render_terminal_contains_escalation_label(self) -> None:
        output = render_terminal(self._sample_events(), source=Path("/tmp/x.jsonl"))
        self.assertIn("ESCALATION", output)
        self.assertIn("message[assistant]", output)

    def test_render_markdown_marks_blocker(self) -> None:
        output = render_markdown(self._sample_events(), source=Path("/tmp/x.jsonl"))
        self.assertIn("# rollout-tail", output)
        self.assertIn("**BLOCKER**", output)

    def test_render_json_roundtrips(self) -> None:
        payload = render_json(self._sample_events(), source=Path("/tmp/x.jsonl"))
        parsed = json.loads(payload)
        self.assertEqual(parsed["command"], "rollout-tail")
        self.assertEqual(len(parsed["events"]), 2)
        self.assertTrue(parsed["events"][0]["is_escalation_request"])

    def test_render_terminal_empty(self) -> None:
        output = render_terminal([], source=None)
        self.assertIn("(no events)", output)


# ---------------------------------------------------------------------------
# End-to-end command entrypoint
# ---------------------------------------------------------------------------


class RolloutTailCommandTests(unittest.TestCase):
    def test_command_autodiscovers_newest_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_codex_session(
                root, session_id="old-0001", mtime=time.time() - 7200
            )
            newest = _write_codex_session(
                root, session_id="new-0002", mtime=time.time()
            )
            args = _make_args(
                sessions_root=str(root),
                format="json",
                limit=10,
            )
            captured = StringIO()
            with patch("sys.stdout", captured):
                exit_code = rollout_tail.run(args)
            self.assertEqual(exit_code, 0)
            payload = json.loads(captured.getvalue())
            self.assertEqual(payload["source"], str(newest))
            self.assertTrue(
                any(event["is_escalation_request"] for event in payload["events"])
            )

    def test_command_reports_missing_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            args = _make_args(sessions_root=str(tmp), format="terminal")
            stderr = StringIO()
            with patch("sys.stderr", stderr):
                exit_code = rollout_tail.run(args)
            self.assertEqual(exit_code, 1)
            self.assertIn("no codex session", stderr.getvalue())

    def test_command_rejects_unknown_provider(self) -> None:
        args = _make_args(provider="bogus")
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            exit_code = rollout_tail.run(args)
        self.assertEqual(exit_code, 2)
        self.assertIn("--provider must be one of", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
