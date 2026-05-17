"""Session-related surface contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


def session_orientation_contracts() -> tuple[ContractSpec, ...]:
    """Return contract rows for fresh-session orientation surfaces."""
    return (
        ContractSpec(
            contract_id="SessionOrientationPacket",
            owner_layer="governance_commands",
            purpose=(
                "Fresh-session reducer that runs startup-context, "
                "session-resume, review-channel status, and context-graph "
                "before choosing the next typed action."
            ),
            required_fields=(
                ContractField("role", "str", "Caller role used for typed routing."),
                ContractField(
                    "generated_at_utc",
                    "str",
                    "UTC timestamp for packet generation.",
                ),
                ContractField("branch", "str", "Current git branch."),
                ContractField("head_sha", "str", "Current HEAD commit SHA."),
                ContractField(
                    "steps",
                    "tuple[SessionOrientationStep, ...]",
                    "Ordered command executions with exit codes and parse status.",
                ),
                ContractField(
                    "startup",
                    "dict[str, object]",
                    "Reduced StartupContext fields.",
                ),
                ContractField(
                    "session_resume",
                    "dict[str, object]",
                    "Reduced SessionCachePacket fields from session-resume.",
                ),
                ContractField(
                    "review_status",
                    "dict[str, object]",
                    "Reduced review-channel status and authority fields.",
                ),
                ContractField(
                    "context_graph",
                    "dict[str, object]",
                    "Reduced ContextGraph bootstrap snapshot fields.",
                ),
                ContractField(
                    "final",
                    "dict[str, object]",
                    "Reduced next-action decision from AuthoritySnapshot.",
                ),
            ),
            runtime_model=(
                "dev.scripts.devctl.commands.governance.session_orientation:"
                "SessionOrientationPacket"
            ),
            startup_surface_tokens=(
                "required_action",
                "next_command",
                "packet_target",
                "context_graph",
            ),
        ),
    )

