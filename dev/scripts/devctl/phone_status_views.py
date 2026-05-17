"""Backward-compat shim -- use `devctl.mobile.phone_views` instead."""
# shim-owner: tooling/mobile
# shim-reason: preserve the stable root phone-status view import while implementation lives under `devctl.mobile`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/mobile/phone_views.py

from .mobile.phone_views import *
