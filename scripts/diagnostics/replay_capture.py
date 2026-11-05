#!/usr/bin/env python3
"""Replay a ptyrec capture through a terminal emulator and show what the host saw.

usage:
  replay_capture.py replay CAPTURE.bytes
      the screen just before each resize and at the end
  replay_capture.py trace CAPTURE.bytes [--marker TEXT]
      every point where the rows holding TEXT (default "PTT", the HUD) changed,
      cut at synchronized-output and resize boundaries
Needs the pyte package: pip install pyte
"""
import argparse
import re

import pyte


def load(path):
    data = open(path, "rb").read()
    events = [line.split() for line in open(path + ".events")]

    def field(event, key):
        for token in event:
            if token.startswith(key + "="):
                return int(token.split("=", 1)[1])
        return None

    start = next(e for e in events if e[2] == "start")
    resizes = {
        field(e, "offset"): (field(e, "rows"), field(e, "cols"))
        for e in events
        if e[2] == "resize"
    }
    return data, field(start, "rows"), field(start, "cols"), resizes


def show(screen, label):
    print(f"\n===== {label}: {screen.lines} rows =====")
    for i, row in enumerate(screen.display, start=1):
        text = row.rstrip()
        if text:
            print(f"{i:2d}| {text[:100]}")


def cmd_replay(args):
    data, rows, cols, resizes = load(args.capture)
    screen = pyte.Screen(cols, rows)
    stream = pyte.ByteStream(screen)
    pos = 0
    for offset in sorted(resizes):
        stream.feed(data[pos:offset])
        rows, cols = resizes[offset]
        show(screen, f"just before resize to {rows}x{cols}")
        screen.resize(rows, cols)
        pos = offset
    stream.feed(data[pos:])
    show(screen, "final")


def cmd_trace(args):
    data, rows, cols, resizes = load(args.capture)
    screen = pyte.Screen(cols, rows)
    stream = pyte.ByteStream(screen)

    def marked_rows():
        return [i + 1 for i, row in enumerate(screen.display) if args.marker in row]

    cuts = sorted(
        {m.start() for m in re.finditer(rb"\x1b\[\?2026[hl]", data)}
        | set(resizes)
        | {len(data)}
    )
    pos = 0
    prev = marked_rows()
    for cut in cuts:
        if cut <= pos:
            continue
        if pos in resizes:
            screen.resize(*resizes[pos])
        stream.feed(data[pos:cut])
        now = marked_rows()
        if now != prev:
            seg = data[pos:cut]
            cups = [int(r) for r, _ in re.findall(rb"\x1b\[(\d+);(\d+)H", seg)]
            print(
                f"bytes {pos}-{cut}: rows with {args.marker!r} {prev} -> {now}"
                f" | screen {screen.lines} rows | CUP rows {cups[:8]}"
                f" | LF {seg.count(b'\n')} | cursor row {screen.cursor.y + 1}"
            )
            prev = now
        pos = cut
    print("final rows with marker:", prev)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    replay = sub.add_parser("replay")
    replay.add_argument("capture")
    replay.set_defaults(run=cmd_replay)
    trace = sub.add_parser("trace")
    trace.add_argument("capture")
    trace.add_argument("--marker", default="PTT")
    trace.set_defaults(run=cmd_trace)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
