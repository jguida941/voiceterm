#!/usr/bin/env python3
"""Backward-compat shim -- use `term_consistency.command`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable probe entrypoint while term-consistency logic lives under `term_consistency/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/term_consistency/command.py

from term_consistency.command import main


if __name__ == "__main__":
    raise SystemExit(main())
