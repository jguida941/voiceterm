"""Async client for the VoiceTerm daemon Unix socket.

Replaces file-based polling with a live connection so the Operator Console
(and any Python tool) receives real-time agent output, spawn confirmations,
and status updates from the daemon hub.

Protocol: JSON-lines over Unix domain socket.
- Client sends: ``DaemonCommand`` objects (one JSON object per line)
- Client receives: ``DaemonEvent`` objects (one JSON object per line)

Usage::

    client = DaemonClient()
    await client.connect()
    await client.spawn_agent("claude", label="reviewer-1")
    async for event in client.events():
        print(event)
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Callable


DEFAULT_SOCKET_PATH = Path.home() / ".voiceterm" / "control.sock"


@dataclass
class DaemonEvent:
    """Parsed daemon event with its raw JSON payload."""

    event_type: str
    payload: dict[str, Any]

    @classmethod
    def from_json(cls, line: str) -> "DaemonEvent":
        data = json.loads(line)
        return cls(event_type=data.get("event", "unknown"), payload=data)

    @property
    def session_id(self) -> str | None:
        return self.payload.get("session_id")

    @property
    def text(self) -> str | None:
        return self.payload.get("text")

    def is_output(self) -> bool:
        return self.event_type == "agent_output"

    def is_error(self) -> bool:
        return self.event_type == "error"


@dataclass
class DaemonClient:
    """Async client for the VoiceTerm daemon Unix domain socket.

    Designed for integration into PyQt6's event loop via ``asyncio``.
    """

    socket_path: Path = field(default_factory=lambda: DEFAULT_SOCKET_PATH)
    _reader: asyncio.StreamReader | None = field(default=None, repr=False)
    _writer: asyncio.StreamWriter | None = field(default=None, repr=False)
    _connected: bool = field(default=False, repr=False)
    _event_callbacks: list[Callable[[DaemonEvent], None]] = field(
        default_factory=list, repr=False
    )

    async def connect(self) -> None:
        """Open a connection to the daemon's Unix socket."""
        if self._connected:
            return
        self._reader, self._writer = await asyncio.open_unix_connection(
            str(self.socket_path)
        )
        self._connected = True

    async def disconnect(self) -> None:
        """Close the connection."""
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
        self._connected = False
        self._reader = None
        self._writer = None

    @property
    def connected(self) -> bool:
        return self._connected

    async def _send_command(self, cmd: dict[str, Any]) -> None:
        """Send a JSON-lines command to the daemon."""
        if self._writer is None:
            raise ConnectionError("not connected to daemon")
        line = json.dumps(cmd, separators=(",", ":")) + "\n"
        self._writer.write(line.encode())
        await self._writer.drain()

    async def spawn_agent(
        self,
        provider: str,
        *,
        working_dir: str | None = None,
        label: str | None = None,
        initial_prompt: str | None = None,
    ) -> None:
        """Request the daemon to spawn a new agent PTY session."""
        cmd: dict[str, Any] = {"cmd": "spawn_agent", "provider": provider}
        if working_dir is not None:
            cmd["working_dir"] = working_dir
        if label is not None:
            cmd["label"] = label
        if initial_prompt is not None:
            cmd["initial_prompt"] = initial_prompt
        await self._send_command(cmd)

    async def send_to_agent(self, session_id: str, text: str) -> None:
        """Send text to a running agent's PTY input."""
        await self._send_command(
            {"cmd": "send_to_agent", "session_id": session_id, "text": text}
        )

    async def kill_agent(self, session_id: str) -> None:
        """Request graceful shutdown of an agent session."""
        await self._send_command(
            {"cmd": "kill_agent", "session_id": session_id}
        )

    async def list_agents(self) -> None:
        """Request a list of all active agent sessions."""
        await self._send_command({"cmd": "list_agents"})

    async def get_status(self) -> None:
        """Request a daemon status snapshot."""
        await self._send_command({"cmd": "get_status"})

    async def shutdown(self) -> None:
        """Request graceful daemon shutdown."""
        await self._send_command({"cmd": "shutdown"})

    def on_event(self, callback: Callable[[DaemonEvent], None]) -> None:
        """Register a callback for incoming daemon events."""
        self._event_callbacks.append(callback)

    async def events(self) -> AsyncIterator[DaemonEvent]:
        """Yield parsed daemon events as they arrive.

        This is an infinite async generator — use it in an ``async for``
        loop or a background task. Stops when the connection is closed.
        """
        if self._reader is None:
            raise ConnectionError("not connected to daemon")
        while True:
            line_bytes = await self._reader.readline()
            if not line_bytes:
                self._connected = False
                return
            line = line_bytes.decode().strip()
            if not line:
                continue
            event = DaemonEvent.from_json(line)
            for cb in self._event_callbacks:
                cb(event)
            yield event

    async def read_one_event(self) -> DaemonEvent | None:
        """Read a single event from the daemon. Returns None on disconnect."""
        if self._reader is None:
            raise ConnectionError("not connected to daemon")
        line_bytes = await self._reader.readline()
        if not line_bytes:
            self._connected = False
            return None
        line = line_bytes.decode().strip()
        if not line:
            return await self.read_one_event()
        return DaemonEvent.from_json(line)
