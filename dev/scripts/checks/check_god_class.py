#!/usr/bin/env python3
"""Backward-compat shim -- use `code_shape.check_god_class`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable god-class guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/code_shape/check_god_class.py

from code_shape.check_god_class import *


if __name__ == "__main__":
    raise SystemExit(main())
