#!/usr/bin/env python3
"""Backward-compat shim -- use ``packet_pkt_bind_completeness.command``."""
# shim-owner: tooling/governance
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/packet_pkt_bind_completeness/command.py

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packet_pkt_bind_completeness.command import main


if __name__ == "__main__":
    raise SystemExit(main())
