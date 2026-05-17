#!/usr/bin/env python3
"""Backward-compat shim -- use `coderabbit.ralph_ai_fix`."""
# shim-owner: tooling/coderabbit
# shim-reason: preserve the stable script entrypoint while ralph_ai_fix lives under `coderabbit/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/coderabbit/ralph_ai_fix.py

from coderabbit.ralph_ai_fix import main

if __name__ == "__main__":
    raise SystemExit(main())
