"""`devctl role show` — read-only deep view of one typed role.

Stub for Phase 0.5 MVP. Full implementation (joining persisted
`CustomRoleDefinition` rows, instruction cards, guards, and capability
grants) lands in a follow-up slice.
"""

from __future__ import annotations

from typing import Any

from ...common import add_standard_output_arguments
from ...runtime.role_profile import _ROLE_CAPABILITY_CLASSES, normalize_role_id


def add_show_parser(sub) -> None:
    parser = sub.add_parser("show", help="Show a typed role (stub).")
    parser.add_argument(
        "--role-id",
        required=True,
        help="Typed role id to show.",
    )
    add_standard_output_arguments(parser, format_choices=("json", "md"), default_format="md")


def run_show(args: Any) -> tuple[dict[str, object], int]:
    """Return the typed-role roster row for one id. Stub for Phase 0.5 MVP."""
    role_id = normalize_role_id(getattr(args, "role_id", ""))
    capability = _ROLE_CAPABILITY_CLASSES.get(role_id)
    if capability is None:
        return (
            {
                "ok": False,
                "action": "show",
                "role_id": role_id,
                "errors": [f"role_id_not_found:{role_id!r}"],
            },
            1,
        )
    return (
        {
            "ok": True,
            "action": "show",
            "role_id": role_id,
            "capability_classes": [str(c) for c in capability],
        },
        0,
    )


__all__ = ["add_show_parser", "run_show"]
