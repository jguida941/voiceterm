#!/usr/bin/env python3
"""Package-owned entrypoint for generated instruction/starter surface sync."""

from __future__ import annotations

if __package__:
    from .instruction_surface_sync import main
else:  # pragma: no cover - standalone script fallback
    from instruction_surface_sync import main


if __name__ == "__main__":
    raise SystemExit(main())
