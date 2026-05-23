"""Thin parser wrapper for `devctl role` (registers the subcommand)."""

from __future__ import annotations

from ..commands.role import add_parser as _command_add_parser


def add_role_parser(sub) -> None:
    """Register the `role` subcommand on the top-level parser."""
    _command_add_parser(sub)


__all__ = ["add_role_parser"]
