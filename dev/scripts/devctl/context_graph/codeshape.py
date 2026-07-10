"""Public facade for bounded codeshape ingestion."""

from __future__ import annotations

from ._codeshape_models import CodeShapeGraph
from ._codeshape_scan import DEFAULT_CODESHAPE_SCOPE_PATHS, build_codeshape_subgraph

__all__ = [
    "CodeShapeGraph",
    "DEFAULT_CODESHAPE_SCOPE_PATHS",
    "build_codeshape_subgraph",
]
