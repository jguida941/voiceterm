"""Backward-compat shim -- use `probe_support.bootstrap`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable probe bootstrap import surface while shared probe helpers live under `probe_support/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/probe_support/bootstrap.py

from probe_support.bootstrap import *
