#!/usr/bin/env bash
# End-to-end smoke test for the VoiceTerm daemon's Unix-socket protocol.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUST_BINARY="$PROJECT_ROOT/rust/target/release/voiceterm"
TEST_DIR="$(mktemp -d "${TMPDIR:-/tmp}/voiceterm-integration.XXXXXX")"
SOCKET_PATH="$TEST_DIR/control.sock"
DAEMON_LOG="$TEST_DIR/daemon.log"
DAEMON_PID=""

cleanup() {
    if [ -n "$DAEMON_PID" ] && kill -0 "$DAEMON_PID" 2>/dev/null; then
        kill "$DAEMON_PID" 2>/dev/null || true
        wait "$DAEMON_PID" 2>/dev/null || true
    fi
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

if [ ! -x "$RUST_BINARY" ]; then
    echo "VoiceTerm release binary not found: $RUST_BINARY" >&2
    echo "Run: make build" >&2
    exit 1
fi

"$RUST_BINARY" --daemon --no-ws --socket-path "$SOCKET_PATH" \
    >"$DAEMON_LOG" 2>&1 &
DAEMON_PID=$!

for _ in $(seq 1 100); do
    if [ -S "$SOCKET_PATH" ]; then
        break
    fi
    if ! kill -0 "$DAEMON_PID" 2>/dev/null; then
        echo "VoiceTerm daemon exited before creating its socket" >&2
        sed -n '1,120p' "$DAEMON_LOG" >&2
        exit 1
    fi
    sleep 0.05
done

if [ ! -S "$SOCKET_PATH" ]; then
    echo "VoiceTerm daemon did not create its socket" >&2
    sed -n '1,120p' "$DAEMON_LOG" >&2
    exit 1
fi

python3 - "$SOCKET_PATH" <<'PY'
import json
import socket
import sys

socket_path = sys.argv[1]
client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.settimeout(5)
client.connect(socket_path)
stream = client.makefile("rwb", buffering=0)


def read_until(event_name: str) -> dict:
    for _ in range(20):
        raw = stream.readline()
        if not raw:
            raise AssertionError(f"connection closed before {event_name}")
        event = json.loads(raw)
        if event.get("event") == event_name:
            return event
    raise AssertionError(f"did not receive {event_name}")


ready = read_until("daemon_ready")
assert ready["version"]
assert ready["socket_path"] == socket_path
assert ready["lifecycle"] == "running"

stream.write(b'{"cmd":"get_status"}\n')
status = read_until("daemon_status")
assert status["active_agents"] == 0
assert status["socket_path"] == socket_path

stream.write(b'{"cmd":"list_agents"}\n')
agents = read_until("agent_list")
assert agents["agents"] == []

stream.write(b'{"cmd":"shutdown"}\n')
read_until("daemon_shutdown")
client.close()

print(f"VoiceTerm daemon integration OK (v{ready['version']})")
PY

wait "$DAEMON_PID"
DAEMON_PID=""
