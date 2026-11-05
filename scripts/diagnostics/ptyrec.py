#!/usr/bin/env python3
"""Record everything a terminal program writes, while forwarding window resizes.
Usage: python3 ptyrec.py OUTPUT.bytes COMMAND [ARGS...]
Writes OUTPUT.bytes (raw output) and OUTPUT.bytes.events (resize events with byte offsets)."""
import os, sys, pty, tty, termios, fcntl, struct, signal, select, time
out_path, cmd = sys.argv[1], sys.argv[2:]
stdin_fd = sys.stdin.fileno()
def winsize(fd):
    return struct.unpack("HHHH", fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\0" * 8))
def write_all(fd, data):
    while data:
        n = os.write(fd, data); data = data[n:]
pid, master = pty.fork()
if pid == 0:
    os.execvp(cmd[0], cmd)
try:
    ws = winsize(stdin_fd)
except OSError:
    ws = (24, 80, 0, 0)
fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", *ws))
events = open(out_path + ".events", "w"); rec = open(out_path, "wb"); written = 0
def log(kind, extra=""):
    events.write(f"{time.time():.3f} offset={written} {kind} {extra}\n"); events.flush()
log("start", f"rows={ws[0]} cols={ws[1]} cmd={' '.join(cmd)}")
def on_winch(signum, frame):
    try:
        ws = winsize(stdin_fd)
        fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", *ws))
        os.kill(pid, signal.SIGWINCH)
        log("resize", f"rows={ws[0]} cols={ws[1]}")
    except OSError as exc:
        log("resize-error", str(exc))
signal.signal(signal.SIGWINCH, on_winch)
old = termios.tcgetattr(stdin_fd); tty.setraw(stdin_fd)
try:
    while True:
        r, _, _ = select.select([stdin_fd, master], [], [])
        if master in r:
            try:
                data = os.read(master, 65536)
            except OSError:
                break
            if not data:
                break
            write_all(1, data); rec.write(data); rec.flush(); written += len(data)
        if stdin_fd in r:
            data = os.read(stdin_fd, 65536)
            if not data:
                break
            write_all(master, data)
finally:
    termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old)
    log("end"); rec.close(); events.close()
    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass
