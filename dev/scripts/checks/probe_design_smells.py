#!/usr/bin/env python3
"""Backward-compat shim -- use `review_probes.probe_design_smells`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable design-smells probe entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_probes/probe_design_smells.py

from review_probes.probe_design_smells import *


if __name__ == "__main__":
    raise SystemExit(main())
