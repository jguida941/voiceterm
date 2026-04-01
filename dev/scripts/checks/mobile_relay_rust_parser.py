"""Backward-compat shim -- use `rust_analysis.mobile_relay_rust_parser`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable mobile-relay Rust parser import surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/rust_analysis/mobile_relay_rust_parser.py

from rust_analysis.mobile_relay_rust_parser import *
