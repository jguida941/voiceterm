"""Typed-role live topology helpers.

Provider ids are runtime adapter labels. Topology authority is typed
actor/session/role/capability state. Primary role ids remain intact; capability
classes are only secondary compatibility metadata for older callers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .role_profile import TandemRole, normalize_role_id, role_capability_classes
from .session_liveness_signal import (
    LIVE_SESSION_LIVENESS_STATES,
    RUNTIME_PRESENT_LIVENESS_STATES,
)
from .value_coercion import coerce_bool


@dataclass(frozen=True, slots=True)
class RoleOccupancy:
    """One live or configured actor occupying a primary typed role id."""

    role_id: str
    provider: str
    actor_id: str | None = None
    session_id: str | None = None
    live: bool = True
    authority_refs: tuple[str, ...] = ()
    capability_classes: tuple[str, ...] = ()
    migration_debt: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LiveRoleTopology:
    """Live role counts and provider occupancy for one topology snapshot."""

    role_occupancies: tuple[RoleOccupancy, ...]
    reviewer_provider: str
    implementer_providers: tuple[str, ...]
    live_reviewer_providers: tuple[str, ...]
    live_implementer_providers: tuple[str, ...]
    live_operator_providers: tuple[str, ...]
    active_providers: tuple[str, ...]
    migration_debt: tuple[str, ...] = ()

    @property
    def live_reviewer(self) -> bool:
        for _provider in self.live_reviewer_providers:
            return True
        return False

    @property
    def live_implementer(self) -> bool:
        for _provider in self.live_implementer_providers:
            return True
        return False

    @property
    def missing_required_roles(self) -> tuple[str, ...]:
        missing: list[str] = []
        if not self.live_reviewer:
            missing.append(TandemRole.REVIEWER.value)
        if not self.live_implementer:
            missing.append(TandemRole.IMPLEMENTER.value)
        return tuple(missing)

    def role_counts(self) -> dict[str, int]:
        return {
            "live_participants_total": len(
                set(
                    [
                        *self.live_reviewer_providers,
                        *self.live_implementer_providers,
                        *self.live_operator_providers,
                    ]
                )
            ),
            "live_reviewer_total": len(self.live_reviewer_providers),
            "live_implementer_total": len(self.live_implementer_providers),
        }

    def providers_for_role(self, role: str) -> tuple[str, ...]:
        normalized = normalize_role_id(role)
        for role_name, providers in self.live_role_providers:
            if role_name == normalized:
                return providers
        return ()

    @property
    def live_role_providers(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        role_map = _role_provider_map(self.role_occupancies)
        return tuple((role, providers) for role, providers in sorted(role_map.items()))

    @property
    def typed_role_topology_label(self) -> str:
        if not self.live_role_providers:
            return "typed_role_topology_unresolved"
        chunks = [
            f"{role}:{','.join(providers)}"
            for role, providers in self.live_role_providers
            if providers
        ]
        return "typed_role_topology[" + ";".join(chunks) + "]"


def resolve_role_topology(
    bridge_liveness: Mapping[str, object],
    *,
    include_runtime_presence: bool = False,
) -> LiveRoleTopology:
    """Resolve occupied runtime roles from typed liveness evidence."""
    live_states = (
        RUNTIME_PRESENT_LIVENESS_STATES
        if include_runtime_presence
        else LIVE_SESSION_LIVENESS_STATES
    )
    occupancies, migration_debt = _live_role_occupancies(
        bridge_liveness,
        live_states=live_states,
    )
    role_provider_map = _role_provider_map(occupancies)
    reviewer_providers = _providers_for_capability(
        role_provider_map,
        TandemRole.REVIEWER,
    )
    reviewer_provider = reviewer_providers[0] if reviewer_providers else ""
    implementer_providers = _providers_for_capability(
        role_provider_map,
        TandemRole.IMPLEMENTER,
    )
    active_providers = _active_providers(
        bridge_liveness,
        include_runtime_presence=include_runtime_presence,
        occupancies=occupancies,
    )
    reviewer_live: list[str] = []
    implementer_live: list[str] = []
    operator_live: list[str] = []
    for provider in active_providers:
        normalized_provider = str(provider or "").strip().lower()
        matched_explicit_role = False
        if normalized_provider == reviewer_provider:
            _append_unique(reviewer_live, provider)
            matched_explicit_role = True
        if normalized_provider in implementer_providers:
            _append_unique(implementer_live, provider)
            matched_explicit_role = True
        if matched_explicit_role:
            continue
        role = _role_for_provider(provider, role_provider_map=role_provider_map)
        legacy_class = _legacy_tandem_class_for_role(role)
        if legacy_class == TandemRole.OPERATOR:
            _append_unique(operator_live, provider)
        elif legacy_class == TandemRole.REVIEWER:
            _append_unique(reviewer_live, provider)
        elif legacy_class == TandemRole.IMPLEMENTER:
            _append_unique(implementer_live, provider)
    for occupancy in occupancies:
        legacy_class = _legacy_tandem_class(occupancy)
        if legacy_class == TandemRole.REVIEWER:
            _append_unique(reviewer_live, occupancy.provider)
        elif legacy_class == TandemRole.IMPLEMENTER:
            _append_unique(implementer_live, occupancy.provider)
        elif legacy_class == TandemRole.OPERATOR:
            _append_unique(operator_live, occupancy.provider)
    return LiveRoleTopology(
        role_occupancies=occupancies,
        reviewer_provider=reviewer_provider,
        implementer_providers=implementer_providers,
        live_reviewer_providers=tuple(reviewer_live),
        live_implementer_providers=tuple(implementer_live),
        live_operator_providers=tuple(operator_live),
        active_providers=active_providers,
        migration_debt=tuple(migration_debt),
    )


def _active_providers(
    bridge_liveness: Mapping[str, object],
    *,
    include_runtime_presence: bool,
    occupancies: tuple[RoleOccupancy, ...],
) -> tuple[str, ...]:
    providers: list[str] = []
    for provider in _string_values(bridge_liveness.get("active_conductor_providers")):
        _append_unique(providers, provider)
    if coerce_bool(bridge_liveness.get("codex_conductor_active")):
        _append_unique(providers, "codex")
    if coerce_bool(bridge_liveness.get("claude_conductor_active")):
        _append_unique(providers, "claude")
    for occupancy in occupancies:
        _append_unique(providers, occupancy.provider)
    if include_runtime_presence:
        for field_name in (
            "active_runtime_providers",
            "remote_control_active_providers",
            "packet_activity_active_providers",
        ):
            for provider in _string_values(bridge_liveness.get(field_name)):
                _append_unique(providers, provider)
        if coerce_bool(bridge_liveness.get("reviewer_activity_active")):
            provider = str(
                bridge_liveness.get("reviewer_activity_provider") or ""
            ).strip().lower()
            if provider:
                _append_unique(providers, provider)
    return tuple(providers)


def _live_role_occupancies(
    bridge_liveness: Mapping[str, object],
    *,
    live_states: frozenset[str],
) -> tuple[tuple[RoleOccupancy, ...], tuple[str, ...]]:
    result: list[RoleOccupancy] = []
    migration_debt: list[str] = []
    for row in _typed_role_rows(bridge_liveness):
        if not isinstance(row, Mapping):
            continue
        state = str(row.get("state") or "").strip()
        if state and state not in live_states:
            continue
        if row.get("live") is not None and not coerce_bool(row.get("live")):
            continue
        provider = str(row.get("provider") or "").strip().lower()
        deprecated_role_ids = _deprecated_role_ids(row)
        role = _role_from_row(row)
        if provider and role:
            result.append(
                RoleOccupancy(
                    role_id=role,
                    provider=provider,
                    actor_id=_optional_string(
                        row.get("actor_id") or row.get("agent_id")
                    ),
                    session_id=_optional_string(
                        row.get("session_id") or row.get("session_name")
                    ),
                    live=True,
                    authority_refs=_authority_refs(row),
                    capability_classes=role_capability_classes(
                        role,
                        grants=row.get("grants"),
                    ),
                    migration_debt=tuple(
                        f"deprecated_role_id:{deprecated_role_id}"
                        for deprecated_role_id in deprecated_role_ids
                    ),
                )
            )
        if provider:
            for deprecated_role_id in deprecated_role_ids:
                _append_unique(migration_debt, f"{provider}:{deprecated_role_id}")
    return tuple(result), tuple(migration_debt)


def _typed_role_rows(
    bridge_liveness: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows: list[Mapping[str, object]] = []
    for field_name in ("session_liveness_signals", "participant_liveness"):
        value = bridge_liveness.get(field_name)
        if isinstance(value, (list, tuple)):
            rows.extend(row for row in value if isinstance(row, Mapping))
    collaboration = bridge_liveness.get("collaboration")
    if isinstance(collaboration, Mapping):
        for field_name in (
            "actor_authorities",
            "participants",
            "role_assignments",
        ):
            value = collaboration.get(field_name)
            if isinstance(value, (list, tuple)):
                rows.extend(row for row in value if isinstance(row, Mapping))
    for field_name in ("actor_authorities", "participants", "role_assignments"):
        value = bridge_liveness.get(field_name)
        if isinstance(value, (list, tuple)):
            rows.extend(row for row in value if isinstance(row, Mapping))
    return tuple(rows)


def _role_from_row(row: Mapping[str, object]) -> str:
    primary_role_id = normalize_role_id(row.get("role_id"))
    if primary_role_id:
        if primary_role_id in _DEPRECATED_ROLE_IDS:
            return _deprecated_role_replacement(primary_role_id)
        return primary_role_id
    for field_name in ("role", "actor_role", "role_preset", "target_role"):
        role = normalize_role_id(row.get(field_name))
        if role in _DEPRECATED_ROLE_IDS:
            return _deprecated_role_replacement(role)
        if role:
            return role
    return ""


_DEPRECATED_ROLE_IDS = frozenset(
    {"lead_agent", "review_agent", "coding_agent", "operator_agent"}
)


def _deprecated_role_ids(row: Mapping[str, object]) -> tuple[str, ...]:
    role_ids: list[str] = []
    for field_name in ("role_id", "role", "actor_role", "role_preset", "target_role"):
        role_id = normalize_role_id(row.get(field_name))
        if role_id in _DEPRECATED_ROLE_IDS:
            _append_unique(role_ids, role_id)
    return tuple(role_ids)


def _deprecated_role_replacement(role_id: str) -> str:
    return {
        "lead_agent": "orchestrator",
        "review_agent": "architecture_review",
        "coding_agent": "implementation",
        "operator_agent": "operator",
    }.get(role_id, "")


def _first_signal_provider_for_role(
    bridge_liveness: Mapping[str, object],
    role: str,
    *,
    live_states: frozenset[str],
) -> str:
    occupancies, _debt = _live_role_occupancies(
        bridge_liveness,
        live_states=live_states,
    )
    for occupancy in occupancies:
        if occupancy.role_id == role:
            return occupancy.provider
    return ""


def _role_for_provider(
    provider: str,
    *,
    role_provider_map: Mapping[str, tuple[str, ...]],
) -> str:
    normalized = str(provider or "").strip().lower()
    for role, providers in role_provider_map.items():
        if normalized in providers:
            return role
    return ""


def _role_provider_map(
    occupancies: tuple[RoleOccupancy, ...],
) -> dict[str, tuple[str, ...]]:
    result: dict[str, list[str]] = {}
    for occupancy in occupancies:
        result.setdefault(occupancy.role_id, [])
        _append_unique(result[occupancy.role_id], occupancy.provider)
    return {role: tuple(providers) for role, providers in result.items()}


def _providers_for_capability(
    role_provider_map: Mapping[str, tuple[str, ...]],
    capability_class: TandemRole,
) -> tuple[str, ...]:
    providers: list[str] = []
    for role, role_providers in role_provider_map.items():
        if _legacy_tandem_class_for_role(role) != capability_class:
            continue
        for provider in role_providers:
            _append_unique(providers, provider)
    return tuple(providers)


def _legacy_tandem_class(occupancy: RoleOccupancy) -> TandemRole | None:
    return _legacy_tandem_from_capability_classes(occupancy.capability_classes)


def _legacy_tandem_class_for_role(role: object) -> TandemRole | None:
    return _legacy_tandem_from_capability_classes(role_capability_classes(role))


def _legacy_tandem_from_capability_classes(
    capability_classes: tuple[str, ...],
) -> TandemRole | None:
    for capability_class in capability_classes:
        if capability_class in {"implementation", "mutation"}:
            return TandemRole.IMPLEMENTER
        if capability_class in {"control", "observe"}:
            return TandemRole.OPERATOR
        if capability_class in {"review", "test", "architecture", "governance", "research", "intake"}:
            return TandemRole.REVIEWER
    return None


def _authority_refs(row: Mapping[str, object]) -> tuple[str, ...]:
    refs: list[str] = []
    for field_name in (
        "source",
        "source_contract",
        "packet_id",
        "approval_ref",
        "snapshot_id",
        "authority_ref",
        "zref",
    ):
        _append_unique(refs, _string(row.get(field_name)))
    value = row.get("evidence_refs")
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _append_unique(refs, _string(item))
    return tuple(refs)


def _string(value: object) -> str:
    return str(value or "").strip()


def _optional_string(value: object) -> str | None:
    text = _string(value)
    return text or None


def _string_values(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        return ()
    return tuple(
        str(item or "").strip().lower()
        for item in value
        if str(item or "").strip()
    )


def _append_unique(values: list[str], value: str) -> None:
    normalized = str(value or "").strip().lower()
    if normalized and normalized not in values:
        values.append(normalized)


__all__ = [
    "LiveRoleTopology",
    "RoleOccupancy",
    "resolve_role_topology",
]
