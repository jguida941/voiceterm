"""`devctl role list` — read-only enumeration of typed roles.

Per A37 Phase 0.5 scope: stub returns the typed role-id roster from
``DEFAULT_ROLE_IDS`` plus any persisted `CustomRoleDefinition` rows
under the typed state path. Full implementation (joining typed
metadata, capability summaries, and source store) lands in a follow-up
slice.
"""

from __future__ import annotations

from typing import Any

from ...common import add_standard_output_arguments
from ...runtime.role_profile import DEFAULT_ROLE_IDS


def add_list_parser(sub) -> None:
    parser = sub.add_parser("list", help="List typed role ids (stub).")
    parser.add_argument(
        "--include-deprecated",
        action="store_true",
        default=False,
        help="Include deprecated aliases (currently a no-op stub).",
    )
    add_standard_output_arguments(parser, format_choices=("json", "md"), default_format="md")


def run_list(args: Any) -> tuple[dict[str, object], int]:
    """Return the typed-role roster as a flat list. Stub for Phase 0.5 MVP."""
    return (
        {
            "ok": True,
            "action": "list",
            "default_role_ids": list(DEFAULT_ROLE_IDS),
        },
        0,
    )


__all__ = ["add_list_parser", "run_list"]
