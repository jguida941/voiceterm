"""Backward-compat shim -- use devctl.loops.packet_parser instead."""
# shim-owner: tooling/loops
# shim-reason: preserve the stable root import while implementation lives under `devctl.loops.packet_parser`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/loops/packet_parser.py
from .loops.packet_parser import *
