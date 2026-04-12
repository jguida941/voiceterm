"""Backward-compat shim -- use `review_probes.probe_path_filters`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable review-probe path-filter helper surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_probes/probe_path_filters.py

try:
    from .review_probes import probe_path_filters as _impl
except ImportError:
    from review_probes import probe_path_filters as _impl

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
