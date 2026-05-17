#!/usr/bin/env python3
"""Backward-compat shim for the repo-portability substrate guard."""

from __future__ import annotations

from repo_portability.command import main


if __name__ == "__main__":
    raise SystemExit(main())
