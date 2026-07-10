"""Typed seam guard package."""

from .scanner import ObjectGetattrFinding, parse_object_getattr_hits, scan_object_param_getattr_functions

__all__ = [
    "ObjectGetattrFinding",
    "parse_object_getattr_hits",
    "scan_object_param_getattr_functions",
]
