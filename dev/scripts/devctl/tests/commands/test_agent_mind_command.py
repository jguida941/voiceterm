"""Tests for the ``agent-mind`` cross-mind polling command (BL-031)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import COMMAND_HANDLERS, build_parser
from dev.scripts.devctl.commands import agent_mind
from dev.scripts.devctl.commands.agent_mind import (
    build_slice,
    render_json,
    render_markdown,
    resolve_projection_path,
    write_projection,
)
from dev.scripts.devctl.commands.rollout_tail import (
    PROVIDER_CODEX,
    parse_rollout_file,
)
from dev.scripts.devctl.runtime.agent_mind_slice import (
    AGENT_MIND_CONTRACT_ID,
    AGENT_MIND_SCHEMA_VERSION,
    AgentMindSlice,
)
from dev.scripts.devctl.runtime.rollout_event import RolloutEvent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _reasoning_line(timestamp: str, text: str) -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "type": "response_item",
            "payload": {
                "type": "reasoning",
                "summary": [{"type": "text", "text": text}],
                "content": None,
            },
        }
    )


def _function_call_line(timestamp: str, cmd: str) -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "arguments": json.dumps({"cmd": cmd, "workdir": "/tmp"}),
                "call_id": f"call_{timestamp}",
            },
        }
    )


def _apply_patch_line(timestamp: str, patch: str) -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "apply_patch",
                "arguments": patch,
                "call_id": f"patch_{timestamp}",
            },
        }
    )


def _assistant_message_line(timestamp: str, text: str) -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": text}],
            },
        }
    )


def _task_complete_line(timestamp: str, last_message: str) -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "type": "event_msg",
            "payload": {
                "type": "task_complete",
                "turn_id": "turn-1",
                "last_agent_message": last_message,
            },
        }
    )


def _token_count_line(timestamp: str) -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "info": {"total_token_usage": {"total_tokens": 123}},
            },
        }
    )


def _escalation_line(timestamp: str) -> str:
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
                        "justification": "rerun outside sandbox?",
                    }
                ),
                "call_id": "call_esc",
            },
        }
    )


def _error_line(timestamp: str) -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "type": "error",
            "payload": {"type": "error", "message": "boom"},
        }
    )


def _write_codex_session(
    root: Path,
    *,
    lines: list[str],
    session_id: str = "019d-abcd-test-0000-111122223333",
) -> Path:
    year_dir = root / "2026" / "04" / "09"
    year_dir.mkdir(parents=True, exist_ok=True)
    path = year_dir / f"rollout-2026-04-09T11-15-01-{session_id}.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "agent": "codex",
        "since_cursor": None,
        "limit": 20,
        "project": False,
        "sessions_root": None,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Slice builder: filtering + typed shape
# ---------------------------------------------------------------------------


class SliceBuilderFilterTests(unittest.TestCase):
    def _parse_codex_events(self, root: Path, lines: list[str]):
        session_path = _write_codex_session(root, lines=lines)
        events = parse_rollout_file(session_path, provider=PROVIDER_CODEX, limit=100)
        return session_path, events

    def test_slice_from_codex_fixture_filters_reasoning_and_tool_calls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lines = [
                _reasoning_line("2026-04-09T20:01:30.123Z", "Planning check run"),
                _function_call_line(
                    "2026-04-09T20:01:34.456Z",
                    'grep -rn "claude-remote-control" dev/scripts/devctl/',
                ),
                _assistant_message_line(
                    "2026-04-09T20:01:42.789Z", "Running the command now"
                ),
            ]
            session_path, events = self._parse_codex_events(root, lines)
            slice_ = build_slice(
                events,
                agent_provider="codex",
                session_id="sess-1",
                session_path=session_path,
                since_cursor=None,
                limit=20,
            )
            self.assertEqual(slice_.event_count, 3)
            kinds = [event.event_type for event in slice_.events]
            self.assertIn("response_item:reasoning", kinds)
            self.assertIn("response_item:function_call", kinds)
            self.assertIn("response_item:message", kinds)
            tool_event = next(
                event
                for event in slice_.events
                if event.event_type == "response_item:function_call"
            )
            self.assertEqual(tool_event.tool_name, "exec_command")
            self.assertIn("claude-remote-control", tool_event.tool_command)

    def test_slice_surfaces_apply_patch_target_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patch = """*** Begin Patch
