#!/usr/bin/env python3
"""Backward-compat shim -- use ``review_probes.probe_packet_carry_forward_debt``."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable packet carry-forward debt probe entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_probes/probe_packet_carry_forward_debt.py

from review_probes.probe_packet_carry_forward_debt import *


if __name__ == "__main__":
    raise SystemExit(main())
