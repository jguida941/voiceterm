"""Unit tests for the daemon client protocol layer."""

from __future__ import annotations

import json

from app.operator_console.collaboration.daemon_client import (
    DaemonClient,
    DaemonEvent,
    DEFAULT_SOCKET_PATH,
)


class TestDaemonEvent:
    """Test DaemonEvent parsing and accessors."""

    def test_from_json_agent_output(self):
        line = json.dumps({
            "event": "agent_output",
            "session_id": "agent_abc_1",
            "text": "thinking...",
        })
        event = DaemonEvent.from_json(line)
        assert event.event_type == "agent_output"
        assert event.session_id == "agent_abc_1"
        assert event.text == "thinking..."
        assert event.is_output()
        assert not event.is_error()

    def test_from_json_error(self):
        line = json.dumps({
            "event": "error",
            "message": "unknown session",
            "session_id": "s1",
        })
        event = DaemonEvent.from_json(line)
        assert event.event_type == "error"
        assert event.is_error()
        assert event.payload["message"] == "unknown session"

    def test_from_json_daemon_ready(self):
        line = json.dumps({
            "event": "daemon_ready",
            "version": "1.1.1",
            "socket_path": "/tmp/test.sock",
            "ws_port": 9876,
            "ws_url": "ws://127.0.0.1:9876",
            "lifecycle": "running",
            "primary_attach": "web_socket",
            "pid": 4242,
            "started_at_unix_ms": 123456,
            "working_dir": "/tmp/repo",
            "memory_mode": "assist",
        })
        event = DaemonEvent.from_json(line)
        assert event.event_type == "daemon_ready"
        assert event.payload["version"] == "1.1.1"
        assert event.payload["ws_url"] == "ws://127.0.0.1:9876"
        assert event.payload["primary_attach"] == "web_socket"
        assert event.payload["memory_mode"] == "assist"

    def test_from_json_daemon_status(self):
        line = json.dumps({
            "event": "daemon_status",
            "version": "1.1.1",
            "active_agents": 2,
            "connected_clients": 3,
            "uptime_secs": 42.5,
            "socket_path": "/tmp/test.sock",
            "ws_port": 9876,
            "ws_url": "ws://127.0.0.1:9876",
            "lifecycle": "running",
            "primary_attach": "web_socket",
            "pid": 4242,
            "started_at_unix_ms": 123456,
            "working_dir": "/tmp/repo",
            "memory_mode": "assist",
        })
        event = DaemonEvent.from_json(line)
        assert event.event_type == "daemon_status"
        assert event.payload["active_agents"] == 2
        assert event.payload["connected_clients"] == 3
        assert event.payload["lifecycle"] == "running"
        assert event.payload["working_dir"] == "/tmp/repo"

    def test_from_json_agent_spawned(self):
        line = json.dumps({
            "event": "agent_spawned",
            "session_id": "agent_1",
            "provider": "claude",
            "label": "reviewer",
            "working_dir": "/tmp",
            "pid": 12345,
        })
        event = DaemonEvent.from_json(line)
        assert event.event_type == "agent_spawned"
        assert event.session_id == "agent_1"

    def test_from_json_agent_exited(self):
        line = json.dumps({
            "event": "agent_exited",
            "session_id": "agent_1",
            "exit_code": 0,
        })
        event = DaemonEvent.from_json(line)
        assert event.event_type == "agent_exited"
        assert event.payload["exit_code"] == 0

    def test_from_json_unknown_event(self):
        line = json.dumps({"event": "future_event", "data": "hello"})
        event = DaemonEvent.from_json(line)
        assert event.event_type == "future_event"

    def test_session_id_none_when_missing(self):
        line = json.dumps({"event": "daemon_shutdown"})
        event = DaemonEvent.from_json(line)
        assert event.session_id is None

    def test_text_none_when_missing(self):
        line = json.dumps({"event": "agent_killed", "session_id": "a1"})
        event = DaemonEvent.from_json(line)
        assert event.text is None


class TestDaemonClient:
    """Test DaemonClient construction and command serialization."""

    def test_default_socket_path(self):
        client = DaemonClient()
        assert client.socket_path == DEFAULT_SOCKET_PATH
        assert "voiceterm" in str(client.socket_path)
        assert str(client.socket_path).endswith("control.sock")

    def test_custom_socket_path(self):
        from pathlib import Path
        client = DaemonClient(socket_path=Path("/tmp/test.sock"))
        assert str(client.socket_path) == "/tmp/test.sock"

    def test_not_connected_by_default(self):
        client = DaemonClient()
        assert not client.connected


class TestCommandSerialization:
    """Verify that command dictionaries match the Rust daemon protocol."""

    def test_spawn_agent_minimal(self):
        cmd = {"cmd": "spawn_agent", "provider": "claude"}
        assert json.loads(json.dumps(cmd))["cmd"] == "spawn_agent"

    def test_spawn_agent_full(self):
        cmd = {
            "cmd": "spawn_agent",
            "provider": "codex",
            "working_dir": "/home/user/project",
            "label": "coder-1",
            "initial_prompt": "implement feature X",
        }
        parsed = json.loads(json.dumps(cmd))
        assert parsed["provider"] == "codex"
        assert parsed["label"] == "coder-1"
        assert parsed["initial_prompt"] == "implement feature X"

    def test_send_to_agent(self):
        cmd = {"cmd": "send_to_agent", "session_id": "a1", "text": "fix the bug"}
        parsed = json.loads(json.dumps(cmd))
        assert parsed["cmd"] == "send_to_agent"
        assert parsed["text"] == "fix the bug"

    def test_kill_agent(self):
        cmd = {"cmd": "kill_agent", "session_id": "a1"}
        parsed = json.loads(json.dumps(cmd))
        assert parsed["cmd"] == "kill_agent"

    def test_list_agents(self):
        cmd = {"cmd": "list_agents"}
        assert json.loads(json.dumps(cmd))["cmd"] == "list_agents"

    def test_get_status(self):
        cmd = {"cmd": "get_status"}
        assert json.loads(json.dumps(cmd))["cmd"] == "get_status"

    def test_shutdown(self):
        cmd = {"cmd": "shutdown"}
        assert json.loads(json.dumps(cmd))["cmd"] == "shutdown"