*** Update File: dev/scripts/devctl/review_channel/runtime_counts.py
@@
-old
+new
*** Add File: dev/scripts/devctl/tests/review_channel/test_runtime_counts.py
+content
*** End Patch
"""
            lines = [
                _reasoning_line("2026-04-09T20:01:30.123Z", "patching now"),
                _apply_patch_line("2026-04-09T20:01:34.456Z", patch),
            ]
            session_path, events = self._parse_codex_events(root, lines)
            slice_ = build_slice(
                events,
                agent_provider="codex",
                session_id="sess-1",
                session_path=session_path,
                since_cursor=None,
                limit=20,
            )
            patch_event = next(
                event
                for event in slice_.events
                if event.event_type == "response_item:function_call"
            )
            self.assertEqual(patch_event.tool_name, "apply_patch")
            self.assertIn("update ", patch_event.tool_command)
            self.assertIn("runtime_counts.py", patch_event.tool_command)
            self.assertIn("add ", patch_event.tool_command)
            self.assertIn("test_runtime_counts.py", patch_event.tool_command)

    def test_slice_includes_escalation_events_marked_is_escalation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lines = [
                _reasoning_line("2026-04-09T20:00:00.000Z", "Planning"),
                _escalation_line("2026-04-09T20:00:05.000Z"),
            ]
            session_path, events = self._parse_codex_events(root, lines)
            slice_ = build_slice(
                events,
                agent_provider="codex",
                session_id="sess-1",
                session_path=session_path,
                since_cursor=None,
                limit=20,
            )
            escalations = [event for event in slice_.events if event.is_escalation]
            self.assertEqual(len(escalations), 1)
            self.assertEqual(slice_.latest_escalation_at, "2026-04-09T20:00:05.000Z")

    def test_slice_skips_token_count_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lines = [
                _reasoning_line("2026-04-09T20:00:00.000Z", "plan"),
                _token_count_line("2026-04-09T20:00:01.000Z"),
                _token_count_line("2026-04-09T20:00:02.000Z"),
                _assistant_message_line("2026-04-09T20:00:03.000Z", "hello"),
            ]
            session_path, events = self._parse_codex_events(root, lines)
            slice_ = build_slice(
                events,
                agent_provider="codex",
                session_id="sess-1",
                session_path=session_path,
                since_cursor=None,
                limit=20,
            )
            self.assertEqual(slice_.event_count, 2)
            kinds = {event.event_type for event in slice_.events}
            self.assertNotIn("event_msg:token_count", kinds)

    def test_since_cursor_filter_returns_only_newer_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lines = [
                _reasoning_line("2026-04-09T20:00:00.000Z", "old"),
                _reasoning_line("2026-04-09T20:00:10.000Z", "mid"),
                _reasoning_line("2026-04-09T20:00:20.000Z", "new"),
            ]
            session_path, events = self._parse_codex_events(root, lines)
            slice_ = build_slice(
                events,
                agent_provider="codex",
                session_id="sess-1",
                session_path=session_path,
                since_cursor="2026-04-09T20:00:10.000Z",
                limit=20,
            )
            self.assertEqual(slice_.event_count, 1)
            self.assertEqual(
                slice_.events[0].timestamp, "2026-04-09T20:00:20.000Z"
            )

    def test_limit_returns_exactly_N_most_recent_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lines = [
                _reasoning_line(f"2026-04-09T20:00:{i:02d}.000Z", f"thought-{i}")
                for i in range(10)
            ]
            session_path, events = self._parse_codex_events(root, lines)
            slice_ = build_slice(
                events,
                agent_provider="codex",
                session_id="sess-1",
                session_path=session_path,
                since_cursor=None,
                limit=3,
            )
            self.assertEqual(slice_.event_count, 3)
            timestamps = [event.timestamp for event in slice_.events]
            self.assertEqual(
                timestamps,
                [
                    "2026-04-09T20:00:07.000Z",
                    "2026-04-09T20:00:08.000Z",
                    "2026-04-09T20:00:09.000Z",
                ],
            )

    def test_latest_task_complete_timestamp_captured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lines = [
                _reasoning_line("2026-04-09T20:00:00.000Z", "plan"),
                _task_complete_line(
                    "2026-04-09T20:00:05.000Z", "Done — findings above"
                ),
            ]
            session_path, events = self._parse_codex_events(root, lines)
            slice_ = build_slice(
                events,
                agent_provider="codex",
                session_id="sess-1",
                session_path=session_path,
                since_cursor=None,
                limit=20,
            )
            self.assertEqual(
                slice_.latest_task_complete_at, "2026-04-09T20:00:05.000Z"
            )
            task_events = [
                event
                for event in slice_.events
                if event.event_type == "event_msg:task_complete"
            ]
            self.assertEqual(len(task_events), 1)
            self.assertIn("Done", task_events[0].summary)

    def test_latest_escalation_timestamp_captured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lines = [
                _escalation_line("2026-04-09T20:00:00.000Z"),
                _reasoning_line("2026-04-09T20:00:05.000Z", "after"),
                _escalation_line("2026-04-09T20:00:10.000Z"),
            ]
            session_path, events = self._parse_codex_events(root, lines)
            slice_ = build_slice(
                events,
                agent_provider="codex",
                session_id="sess-1",
                session_path=session_path,
                since_cursor=None,
                limit=20,
            )
            self.assertEqual(
                slice_.latest_escalation_at, "2026-04-09T20:00:10.000Z"
            )

    def test_since_cursor_survives_over_400_noise_lines(self) -> None:
        """Regression: decision events must not be lost behind >400 noise lines.

        The old parser hard-capped the tail window at 400 raw lines
        *before* the cursor filter ran, silently dropping decision events
        beyond that window when using --since-cursor.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cursor_ts = "2026-04-09T19:59:59.000Z"
            first_decision = _reasoning_line(
                "2026-04-09T20:00:00.000Z", "first decision"
            )
            noise_lines = [
                _token_count_line(
                    f"2026-04-09T20:00:{i // 60:02d}.{i % 60:03d}Z"
                )
                for i in range(1, 420)
            ]
            second_decision = _reasoning_line(
                "2026-04-09T20:10:00.000Z", "second decision"
            )
            all_lines = [first_decision] + noise_lines + [second_decision]
            session_path = _write_codex_session(root, lines=all_lines)

            from dev.scripts.devctl.commands.agent_mind.command import (
                _build_slice_from_session,
            )
            slice_ = _build_slice_from_session(
                session_path,
                provider="codex",
                limit=20,
                since_cursor=cursor_ts,
            )
            self.assertGreaterEqual(
                slice_.event_count,
                2,
                f"Expected >=2 decision events, got {slice_.event_count}",
            )
            timestamps = [e.timestamp for e in slice_.events]
            self.assertIn("2026-04-09T20:00:00.000Z", timestamps)
            self.assertIn("2026-04-09T20:10:00.000Z", timestamps)

    def test_slice_deterministic_for_frozen_fixture(self) -> None:
        event = RolloutEvent(
            timestamp="2026-04-09T20:00:00.000Z",
            provider="codex",
            session_id="sess-1",
            event_type="response_item:reasoning",
            raw_payload={
                "payload": {
                    "type": "reasoning",
                    "summary": [{"type": "text", "text": "frozen"}],
                    "content": None,
                }
            },
            summary="",
        )
        first = build_slice(
            [event],
            agent_provider="codex",
            session_id="sess-1",
            session_path=Path("/tmp/frozen.jsonl"),
            since_cursor=None,
            limit=20,
            now_utc="2026-04-09T21:00:00.000Z",
        )
        second = build_slice(
            [event],
            agent_provider="codex",
            session_id="sess-1",
            session_path=Path("/tmp/frozen.jsonl"),
            since_cursor=None,
            limit=20,
            now_utc="2026-04-09T21:00:00.000Z",
        )
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.contract_id, AGENT_MIND_CONTRACT_ID)
        self.assertEqual(first.schema_version, AGENT_MIND_SCHEMA_VERSION)


