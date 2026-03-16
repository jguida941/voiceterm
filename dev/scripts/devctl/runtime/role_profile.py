"""Provider-agnostic role profiles for the tandem review/code loop.

Defines the three durable roles (reviewer, implementer, operator) that
the tandem loop requires, independent of which concrete AI provider
fills each role. Provider choice sits underneath these roles.

This module is the canonical source for role names, default provider
mappings, and the role-profile contract. All tandem-loop code that
needs to distinguish "who reviews" from "who codes" should import
from here instead of hardcoding provider names.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from .value_coercion import coerce_string


class TandemRole(StrEnum):
    """Provider-agnostic roles in the review/code tandem loop."""

    REVIEWER = "reviewer"
    IMPLEMENTER = "implementer"
    OPERATOR = "operator"


# Default provider-to-role mapping for the current VoiceTerm tandem loop.
# Other repos or configurations can override this via repo-pack policy.
DEFAULT_PROVIDER_ROLE_MAP: dict[str, TandemRole] = {
    "codex": TandemRole.REVIEWER,
    "claude": TandemRole.IMPLEMENTER,
    "cursor": TandemRole.IMPLEMENTER,
    "operator": TandemRole.OPERATOR,
    "human": TandemRole.OPERATOR,
}


@dataclass(frozen=True, slots=True)
class RoleProfile:
    """One participant in the tandem loop, identified by role not provider.

    The ``provider`` field records which concrete AI/human fills this role.
    The ``role`` field is the durable contract name that loop logic uses.
    """

    schema_version: int
    contract_id: str
    role: str
    provider: str
    display_name: str
    capabilities: tuple[str, ...]
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TandemProfile:
    """Complete role assignment for one tandem-loop session.

    Contains exactly one reviewer, one or more implementers, and one
    operator. The tandem guard and launcher should validate this profile
    before opening sessions.
    """

    schema_version: int
    contract_id: str
    reviewer: RoleProfile
    implementers: tuple[RoleProfile, ...]
    operator: RoleProfile

    def all_roles(self) -> tuple[RoleProfile, ...]:
        return (self.reviewer, *self.implementers, self.operator)

    def by_provider(self, provider: str) -> RoleProfile | None:
        for profile in self.all_roles():
            if profile.provider == provider:
                return profile
        return None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def role_for_provider(
    provider: str,
    provider_role_map: dict[str, TandemRole] | None = None,
) -> TandemRole:
    """Look up the tandem role for a concrete provider name."""
    mapping = provider_role_map or DEFAULT_PROVIDER_ROLE_MAP
    normalized = provider.strip().lower()
    return mapping.get(normalized, TandemRole.IMPLEMENTER)


def role_profile_from_mapping(payload: Mapping[str, object]) -> RoleProfile:
    """Parse a role profile from a JSON-like mapping."""
    provider = coerce_string(payload.get("provider"))
    role = coerce_string(payload.get("role"))
    if not role and provider:
        role = role_for_provider(provider).value
    capabilities_raw = payload.get("capabilities")
    capabilities: tuple[str, ...] = ()
    if isinstance(capabilities_raw, (list, tuple)):
        capabilities = tuple(str(v).strip() for v in capabilities_raw if str(v).strip())
    return RoleProfile(
        schema_version=int(payload.get("schema_version") or 1),
        contract_id=coerce_string(payload.get("contract_id")) or "RoleProfile",
        role=role or TandemRole.IMPLEMENTER.value,
        provider=provider or "unknown",
        display_name=coerce_string(payload.get("display_name")) or provider or "unknown",
        capabilities=capabilities,
        active=bool(payload.get("active", True)),
    )


def build_default_tandem_profile(
    *,
    reviewer_provider: str = "codex",
    implementer_providers: tuple[str, ...] = ("claude",),
    operator_provider: str = "operator",
) -> TandemProfile:
    """Build the default tandem profile for the current VoiceTerm loop."""
    return TandemProfile(
        schema_version=1,
        contract_id="TandemProfile",
        reviewer=RoleProfile(
            schema_version=1,
            contract_id="RoleProfile",
            role=TandemRole.REVIEWER.value,
            provider=reviewer_provider,
            display_name=reviewer_provider.title(),
            capabilities=("review", "promote", "heartbeat"),
        ),
        implementers=tuple(
            RoleProfile(
                schema_version=1,
                contract_id="RoleProfile",
                role=TandemRole.IMPLEMENTER.value,
                provider=provider,
                display_name=provider.title(),
                capabilities=("code", "fix", "ack"),
            )
            for provider in implementer_providers
        ),
        operator=RoleProfile(
            schema_version=1,
            contract_id="RoleProfile",
            role=TandemRole.OPERATOR.value,
            provider=operator_provider,
            display_name="Operator",
            capabilities=("approve", "deny", "configure"),
        ),
    )
