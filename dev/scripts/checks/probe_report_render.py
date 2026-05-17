#!/usr/bin/env python3
"""Backward-compat shim -- use `probe_report.render`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable probe-report renderer entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/probe_report/render.py

from probe_report.render import *


if __name__ == "__main__":
    raise SystemExit(main())
