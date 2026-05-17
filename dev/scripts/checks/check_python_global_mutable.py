#!/usr/bin/env python3
"""Backward-compat shim -- use `python_analysis.check_python_global_mutable`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable Python global-mutable guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/python_analysis/check_python_global_mutable.py

from python_analysis.check_python_global_mutable import *


if __name__ == "__main__":
    raise SystemExit(main())
