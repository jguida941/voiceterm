"""Backward-compat shim -- use `devctl.control_plane.action_support` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable root controller-action support import while implementation lives under `devctl.control_plane`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/control_plane/action_support.py

from .control_plane.action_support import *
