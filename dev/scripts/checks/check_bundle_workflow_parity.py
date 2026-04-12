#!/usr/bin/env python3
"""Backward-compat shim -- use `bundle_workflow_parity.command`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable bundle-workflow parity guard entrypoint while implementation lives under `bundle_workflow_parity/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/bundle_workflow_parity/command.py

from __future__ import annotations

import inspect

try:
    from .bundle_workflow_parity import command as _impl
    from .bundle_workflow_parity import sequences as _sequences
except ImportError:
    from bundle_workflow_parity import command as _impl
    from bundle_workflow_parity import sequences as _sequences

_SHIM_EXCLUDED_NAMES = {
    "__builtins__",
    "__cached__",
    "__file__",
    "__loader__",
    "__name__",
    "__package__",
    "__spec__",
}


def _apply_shim_overrides() -> list[tuple[object, str, object]]:
    overrides: list[tuple[object, str, object]] = []
    for _name, _value in globals().items():
        if _name.startswith("__") or _name in _SHIM_EXCLUDED_NAMES:
            continue
        if getattr(_value, "__shim_proxy__", False):
            continue
        if hasattr(_impl, _name):
            overrides.append((_impl, _name, getattr(_impl, _name)))
            setattr(_impl, _name, _value)
    return overrides


def _restore_overrides(overrides: list[tuple[object, str, object]]) -> None:
    for _module, _name, _value in reversed(overrides):
        setattr(_module, _name, _value)


def _proxy(name: str):
    target = getattr(_impl, name)

    def _wrapped(*args, **kwargs):
        overrides = _apply_shim_overrides()
        try:
            return getattr(_impl, name)(*args, **kwargs)
        finally:
            _restore_overrides(overrides)

    _wrapped.__name__ = getattr(target, "__name__", name)
    _wrapped.__doc__ = getattr(target, "__doc__", None)
    _wrapped.__shim_proxy__ = True
    return _wrapped


for _name, _value in vars(_impl).items():
    if _name in _SHIM_EXCLUDED_NAMES:
        continue
    globals()[_name] = _value
    if inspect.isfunction(_value):
        globals()[_name] = _proxy(_name)
for _name, _value in vars(_sequences).items():
    if _name in _SHIM_EXCLUDED_NAMES or _name in globals():
        continue
    globals()[_name] = _value


if __name__ == "__main__":
    raise SystemExit(main())
