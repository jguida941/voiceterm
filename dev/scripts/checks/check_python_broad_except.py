#!/usr/bin/env python3
"""Backward-compat shim -- use `python_analysis.check_python_broad_except`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable Python broad-except guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/python_analysis/check_python_broad_except.py

from python_analysis.check_python_broad_except import *


if __name__ == "__main__":
    raise SystemExit(main())
