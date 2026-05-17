#!/usr/bin/env python3
"""Backward-compat shim -- use ``review_channel_bridge.command``."""
# shim-owner: tooling/review-channel
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_channel_bridge/command.py

from __future__ import annotations

from review_channel_bridge.command import main


if __name__ == "__main__":
    raise SystemExit(main())
