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
from dev.scripts.devctl.commands.rollout_tail.parser import _tail_lines
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


# ---------------------------------------------------------------------------
# Claude discovery layout quirks (subagents, non-UUID filenames)
# ---------------------------------------------------------------------------


_VALID_CLAUDE_UUID = "abcdef01-2345-6789-abcd-ef0123456789"
_OTHER_CLAUDE_UUID = "11111111-2222-3333-4444-555555555555"


def _write_claude_uuid_session(
    root: Path, project: str, session_uuid: str, *, mtime: float | None = None
) -> Path:
    project_dir = root / project
    project_dir.mkdir(parents=True, exist_ok=True)
    path = project_dir / f"{session_uuid}.jsonl"
    path.write_text(
        json.dumps({"type": "user", "message": {"content": "hi"}}) + "\n",
        encoding="utf-8",
    )
    if mtime is not None:
        import os

        os.utime(path, (mtime, mtime))
    return path


def _write_claude_subagent(
    root: Path, project: str, session_uuid: str, *, mtime: float | None = None
) -> Path:
    subagent_dir = root / project / session_uuid / "subagents"
    subagent_dir.mkdir(parents=True, exist_ok=True)
    path = subagent_dir / "agent-x.jsonl"
    path.write_text(
        json.dumps({"type": "assistant", "message": {"content": "sub"}}) + "\n",
        encoding="utf-8",
    )
    if mtime is not None:
        import os

        os.utime(path, (mtime, mtime))
    return path


def _write_claude_memory_artifact(
    root: Path, project: str, filename: str, *, mtime: float | None = None
) -> Path:
    """Write a non-session JSONL artifact under ``<project>/memory/``.

    Claude Code's project directories can hold arbitrary nested JSONL
    artifacts (memory projections, tool-results, notebook data) that are
    not real chat sessions. The discovery picker must leave those alone
    even when their mtime is newer than the real session file. Mirrors
    the F3 Codex finding on ``memory/**`` exclusion.
    """
    memory_dir = root / project / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    path = memory_dir / filename
    path.write_text(
        json.dumps({"type": "memory", "payload": "not-a-session"}) + "\n",
        encoding="utf-8",
    )
    if mtime is not None:
        import os

        os.utime(path, (mtime, mtime))
    return path


