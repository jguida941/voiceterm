"""Thin parser wrapper for `devctl receipt-steward` (A38.2 S2)."""

from __future__ import annotations

from ..commands.receipt_steward import add_parser as _command_add_parser


def add_receipt_steward_parser(sub) -> None:
    """Register the `receipt-steward` subcommand on the top-level parser."""
    _command_add_parser(sub)


__all__ = ["add_receipt_steward_parser"]
