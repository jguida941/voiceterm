#!/usr/bin/env python3
"""Backward-compat shim -- use `rust_analysis.check_rust_audit_patterns`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable Rust audit-patterns guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/rust_analysis/check_rust_audit_patterns.py

from rust_analysis.check_rust_audit_patterns import *


if __name__ == "__main__":
    raise SystemExit(main())
