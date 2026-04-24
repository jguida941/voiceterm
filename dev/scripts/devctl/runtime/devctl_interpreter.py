"""Shared helper to derive the runtime interpreter for emitted commands.

Codex finding 2026-04-24 (rev_pkt_1801 reply): six call sites previously
used ``os.path.basename(sys.executable)`` directly, which produces
``python`` (not ``python3``) for venv interpreters at paths like
``/repo/.venv/bin/python``. Rendered commands of the form
``python dev/scripts/devctl.py …`` are not runnable outside an
activated shell on most systems.

This helper guarantees the returned token always begins with
``python3``, so downstream-rendered command lines stay portable across
pyenv shims, system Python, Homebrew Python, and venvs whose binary is
named ``python``.
"""

from __future__ import annotations

import os
import sys


def devctl_interpreter() -> str:
    """Return a portable interpreter token for rendered command surfaces.

    Resolution order:
    1. ``os.path.basename(sys.executable)`` if it starts with ``python3``
       (e.g., ``python3``, ``python3.11``, ``python3.12``). Preserves the
       version suffix so the rendered command runs the same interpreter
       the live process is using — important on pyenv systems where
       bare ``python3`` resolves to a stale 3.10 with the
       ``datetime.UTC`` import gap.
    2. ``"python3"`` otherwise. Catches venv binaries (``python``),
       missing ``sys.executable``, and any future case where the basename
       does not include the major-version anchor.
    """
    basename = os.path.basename(sys.executable or "")
    if basename.startswith("python3"):
        return basename
    return "python3"
