"""Backward-compat shim -- use `devctl.review_channel.prompt`."""
# shim-owner: tooling/review-channel
# shim-reason: preserve the stable import path while review-channel prompt lives under `devctl.review_channel`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/review_channel/prompt.py

from .review_channel.prompt import *  # noqa: F401,F403