# ---------------------------------------------------------------------------
# Projection writer
# ---------------------------------------------------------------------------


class ProjectionWriterTests(unittest.TestCase):
    def _sample_slice(self) -> AgentMindSlice:
        return build_slice(
            [
                RolloutEvent(
                    timestamp="2026-04-09T20:00:00.000Z",
                    provider="codex",
                    session_id="sess-1",
                    event_type="response_item:reasoning",
                    raw_payload={
                        "payload": {
                            "type": "reasoning",
                            "summary": [{"type": "text", "text": "projecting"}],
                            "content": None,
                        }
                    },
                    summary="",
                ),
            ],
            agent_provider="codex",
            session_id="sess-1",
            session_path=Path("/tmp/x.jsonl"),
            since_cursor=None,
            limit=20,
            now_utc="2026-04-09T21:00:00.000Z",
        )

    def test_projection_writes_latest_json_to_agent_minds_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "dev" / "reports").mkdir(parents=True)
            slice_ = self._sample_slice()
            target = write_projection(slice_, repo_root=repo_root)
            self.assertTrue(target.exists())
            self.assertEqual(target.name, "codex_latest.json")
            self.assertEqual(target.parent.name, "agent_minds")
            payload = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(payload["contract_id"], AGENT_MIND_CONTRACT_ID)
            self.assertEqual(payload["agent_provider"], "codex")
            self.assertEqual(payload["schema_version"], AGENT_MIND_SCHEMA_VERSION)
            self.assertEqual(payload["event_count"], 1)

    def test_projection_atomicity_writes_tmp_then_renames(self) -> None:
        calls: list[str] = []
        real_replace = os.replace

        def tracking_replace(src, dst):
            calls.append(str(src))
            return real_replace(src, dst)

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "dev" / "reports").mkdir(parents=True)
            slice_ = self._sample_slice()
            with patch(
                "dev.scripts.devctl.commands.agent_mind.projection.os.replace",
                side_effect=tracking_replace,
            ):
                target = write_projection(slice_, repo_root=repo_root)
            self.assertEqual(len(calls), 1)
            self.assertTrue(calls[0].endswith(".tmp"))
            self.assertTrue(target.exists())
            self.assertFalse(Path(calls[0]).exists())


