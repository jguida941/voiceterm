"""Identity helpers for session-resume continuation state."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...runtime.conductor_capability import session_resume_command_for_role

if TYPE_CHECKING:
    from ...runtime.authority_snapshot import AuthoritySnapshot

ROLE_AGENT_DEFAULTS = {
    "implementer": "claude",
    "reviewer": "codex",
    "observer": "operator",
    "dashboard": "operator",
}


def agent_id_for_role(
    *,
    role: str,
    authority_snapshot: "AuthoritySnapshot | None",
) -> str:
    actor_identity = authority_text(authority_snapshot, "actor_identity")
    if actor_identity:
        return actor_identity
    return ROLE_AGENT_DEFAULTS.get(str(role or "").strip().lower(), "operator")


def resume_receipt_command(*, role: str, provider: str) -> str:
    base = session_resume_command_for_role(role, format="json")
    provider_arg = provider or ROLE_AGENT_DEFAULTS.get(role, "operator")
    return f"{base} --provider {provider_arg} --write-resume-receipt"


def authority_text(authority_snapshot: "AuthoritySnapshot | None", attr: str) -> str:
    return str(getattr(authority_snapshot, attr, "") or "").strip()


__all__ = ["agent_id_for_role", "authority_text", "resume_receipt_command"]
