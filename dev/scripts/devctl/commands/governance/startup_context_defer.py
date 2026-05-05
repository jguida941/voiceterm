"""Startup-context publication deferral options."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StartupRoutingOptions:
    """Action-routing options for a startup-context invocation."""

    caller_role: str | None = None
    reviewer_override: bool = False
    defer_publication: bool = False


def defer_publication_requested(args) -> bool:
    if bool(getattr(args, "defer_publication", False)):
        return True
    return os.environ.get("DEVCTL_DEFER_PUBLICATION") == "1"


__all__ = ["StartupRoutingOptions", "defer_publication_requested"]
