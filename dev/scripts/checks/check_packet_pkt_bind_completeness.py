#!/usr/bin/env python3
"""Backward-compat shim -- use ``packet_pkt_bind_completeness.command``."""
# shim-owner: tooling/governance
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/packet_pkt_bind_completeness/command.py

from packet_pkt_bind_completeness.command import main


if __name__ == "__main__":
    raise SystemExit(main())
