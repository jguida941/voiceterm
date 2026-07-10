#!/usr/bin/env python3
"""Backward-compat shim -- use `rust_analysis.check_rust_compiler_warnings`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable Rust compiler-warnings guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/rust_analysis/check_rust_compiler_warnings.py

from rust_analysis.check_rust_compiler_warnings import *


if __name__ == "__main__":
    raise SystemExit(main())
