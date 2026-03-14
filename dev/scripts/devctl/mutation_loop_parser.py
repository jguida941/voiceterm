"""Backward-compat shim -- use devctl.mutation_loop.parser instead."""
# shim-owner: tooling/mutation-loop
# shim-reason: preserve the stable root import while implementation lives under `devctl.mutation_loop.parser`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/mutation_loop/parser.py
from .mutation_loop.parser import *
