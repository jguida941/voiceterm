"""Backward-compat shim -- use devctl.loops.comment instead."""
# shim-owner: tooling/loops
# shim-reason: preserve the stable root import while implementation lives under `devctl.loops.comment`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/loops/comment.py
from .loops.comment import *
