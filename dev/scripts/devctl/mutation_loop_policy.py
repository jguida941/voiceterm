"""Backward-compat shim -- use devctl.mutation_loop.policy instead."""
# shim-owner: tooling/mutation-loop
# shim-reason: preserve the stable root import while implementation lives under `devctl.mutation_loop.policy`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/mutation_loop/policy.py
from .mutation_loop.policy import *
