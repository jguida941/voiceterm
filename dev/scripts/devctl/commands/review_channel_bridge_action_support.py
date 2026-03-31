"""Backward-compat shim -- use devctl.commands.review_channel.bridge_action_support instead."""
# shim-owner: tooling/review-channel
# shim-reason: preserve the stable bridge-action-support import while the implementation lives under `devctl.commands.review_channel`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/review_channel/bridge_action_support.py

from .review_channel.bridge_action_support import *
