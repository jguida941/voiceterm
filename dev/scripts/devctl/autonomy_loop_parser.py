"""Backward-compat shim -- use `devctl.autonomy.loop_parser`."""
# shim-owner: tooling/autonomy
# shim-reason: preserve the stable import path while autonomy loop parser lives under `devctl.autonomy`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/autonomy/loop_parser.py

from .autonomy.loop_parser import *  # noqa: F401,F403
