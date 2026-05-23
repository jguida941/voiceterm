"""Provider-neutral role profiles for governed agent work.

Provider names are adapter identities. Runtime authority comes from typed
actor/session/role/capability state, not from provider defaults or topology
mode labels.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import re
from typing import Any

from .enum_compat import StrEnum
from .value_coercion import coerce_string, coerce_string_items


class TandemRole(StrEnum):
    """Capability classes used by older tandem-loop guards."""

    REVIEWER = "reviewer"
    IMPLEMENTER = "implementer"
    OPERATOR = "operator"


class RoleCapabilityClass(StrEnum):
    """Secondary capability tags for primary typed role ids."""

    REVIEW = "review"
    IMPLEMENTATION = "implementation"
    CONTROL = "control"
    OBSERVE = "observe"
    TEST = "test"
    ARCHITECTURE = "architecture"
    GOVERNANCE = "governance"
    RESEARCH = "research"
    INTAKE = "intake"
    MUTATION = "mutation"


REGISTERED_COGNITIVE_ROLES: tuple[str, ...] = (
    "orchestrator",
    "watcher",
    "codex_research",
    "implementation",
    "architecture_review",
    "duplicate_scope_guard",
    "dogfood_test",
    "governance_receipt",
)
"""Current typed cognitive-role roster from the cached-hammock plan."""

DEFAULT_ROLE_IDS: tuple[str, ...] = tuple(
    dict.fromkeys(
        (
            *REGISTERED_COGNITIVE_ROLES,
            "dashboard",
            "implementer",
            "reviewer",
            "architect",
            "researcher",
            "intake",
            "tester",
            "operator",
            "observer",
            "plan_steward",
            "builder",
            "coder",
            "tdd_discovery",
            "tdd_first_role",
            "operator_inquiry_role",
            "governance_discovery_agent",
            "system_alignment_role",
        )
    )
)
"""Seed role ids from the active plan, `/develop`, guards, and typed custom roles.

