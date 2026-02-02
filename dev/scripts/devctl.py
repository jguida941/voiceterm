#!/usr/bin/env python3
"""Entrypoint wrapper for the modular devctl package."""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from devctl.cli import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
