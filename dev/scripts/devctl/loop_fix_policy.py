"""Backward-compat shim -- use devctl.loops.fix_policy instead."""
# shim-owner: tooling/loops
# shim-reason: preserve the stable root import while implementation lives under `devctl.loops.fix_policy`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/loops/fix_policy.py
from .loops.fix_policy import *