The tuple is not a closed enum. Runtime role authority still comes from typed
role/session/capability state and custom role definitions.
"""


class OperatorRole(StrEnum):
    """First-class operator directive sources in runtime routing."""

    HUMAN_OPERATOR = "human_operator"
    AGENT_RUNTIME = "agent_runtime"
    AUTOMATION_LOOP = "automation_loop"
    REMOTE_OPERATOR = "remote_operator"


OPERATOR_DIRECTIVE_CAPABILITIES: tuple[str, ...] = (
    "directive_authority",
    "bypass_authority",
    "override_authority",
    "dogfood_witness",
)


# Provider names are adapter identities, not role authority. Callers that need a
# provider-to-role mapping must pass a typed map derived from session/topology
# state. An empty default makes provider-only inputs fail closed.
DEFAULT_PROVIDER_ROLE_MAP: dict[str, TandemRole] = {}

_REVIEWER_ROLE_ALIASES = frozenset({"review", "reviewer"})
_IMPLEMENTER_ROLE_ALIASES = frozenset(
    {"code", "coder", "coding", "implement", "implementer"}
)
_ROLE_ID_RE = re.compile(r"[^a-z0-9_]+")
_ROLE_ID_ALIASES = {role.replace("_", "-"): role for role in DEFAULT_ROLE_IDS}
_ROLE_ID_ALIASES.update({role: role for role in DEFAULT_ROLE_IDS})
_ROLE_ID_ALIASES.update(
    {
        "dogfood_tester": "dogfood_test",
        "dogfood_test_role": "dogfood_test",
        "dogfooder": "dogfood_test",
        "governance_receipt_role": "governance_receipt",
        "governance_receipter": "governance_receipt",
        "quality_engineer": "tester",
        "test_driver": "tester",
        "testdriven": "tdd_first_role",
        "tdd_first": "tdd_first_role",
        "tddfirst": "tdd_first_role",
        "tdd_first_role": "tdd_first_role",
        "tdd_discovery_role": "tdd_discovery",
        "rule_runner": "governance_receipt",
        "rule_runner_role": "governance_receipt",
    }
)
_OPERATOR_ROLE_ALIASES = frozenset(
    {"operator", "approver", "human_operator", "remote_operator"}
)
_ROLE_CAPABILITY_CLASSES: dict[str, tuple[RoleCapabilityClass, ...]] = {
    "implementation": (RoleCapabilityClass.IMPLEMENTATION,),
    "implementer": (RoleCapabilityClass.IMPLEMENTATION,),
    "builder": (RoleCapabilityClass.IMPLEMENTATION,),
    "coder": (RoleCapabilityClass.IMPLEMENTATION,),
    "reviewer": (RoleCapabilityClass.REVIEW,),
    "review": (RoleCapabilityClass.REVIEW,),
    "architecture_review": (
        RoleCapabilityClass.REVIEW,
        RoleCapabilityClass.ARCHITECTURE,
    ),
    "architect": (RoleCapabilityClass.ARCHITECTURE,),
    "researcher": (RoleCapabilityClass.RESEARCH,),
    "codex_research": (RoleCapabilityClass.RESEARCH,),
    "duplicate_scope_guard": (RoleCapabilityClass.REVIEW, RoleCapabilityClass.GOVERNANCE),
    "tester": (RoleCapabilityClass.TEST,),
    "dogfood_test": (RoleCapabilityClass.TEST,),
    "tdd_discovery": (RoleCapabilityClass.TEST,),
    "tdd_first_role": (RoleCapabilityClass.TEST,),
    "governance_receipt": (RoleCapabilityClass.GOVERNANCE,),
    "watcher": (RoleCapabilityClass.OBSERVE,),
    "orchestrator": (RoleCapabilityClass.CONTROL,),
    "plan_steward": (RoleCapabilityClass.GOVERNANCE,),
    "observer": (RoleCapabilityClass.OBSERVE,),
    "dashboard": (RoleCapabilityClass.OBSERVE,),
    "operator": (RoleCapabilityClass.CONTROL,),
    "review_agent": (RoleCapabilityClass.REVIEW,),
    "coding_agent": (RoleCapabilityClass.IMPLEMENTATION,),
    "operator_agent": (RoleCapabilityClass.CONTROL, RoleCapabilityClass.OBSERVE),
    "operator_inquiry_role": (RoleCapabilityClass.CONTROL,),
    "governance_discovery_agent": (
        RoleCapabilityClass.GOVERNANCE,
        RoleCapabilityClass.RESEARCH,
    ),
    "system_alignment_role": (
        RoleCapabilityClass.GOVERNANCE,
        RoleCapabilityClass.ARCHITECTURE,
    ),
}
_GRANT_CAPABILITY_CLASSES: dict[str, RoleCapabilityClass] = {
    "implementation.edit": RoleCapabilityClass.MUTATION,
    "repo.write": RoleCapabilityClass.MUTATION,
    "repo.mutate": RoleCapabilityClass.MUTATION,
    "repo.stage": RoleCapabilityClass.MUTATION,
    "repo.commit": RoleCapabilityClass.MUTATION,
    "review.checkpoint": RoleCapabilityClass.REVIEW,
    "review.finding": RoleCapabilityClass.REVIEW,
    "review.verdict": RoleCapabilityClass.REVIEW,
    "runtime.observe": RoleCapabilityClass.OBSERVE,
    "approval.commit": RoleCapabilityClass.CONTROL,
    "guard.run": RoleCapabilityClass.TEST,
    "dogfood.run": RoleCapabilityClass.TEST,
}
_LEGACY_TANDEM_FROM_CAPABILITY_CLASS: dict[RoleCapabilityClass, TandemRole] = {
    RoleCapabilityClass.IMPLEMENTATION: TandemRole.IMPLEMENTER,
    RoleCapabilityClass.MUTATION: TandemRole.IMPLEMENTER,
    RoleCapabilityClass.CONTROL: TandemRole.OPERATOR,
    RoleCapabilityClass.OBSERVE: TandemRole.OPERATOR,
    RoleCapabilityClass.REVIEW: TandemRole.REVIEWER,
    RoleCapabilityClass.TEST: TandemRole.REVIEWER,
    RoleCapabilityClass.ARCHITECTURE: TandemRole.REVIEWER,
    RoleCapabilityClass.GOVERNANCE: TandemRole.REVIEWER,
    RoleCapabilityClass.RESEARCH: TandemRole.REVIEWER,
    RoleCapabilityClass.INTAKE: TandemRole.REVIEWER,
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
class OperatorDirectivePacket:
    """Typed packet envelope for first-class operator directives."""

    directive_id: str
    operator_role: str
    issued_by: str
    target_role: str
    target_session_id: str
    scope: str
    summary: str
    body: str = ""
    capabilities: tuple[str, ...] = OPERATOR_DIRECTIVE_CAPABILITIES
    evidence_refs: tuple[str, ...] = ()
    issued_at_utc: str = ""
    expires_at_utc: str = ""
    schema_version: int = 1
    contract_id: str = "OperatorDirectivePacket"

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
) -> TandemRole | None:
    """Look up the tandem role for a concrete provider name."""
    mapping = provider_role_map if provider_role_map is not None else DEFAULT_PROVIDER_ROLE_MAP
    normalized = provider.strip().lower()
    return mapping.get(normalized)


def normalize_tandem_role(role: str | TandemRole | None) -> TandemRole | None:
    """Return one canonical tandem role or ``None`` for unknown text."""
    if isinstance(role, TandemRole):
        return role
    normalized = coerce_string(role).lower().replace("-", "_").replace(" ", "_")
    if not normalized:
        return None
    if normalized in _REVIEWER_ROLE_ALIASES:
        return TandemRole.REVIEWER
    if normalized in _IMPLEMENTER_ROLE_ALIASES:
        return TandemRole.IMPLEMENTER
    if normalized in _OPERATOR_ROLE_ALIASES:
        return TandemRole.OPERATOR
    return None


def normalize_role_id(role: object) -> str:
    """Return the primary typed role id for any registered or custom role."""
    raw = coerce_string(role)
    if not raw:
        return ""
    normalized = _camel_to_snake(raw).lower().replace("-", "_").replace(" ", "_")
    normalized = _ROLE_ID_RE.sub("_", normalized).strip("_")
    if not normalized:
        return ""
    return _ROLE_ID_ALIASES.get(normalized, normalized)


def normalize_registered_role(role: object) -> str:
    """Compatibility wrapper for callers that already use the older name."""
    return normalize_role_id(role)


def role_capability_classes(
    role: object,
    *,
    grants: object = (),
) -> tuple[str, ...]:
    """Return secondary capability tags for a primary role id and grants."""
    role_id = normalize_role_id(role)
    classes: list[str] = []
    for capability_class in _ROLE_CAPABILITY_CLASSES.get(role_id, ()):
        _append_unique(classes, capability_class.value)
    if isinstance(grants, (list, tuple)):
        for row in grants:
            capability = ""
            granted = True
            if isinstance(row, Mapping):
                capability = coerce_string(row.get("capability")).lower()
                granted = bool(row.get("granted", True))
            else:
                capability = coerce_string(row).lower()
            if not granted:
                continue
            capability_class = _GRANT_CAPABILITY_CLASSES.get(capability)
            if capability_class is not None:
                _append_unique(classes, capability_class.value)
    return tuple(classes)


def role_capability_class(role: object) -> TandemRole | None:
    """Legacy tandem class derived from secondary capability tags."""
    for capability_class in role_capability_classes(role):
        tandem = _LEGACY_TANDEM_FROM_CAPABILITY_CLASS.get(
            RoleCapabilityClass(capability_class)
        )
        if tandem is not None:
            return tandem
    return normalize_tandem_role(role)


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def _camel_to_snake(value: str) -> str:
    first_pass = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first_pass)


def default_provider_for_role(
    role: str | TandemRole,
    provider_role_map: dict[str, TandemRole] | None = None,
) -> str:
    """Return the default provider for one tandem role."""
    normalized_role = normalize_tandem_role(role)
    if normalized_role is None:
        return ""
    mapping = provider_role_map if provider_role_map is not None else DEFAULT_PROVIDER_ROLE_MAP
    for provider, mapped_role in mapping.items():
        if mapped_role == normalized_role:
            return provider
    return ""


def role_profile_from_mapping(payload: Mapping[str, object]) -> RoleProfile:
    """Parse a role profile from a JSON-like mapping."""
    provider = coerce_string(payload.get("provider"))
    role = normalize_role_id(
        payload.get("role") or payload.get("role_id") or payload.get("role_preset")
    )
    if not role and provider:
        resolved_role = role_for_provider(provider)
        role = resolved_role.value if resolved_role is not None else ""
    capabilities_raw = payload.get("capabilities")
    capabilities: tuple[str, ...] = ()
    if isinstance(capabilities_raw, (list, tuple)):
        capabilities = tuple(str(v).strip() for v in capabilities_raw if str(v).strip())
    return RoleProfile(
        schema_version=int(payload.get("schema_version") or 1),
        contract_id=coerce_string(payload.get("contract_id")) or "RoleProfile",
        role=role,
        provider=provider or "unknown",
        display_name=coerce_string(payload.get("display_name")) or provider or "unknown",
        capabilities=capabilities,
        active=bool(payload.get("active", True)),
    )


def operator_directive_packet_from_mapping(
    payload: Mapping[str, object],
) -> OperatorDirectivePacket:
    """Parse an operator directive packet from a JSON-like mapping."""
    operator_role = _operator_role_value(payload.get("operator_role"))
    capabilities = coerce_string_items(payload.get("capabilities"))
    return OperatorDirectivePacket(
        directive_id=coerce_string(payload.get("directive_id")),
        operator_role=operator_role.value,
        issued_by=coerce_string(payload.get("issued_by")) or operator_role.value,
        target_role=normalize_role_id(payload.get("target_role")),
        target_session_id=coerce_string(payload.get("target_session_id")),
        scope=coerce_string(payload.get("scope")),
        summary=coerce_string(payload.get("summary")),
        body=coerce_string(payload.get("body")),
        capabilities=capabilities or OPERATOR_DIRECTIVE_CAPABILITIES,
        evidence_refs=coerce_string_items(payload.get("evidence_refs")),
        issued_at_utc=coerce_string(payload.get("issued_at_utc")),
        expires_at_utc=coerce_string(payload.get("expires_at_utc")),
        schema_version=int(payload.get("schema_version") or 1),
        contract_id=(
            coerce_string(payload.get("contract_id")) or "OperatorDirectivePacket"
        ),
    )


def _operator_role_value(value: object) -> OperatorRole:
    normalized = coerce_string(value).lower().replace("-", "_").replace(" ", "_")
    if normalized in {"operator", "human"}:
        normalized = OperatorRole.HUMAN_OPERATOR.value
    if normalized == "remote":
        normalized = OperatorRole.REMOTE_OPERATOR.value
    if normalized == "automation":
        normalized = OperatorRole.AUTOMATION_LOOP.value
    if normalized == "agent":
        normalized = OperatorRole.AGENT_RUNTIME.value
    try:
        return OperatorRole(normalized)
    except ValueError:
        return OperatorRole.HUMAN_OPERATOR


def build_default_tandem_profile(
    *,
    reviewer_provider: str = "",
    implementer_providers: tuple[str, ...] = (),
    operator_provider: str = "operator",
) -> TandemProfile:
    """Build a role profile from explicit typed provider assignments.

    Empty provider inputs intentionally render as ``unassigned``. They do not
    grant role or mutation authority, and they prevent callers from silently
    reviving old provider-pair defaults.
    """
    reviewer_provider = _profile_provider(reviewer_provider)
    implementer_providers = tuple(
        _profile_provider(provider) for provider in implementer_providers if provider
    )
    if not implementer_providers:
        implementer_providers = ("unassigned",)
    operator_provider = _profile_provider(operator_provider)
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
            display_name=operator_provider.title(),
            capabilities=("approve", "deny", "configure"),
        ),
    )


def _profile_provider(provider: str) -> str:
    return coerce_string(provider).lower() or "unassigned"
