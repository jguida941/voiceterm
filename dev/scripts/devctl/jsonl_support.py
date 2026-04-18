"""Backward-compat shim -- use `devctl.runtime.jsonl_support` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable root JSONL support import while implementation lives under `devctl.runtime`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/runtime/jsonl_support.py

from .runtime.jsonl_support import *
