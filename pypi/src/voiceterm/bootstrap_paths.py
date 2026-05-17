"""Filesystem helpers for the launcher bootstrap flow."""

from __future__ import annotations

import os
from pathlib import Path


def _native_root() -> Path:
    configured = os.environ.get("VOICETERM_PY_NATIVE_ROOT")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".local" / "share" / "voiceterm" / "native"


def _native_bin() -> Path:
    configured = os.environ.get("VOICETERM_NATIVE_BIN")
    if configured:
        return Path(configured).expanduser()
    return _native_root() / "bin" / "voiceterm"
