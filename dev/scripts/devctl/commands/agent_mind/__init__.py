"""Public surface for the ``agent-mind`` devctl command.

Re-exports the small entry-point helpers consumed by ``cli.py``, the
CLI parser module, and the test suite. The implementation is split
across sibling modules (command, slice_builder, projection, renderers)
so each stays under the code-shape soft limit and is separated by
concern: discovery/run vs pure transforms vs pure rendering.
"""

from __future__ import annotations

from .command import SUPPORTED_AGENTS, run
from .projection import resolve_projection_path, write_projection
from .renderers import render_json, render_markdown, render_terminal
from .slice_builder import SliceRequest, build_slice

__all__ = [
    "SUPPORTED_AGENTS",
    "SliceRequest",
    "build_slice",
    "render_json",
    "render_markdown",
    "render_terminal",
    "resolve_projection_path",
    "run",
    "write_projection",
]
