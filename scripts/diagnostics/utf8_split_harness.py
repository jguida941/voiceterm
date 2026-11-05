#!/usr/bin/env python3
"""Run VoiceTerm with a child that splits a multibyte character across a pause
and force a HUD repaint inside the gap, then check the host screen for
replacement glyphs.

usage: utf8_split_harness.py VOICETERM_BIN [OUTDIR]
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

ROWS, COLS = 24, 80
HERE = os.path.dirname(os.path.abspath(__file__))
BIN = sys.argv[1]
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/voiceterm-captures")
os.makedirs(OUTDIR, exist_ok=True)
OUT = os.path.join(OUTDIR, "utf8split.bytes")
LOG = os.path.join(OUTDIR, "utf8split.log")
for path in (OUT, OUT + ".events", LOG):
    if os.path.exists(path):
        os.remove(path)

env = dict(os.environ, VOICETERM_LOG_PATH=LOG, VOICETERM_NO_STARTUP_BANNER="1",
           TERM="xterm-256color", TERM_PROGRAM="vscode")
for key in ("TERMINAL_EMULATOR", "CURSOR_TRACE_ID"):
    env.pop(key, None)

pid, fd = pty.fork()
if pid == 0:
    os.execve(
        "/usr/bin/env",
        ["env", "python3", os.path.join(HERE, "ptyrec.py"), OUT, BIN,
         "--backend", os.path.join(HERE, "fake_claude_utf8.sh"), "--logs"],
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


drain(4.0)
os.write(fd, b"\x07")  # Ctrl+G forces a full HUD repaint during the pause
drain(7.0)
try:
    os.write(fd, b"\x11")
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
row1 = screen.display[0].rstrip()
print("row 1 as the terminal shows it:", repr(row1))
print("replacement glyphs on row 1:", row1.count("�"))
match = re.search(rb"\xe2\x94(?!\x80)(.{0,12})", data[start:stop], re.S)
print("split signature (bytes after a dangling E2 94):", match.group(1)[:12] if match else None)
