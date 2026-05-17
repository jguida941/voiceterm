#!/usr/bin/env python3
"""Backward-compat shim -- use `python_analysis.check_python_design_complexity`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable Python design-complexity guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/python_analysis/check_python_design_complexity.py

from python_analysis.check_python_design_complexity import *


if __name__ == "__main__":
    raise SystemExit(main())
