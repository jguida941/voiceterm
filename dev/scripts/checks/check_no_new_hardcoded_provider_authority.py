#!/usr/bin/env python3
"""Stable entrypoint for the Phase 0.6.C provider-hardcode guard."""

from __future__ import annotations

import sys

from topology_hardcode.command import build_report, main


if __name__ == "__main__":
    raise SystemExit(main(["--mode", "provider", *sys.argv[1:]]))
