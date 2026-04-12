#!/usr/bin/env python3
"""Backward-compat shim -- use `review_probes.probe_vague_errors`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable vague-errors probe entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_probes/probe_vague_errors.py

try:
    from .review_probes import probe_vague_errors as _impl
except ImportError:
    from review_probes import probe_vague_errors as _impl

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
