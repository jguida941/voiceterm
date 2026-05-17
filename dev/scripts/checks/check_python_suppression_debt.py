#!/usr/bin/env python3
"""Backward-compat shim -- use `python_analysis.check_python_suppression_debt`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable Python suppression-debt guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/python_analysis/check_python_suppression_debt.py

from python_analysis.check_python_suppression_debt import *


if __name__ == "__main__":
    raise SystemExit(main())
