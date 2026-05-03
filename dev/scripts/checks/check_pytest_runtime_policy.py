#!/usr/bin/env python3
"""Backward-compat shim -- use checks.pytest_runtime_policy.command instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable pytest runtime-policy guard entrypoint while the implementation lives under `checks/pytest_runtime_policy`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/checks/pytest_runtime_policy/command.py

from pytest_runtime_policy.command import *


if __name__ == "__main__":
    raise SystemExit(main())
