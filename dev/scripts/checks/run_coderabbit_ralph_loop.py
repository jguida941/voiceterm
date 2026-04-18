#!/usr/bin/env python3
"""Backward-compat shim -- use `coderabbit.run_ralph_loop`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable CodeRabbit Ralph loop entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/coderabbit/run_ralph_loop.py

from coderabbit.run_ralph_loop import *


if __name__ == "__main__":
    raise SystemExit(main())
