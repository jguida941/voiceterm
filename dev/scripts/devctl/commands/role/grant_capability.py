"""`devctl role grant-capability` — typed capability grant to a role.

Stub for Phase 0.5 MVP. Full implementation (issuing typed
`CapabilityGrantState` rows + persisting to
`dev/state/role_capability_grants.jsonl` + emitting a typed receipt)
lands in a follow-up slice once the create handler is fully dogfooded.
"""

from __future__ import annotations

from typing import Any

from ...common import add_standard_output_arguments


def add_grant_capability_parser(sub) -> None:
    parser = sub.add_parser(
        "grant-capability",
        help="Grant a typed capability to a typed role (stub).",
    )
    parser.add_argument("--role-id", required=True, help="Typed role id to grant capability to.")
    parser.add_argument("--capability", required=True, help="Typed capability id to grant.")
    add_standard_output_arguments(parser, format_choices=("json", "md"), default_format="md")


def run_grant_capability(args: Any) -> tuple[dict[str, object], int]:
    """Stub for Phase 0.5 MVP. Returns not-implemented signal."""
    return (
        {
            "ok": False,
            "action": "grant-capability",
            "role_id": getattr(args, "role_id", ""),
            "capability": getattr(args, "capability", ""),
            "errors": ["not_implemented_in_phase_0_5_mvp_grant_capability_stub"],
        },
        1,
    )


__all__ = ["add_grant_capability_parser", "run_grant_capability"]
