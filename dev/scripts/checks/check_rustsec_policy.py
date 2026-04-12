#!/usr/bin/env python3
"""Backward-compat shim -- use `rust_analysis.check_rustsec_policy`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable RustSec policy guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/rust_analysis/check_rustsec_policy.py

try:
    from .rust_analysis import check_rustsec_policy as _impl
except ImportError:
    from rust_analysis import check_rustsec_policy as _impl

for _name, _value in vars(_impl).items():
    if _name in {
        "__builtins__",
        "__cached__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__spec__",
    }:
        continue
    globals()[_name] = _value


if __name__ == "__main__":
    raise SystemExit(main())
