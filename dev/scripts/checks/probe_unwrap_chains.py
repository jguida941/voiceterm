#!/usr/bin/env python3
"""Backward-compat shim -- use `review_probes.probe_unwrap_chains`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable unwrap-chains probe entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_probes/probe_unwrap_chains.py

from review_probes.probe_unwrap_chains import *


if __name__ == "__main__":
    raise SystemExit(main())
