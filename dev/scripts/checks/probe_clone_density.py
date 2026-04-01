#!/usr/bin/env python3
"""Backward-compat shim -- use `review_probes.probe_clone_density`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable clone-density probe entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_probes/probe_clone_density.py

from review_probes.probe_clone_density import *


if __name__ == "__main__":
    raise SystemExit(main())
