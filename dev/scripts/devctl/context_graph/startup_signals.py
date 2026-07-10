"""Compatibility shim for the canonical startup-signal loader."""

from __future__ import annotations

from ..runtime.startup_signals import (
    load_startup_quality_signals,
    load_startup_quality_signals as load_bootstrap_quality_signals,
)

__all__ = ["load_bootstrap_quality_signals", "load_startup_quality_signals"]