class ClaudeDiscoveryLayoutTests(unittest.TestCase):
    def test_discover_excludes_newer_subagent_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = time.time()
            real_session = _write_claude_uuid_session(
                root, "-proj", _VALID_CLAUDE_UUID, mtime=now - 60
            )
            # Subagent is newer, but must not be picked as the active session.
            _write_claude_subagent(
                root, "-proj", _VALID_CLAUDE_UUID, mtime=now + 60
            )
            picked = discover_latest_session(PROVIDER_CLAUDE, root=root)
            self.assertEqual(picked, real_session)

    def test_discover_skips_non_uuid_session_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "-proj"
            project_dir.mkdir(parents=True, exist_ok=True)
            # Non-UUID stray file at depth 2 must be ignored even though
            # the narrow glob would otherwise match it.
            stray = project_dir / "not-a-uuid.jsonl"
            stray.write_text("{}\n", encoding="utf-8")
            self.assertIsNone(
                discover_latest_session(PROVIDER_CLAUDE, root=root)
            )

    def test_discover_picks_newest_uuid_session_across_projects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = time.time()
            _write_claude_uuid_session(
                root, "-proj-a", _VALID_CLAUDE_UUID, mtime=now - 3600
            )
            newer = _write_claude_uuid_session(
                root, "-proj-b", _OTHER_CLAUDE_UUID, mtime=now
            )
            picked = discover_latest_session(PROVIDER_CLAUDE, root=root)
            self.assertEqual(picked, newer)

    def test_resolve_session_file_filters_claude_subagents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = time.time()
            real = _write_claude_uuid_session(
                root, "-proj", _VALID_CLAUDE_UUID, mtime=now
            )
            _write_claude_subagent(
                root, "-proj", _VALID_CLAUDE_UUID, mtime=now + 60
            )
            resolved = resolve_session_file(
                PROVIDER_CLAUDE, session_id=_VALID_CLAUDE_UUID, root=root
            )
            self.assertEqual(resolved, real)

    def test_discover_excludes_memory_artifacts_even_when_uuid_named(
        self,
    ) -> None:
        """F3 regression: ``memory/**`` stays excluded from Claude auto-discovery.

        A UUID-named JSONL artifact under a project's ``memory/`` subdir
        must not be picked as a real session even when its mtime is
        newer than the real session file at depth 2. This pins down
        Codex's specific ``memory/**`` example so the narrow
        ``glob('*/*.jsonl')`` + UUID-stem filter cannot regress into
        the old recursive ``rglob('*.jsonl')`` shape.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = time.time()
            real_session = _write_claude_uuid_session(
                root, "-proj", _VALID_CLAUDE_UUID, mtime=now - 60
            )
            # UUID-named artifact under memory/ — identical stem shape to
            # a real session, and a newer mtime, so a regression back to
            # recursive rglob would pick this instead of the real one.
            _write_claude_memory_artifact(
                root,
                "-proj",
                f"{_OTHER_CLAUDE_UUID}.jsonl",
                mtime=now + 600,
            )
            picked = discover_latest_session(PROVIDER_CLAUDE, root=root)
            self.assertEqual(picked, real_session)

    def test_resolve_by_id_skips_memory_artifacts(self) -> None:
        """F3 regression: id-based resolve also ignores ``memory/**`` hits."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = time.time()
            _write_claude_memory_artifact(
                root,
                "-proj",
                f"{_OTHER_CLAUDE_UUID}.jsonl",
                mtime=now + 600,
            )
            # No real session exists under the project; id-based resolve
            # must return None rather than falling through to the memory
            # artifact with a UUID-shaped name.
            resolved = resolve_session_file(
                PROVIDER_CLAUDE, session_id=_OTHER_CLAUDE_UUID, root=root
            )
            self.assertIsNone(resolved)


# ---------------------------------------------------------------------------
# Tail reader: off-by-one across reverse-seek block boundary
# ---------------------------------------------------------------------------


def _build_large_rollout_lines(count: int, filler_bytes: int) -> list[str]:
    """Build ``count`` distinct JSONL events each padded to ``filler_bytes``."""
    lines: list[str] = []
    for index in range(count):
        payload = {
            "timestamp": f"2026-04-09T15:00:{index:02d}.000Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        # Filler keeps each line well above 1 byte so the
                        # cumulative size crosses the 64 KiB tail window.
                        "text": f"evt-{index:04d}-" + ("x" * filler_bytes),
                    }
                ],
            },
        }
        lines.append(json.dumps(payload))
    return lines


class TailReaderBoundaryTests(unittest.TestCase):
    def test_tail_lines_returns_full_complete_lines_across_block_boundary(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "big.jsonl"
            # 30 lines * ~5 KiB filler => ~150 KiB, well past the 64 KiB
            # reverse-seek block boundary inside ``_tail_lines``.
            lines = _build_large_rollout_lines(count=30, filler_bytes=5_000)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertGreater(path.stat().st_size, 128 * 1024)

            tailed = _tail_lines(path, limit=5)
            self.assertEqual(len(tailed), 5)
            # Every returned line must be a complete, parseable JSON event
            # with the expected trailing marker, not a truncated prefix.
            for text in tailed:
                decoded = json.loads(text)
                self.assertEqual(decoded["type"], "response_item")
                self.assertTrue(
                    decoded["payload"]["content"][0]["text"].startswith("evt-")
                )
            # Last five events must line up with the last five we wrote.
            expected_tail = [json.loads(line) for line in lines[-5:]]
            actual_tail = [json.loads(text) for text in tailed]
            self.assertEqual(actual_tail, expected_tail)

    def test_rollout_tail_command_returns_exact_limit_on_large_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            year_dir = root / "2026" / "04" / "09"
            year_dir.mkdir(parents=True, exist_ok=True)
            rollout_path = (
                year_dir / "rollout-2026-04-09T11-15-01-cccc-0003.jsonl"
            )
            lines = _build_large_rollout_lines(count=40, filler_bytes=4_000)
            rollout_path.write_text(
                "\n".join(lines) + "\n", encoding="utf-8"
            )
            self.assertGreater(rollout_path.stat().st_size, 128 * 1024)

            events = parse_rollout_file(
                rollout_path, provider=PROVIDER_CODEX, limit=5
            )
            self.assertEqual(len(events), 5)
            # All five must classify as normal assistant messages — a
            # truncated leading line would have been dropped by the JSON
            # decoder and shrunk the result below 5.
            for event in events:
                self.assertFalse(event.is_error)
                self.assertFalse(event.is_escalation_request)
                self.assertIn("message[assistant]", event.summary)


if __name__ == "__main__":
    unittest.main()
