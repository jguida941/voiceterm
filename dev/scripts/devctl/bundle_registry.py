"""Backward-compat shim -- use devctl.bundles.registry instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable bundle-registry import while the implementation lives under `devctl.bundles`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/bundles/registry.py

from .bundles import registry as _impl

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
