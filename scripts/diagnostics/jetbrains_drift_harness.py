#!/usr/bin/env python3
"""Run VoiceTerm under a simulated JetBrains terminal with a child that streams
more lines than its viewport holds, then report where the HUD and the child's
lines ended up on the host screen.

usage: jetbrains_drift_harness.py VOICETERM_BIN [OUTDIR]
Needs the pyte package: pip install pyte
"""
import fcntl
import os
import pty
import re
import select
import signal
import struct
import sys
import termios
import time

import pyte

ROWS, COLS = 32, 100
HERE = os.path.dirname(os.path.abspath(__file__))
BIN = sys.argv[1]
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/voiceterm-captures")
os.makedirs(OUTDIR, exist_ok=True)
OUT = os.path.join(OUTDIR, "jbdrift.bytes")
LOG = os.path.join(OUTDIR, "jbdrift.log")
for path in (OUT, OUT + ".events", LOG):
    if os.path.exists(path):
        os.remove(path)

env = dict(
    os.environ,
    VOICETERM_LOG_PATH=LOG,
    VOICETERM_DEBUG_CLAUDE_HUD="1",
    VOICETERM_NO_STARTUP_BANNER="1",
    TERM="xterm-256color",
    TERMINAL_EMULATOR="JetBrains-JediTerm",
    VOICETERM_BACKEND_LABEL="claude",
)
for key in ("TERM_PROGRAM", "CURSOR_TRACE_ID"):
    env.pop(key, None)

pid, fd = pty.fork()
if pid == 0:
    os.execve(
        "/usr/bin/env",
        ["env", "python3", os.path.join(HERE, "ptyrec.py"), OUT, BIN,
         "--backend", os.path.join(HERE, "fake_claude_lines.sh"), "--logs"],
        env,
    )
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))


def drain(seconds):
    end = time.time() + seconds
    while time.time() < end:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            try:
                os.read(fd, 65536)
            except OSError:
                return


drain(9.0)
try:
    os.write(fd, b"\x11")  # Ctrl+Q quits VoiceTerm
    drain(2.0)
except OSError:
    pass
try:
    os.kill(pid, signal.SIGTERM)
except ProcessLookupError:
    pass
try:
    os.waitpid(pid, 0)
except ChildProcessError:
    pass

data = open(OUT, "rb").read()
start = max(data.find(b"\x1b[2J\x1b[3J\x1b[H"), 0)
stop = data.rfind(b"\x1b[=0;1u")
stop = stop if stop > start else len(data)
screen = pyte.Screen(COLS, ROWS)
pyte.ByteStream(screen).feed(data[start:stop])
pty_rows = None
for line in open(LOG):
    match = re.search(r"pty_rows=(\d+)", line)
    if match:
        pty_rows = int(match.group(1))
hud = [i + 1 for i, row in enumerate(screen.display) if "PTT" in row or "AUTO" in row]
child = [i + 1 for i, row in enumerate(screen.display) if "answer line" in row]
print("child viewport rows:", pty_rows, "| host rows:", ROWS)
print("rows holding HUD text:", hud)
print("rows holding child lines:", child[:3], "...", child[-3:],
      "| child rows beyond its viewport:", [r for r in child if pty_rows and r > pty_rows])
print("=== final screen ===")
for i, row in enumerate(screen.display, start=1):
    if row.strip():
        print(f"{i:2d}| {row.rstrip()[:70]}")