# ---------------------------------------------------------------------------
# Command entrypoint
# ---------------------------------------------------------------------------


class AgentMindCommandTests(unittest.TestCase):
    def test_command_autodiscovers_and_emits_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lines = [
                _reasoning_line("2026-04-09T20:00:00.000Z", "plan"),
                _assistant_message_line(
                    "2026-04-09T20:00:05.000Z", "hello world"
                ),
            ]
            _write_codex_session(root, lines=lines)
            args = _make_args(sessions_root=str(root), format="json", limit=10)
            captured = StringIO()
            with patch("sys.stdout", captured):
                exit_code = agent_mind.run(args)
            self.assertEqual(exit_code, 0)
            payload = json.loads(captured.getvalue())
            self.assertEqual(payload["contract_id"], AGENT_MIND_CONTRACT_ID)
            self.assertEqual(payload["agent_provider"], "codex")
            self.assertGreaterEqual(payload["event_count"], 2)

    def test_unknown_provider_returns_error_exit_code(self) -> None:
        args = _make_args(agent="bogus")
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            exit_code = agent_mind.run(args)
        self.assertEqual(exit_code, 2)
        self.assertIn("--agent must be one of", stderr.getvalue())

    def test_missing_session_file_returns_none_gracefully(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            args = _make_args(sessions_root=str(tmp), format="md")
            stderr = StringIO()
            with patch("sys.stderr", stderr):
                exit_code = agent_mind.run(args)
            self.assertEqual(exit_code, 1)
            self.assertIn("no codex session", stderr.getvalue())

    def test_since_cursor_keeps_decision_before_more_than_400_noise_lines(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            noise_lines = [
                _token_count_line(
                    f"2026-04-09T20:{1 + index // 60:02d}:{index % 60:02d}.000Z"
                )
                for index in range(401)
            ]
            _write_codex_session(
                root,
                lines=[
                    _reasoning_line("2026-04-09T20:00:00.000Z", "old"),
                    _reasoning_line(
                        "2026-04-09T20:00:01.000Z",
                        "decision survives",
                    ),
                    *noise_lines,
                ],
            )
            args = _make_args(
                sessions_root=str(root),
                format="json",
                limit=10,
                since_cursor="2026-04-09T20:00:00.000Z",
            )
            captured = StringIO()
            with patch("sys.stdout", captured):
                exit_code = agent_mind.run(args)
            self.assertEqual(exit_code, 0)
            payload = json.loads(captured.getvalue())
            self.assertEqual(payload["event_count"], 1)
            self.assertEqual(
                payload["events"][0]["summary"],
                "decision survives",
            )

    def test_cli_parser_accepts_agent_mind_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "agent-mind",
                "--agent",
                "codex",
                "--since-cursor",
                "2026-04-09T20:00:00.000Z",
                "--limit",
                "5",
                "--project",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "agent-mind")
        self.assertEqual(args.agent, "codex")
        self.assertEqual(args.since_cursor, "2026-04-09T20:00:00.000Z")
        self.assertEqual(args.limit, 5)
        self.assertTrue(args.project)
        self.assertEqual(args.format, "json")

    def test_cli_dispatch_maps_agent_mind_handler(self) -> None:
        self.assertIs(COMMAND_HANDLERS["agent-mind"], agent_mind.run)


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


class RenderingTests(unittest.TestCase):
    def _fixture_slice(self) -> AgentMindSlice:
        return build_slice(
            [
                RolloutEvent(
                    timestamp="2026-04-09T20:01:30.123Z",
                    provider="codex",
                    session_id="sess-1",
                    event_type="response_item:reasoning",
                    raw_payload={
                        "payload": {
                            "type": "reasoning",
                            "summary": [
                                {"type": "text", "text": "plan the fix"}
                            ],
                            "content": None,
                        }
                    },
                    summary="",
                ),
                RolloutEvent(
                    timestamp="2026-04-09T20:02:05.234Z",
                    provider="codex",
                    session_id="sess-1",
                    event_type="event_msg:task_complete",
                    raw_payload={
                        "payload": {
                            "type": "task_complete",
                            "last_agent_message": "All good",
                        }
                    },
                    summary="",
                ),
            ],
            agent_provider="codex",
            session_id="sess-1",
            session_path=Path("/tmp/sess.jsonl"),
            since_cursor=None,
            limit=20,
            now_utc="2026-04-09T21:00:00.000Z",
        )

    def test_render_markdown_header_and_task_complete(self) -> None:
        rendered = render_markdown(self._fixture_slice())
        self.assertIn("# agent-mind (codex)", rendered)
        self.assertIn("## Recent decisions", rendered)
        self.assertIn("TASK COMPLETE", rendered)
        self.assertIn("plan the fix", rendered)

    def test_render_json_payload_roundtrips(self) -> None:
        payload = json.loads(render_json(self._fixture_slice()))
        self.assertEqual(payload["contract_id"], AGENT_MIND_CONTRACT_ID)
        self.assertEqual(payload["event_count"], 2)
        self.assertEqual(
            payload["latest_task_complete_at"], "2026-04-09T20:02:05.234Z"
        )


# ---------------------------------------------------------------------------
# Projection path resolution
# ---------------------------------------------------------------------------


class ProjectionPathResolutionTests(unittest.TestCase):
    def test_resolve_projection_path_uses_reports_root_rel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            path = resolve_projection_path("codex", repo_root=repo_root)
            self.assertEqual(path.name, "codex_latest.json")
            self.assertEqual(path.parent.name, "agent_minds")
            self.assertTrue(str(path).startswith(str(repo_root)))


# ---------------------------------------------------------------------------
# Live run soft-skip
# ---------------------------------------------------------------------------


class LiveRunSoftSkipTests(unittest.TestCase):
    def test_live_run_against_current_codex_session_produces_md_output(self) -> None:
        codex_root = Path.home() / ".codex" / "sessions"
        if not codex_root.exists():
            self.skipTest("no live codex sessions directory present")
        args = _make_args(
            sessions_root=str(codex_root),
            format="md",
            limit=5,
        )
        captured = StringIO()
        stderr = StringIO()
        with patch("sys.stdout", captured), patch("sys.stderr", stderr):
            exit_code = agent_mind.run(args)
        if exit_code != 0:
            self.skipTest(
                f"live codex session not available: {stderr.getvalue().strip()}"
            )
        self.assertIn("# agent-mind (codex)", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
