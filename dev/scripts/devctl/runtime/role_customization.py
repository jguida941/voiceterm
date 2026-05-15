"""Operator-defined role cards and guards over existing workstreams."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, replace
import re

from .development_team import build_default_development_topology
from .role_profile import normalize_tandem_role
from .value_coercion import coerce_mapping, coerce_string, coerce_string_items


CUSTOM_ROLE_DEFINITION_CONTRACT_ID = "CustomRoleDefinition"
ROLE_INSTRUCTION_CARD_CONTRACT_ID = "RoleInstructionCard"
ROLE_GUARD_CONTRACT_ID = "RoleGuard"
ROLE_CREATION_ACTION_CONTRACT_ID = "RoleCreationAction"
ROLE_CUSTOMIZATION_SCHEMA_VERSION = 1

_ROLE_ID_RE = re.compile(r"[^a-z0-9_]+")
_PROVIDER_SPECIFIC_COMMAND_MARKERS = ("claude-", "codex-", "cursor-")


@dataclass(frozen=True, slots=True)
class RoleInstructionCard:
    """Operator-editable typed instructions for one custom role."""

    card_id: str
    role_id: str
    instruction_kind: str
    rules: tuple[str, ...]
    guard_refs: tuple[str, ...] = ()
    source_ref: str = ""
    active: bool = True
    schema_version: int = ROLE_CUSTOMIZATION_SCHEMA_VERSION
    contract_id: str = ROLE_INSTRUCTION_CARD_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rules"] = list(self.rules)
        payload["guard_refs"] = list(self.guard_refs)
        return payload


@dataclass(frozen=True, slots=True)
class RoleGuard:
    """Typed enforcement row attached to one custom role."""

    guard_id: str
    role_id: str
    enforcement_point: str
    violation_action: str
    rule_refs: tuple[str, ...] = ()
    severity: str = "error"
    active: bool = True
    schema_version: int = ROLE_CUSTOMIZATION_SCHEMA_VERSION
    contract_id: str = ROLE_GUARD_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rule_refs"] = list(self.rule_refs)
        return payload


@dataclass(frozen=True, slots=True)
class CustomRoleDefinition:
    """Custom role overlay mapped to an existing workstream authority lane."""

    role_id: str
    base_workstream_id: str
    display_name: str
    description: str = ""
    base_tandem_role: str = ""
    capabilities: tuple[str, ...] = ()
    instruction_card_ids: tuple[str, ...] = ()
    guard_ids: tuple[str, ...] = ()
    slash_command_refs: tuple[str, ...] = ()
    active: bool = True
    schema_version: int = ROLE_CUSTOMIZATION_SCHEMA_VERSION
    contract_id: str = CUSTOM_ROLE_DEFINITION_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        for key in (
            "capabilities",
            "instruction_card_ids",
            "guard_ids",
            "slash_command_refs",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class RoleCreationAction:
    """Typed action payload for creating a custom role, cards, and guards."""

    action_id: str
    role: CustomRoleDefinition
    instruction_cards: tuple[RoleInstructionCard, ...]
    guards: tuple[RoleGuard, ...]
    requested_by: str
    status: str = "accepted"
    validation_errors: tuple[str, ...] = ()
    schema_version: int = ROLE_CUSTOMIZATION_SCHEMA_VERSION
    contract_id: str = ROLE_CREATION_ACTION_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["role"] = self.role.to_dict()
        payload["instruction_cards"] = [
            card.to_dict() for card in self.instruction_cards
        ]
        payload["guards"] = [guard.to_dict() for guard in self.guards]
        payload["validation_errors"] = list(self.validation_errors)
        return payload


@dataclass(frozen=True, slots=True)
class RoleCommandEnvelope:
    role_id: str
    available_commands: tuple[str, ...]
    enforcement_mode: str
    fleet_review_toggle: str
    operator_toggle_receipt: str
    schema_version: int = 1
    contract_id: str = "RoleCommandEnvelope"


def normalize_custom_role_id(value: object) -> str:
    """Normalize operator role ids without touching TandemRole."""
    text = coerce_string(value).lower().replace("-", "_").replace(" ", "_")
    return _ROLE_ID_RE.sub("_", text).strip("_")


def known_base_workstream_ids() -> tuple[str, ...]:
    """Return the existing authority lanes custom roles may overlay."""
    topology = build_default_development_topology()
    return tuple(item.workstream_id for item in topology.workstreams)


def build_role_creation_action(
    *,
    role_id: object,
    base_workstream_id: object,
    display_name: object = "",
    instructions: Iterable[object] = (),
    guards: Iterable[object] = (),
    slash_command_refs: Iterable[object] = (),
    requested_by: object = "operator",
) -> RoleCreationAction:
    """Build and validate a role-creation payload over existing workstreams."""
    normalized_role_id = normalize_custom_role_id(role_id)
    workstream_id = normalize_custom_role_id(base_workstream_id)
    slash_refs = tuple(coerce_string(item) for item in slash_command_refs if coerce_string(item))
    cards = tuple(
        RoleInstructionCard(
            card_id=f"{normalized_role_id}:instruction:{index}",
            role_id=normalized_role_id,
            instruction_kind="operator_rule",
            rules=(coerce_string(rule),),
            source_ref="role_creation_action",
        )
        for index, rule in enumerate(instructions, start=1)
        if coerce_string(rule)
    )
    guard_rows = tuple(
        RoleGuard(
            guard_id=f"{normalized_role_id}:guard:{index}",
            role_id=normalized_role_id,
            enforcement_point=coerce_string(guard) or "role_runtime",
            violation_action="fail_closed",
            rule_refs=tuple(card.card_id for card in cards),
        )
        for index, guard in enumerate(guards, start=1)
    )
    role = CustomRoleDefinition(
        role_id=normalized_role_id,
        base_workstream_id=workstream_id,
        base_tandem_role=_base_tandem_role_for_workstream(workstream_id),
        display_name=coerce_string(display_name) or normalized_role_id.replace("_", " ").title(),
        capabilities=tuple(card.instruction_kind for card in cards),
        instruction_card_ids=tuple(card.card_id for card in cards),
        guard_ids=tuple(guard.guard_id for guard in guard_rows),
        slash_command_refs=slash_refs,
    )
    action = RoleCreationAction(
        action_id=f"role_create:{normalized_role_id}",
        role=role,
        instruction_cards=cards,
        guards=guard_rows,
        requested_by=coerce_string(requested_by) or "operator",
    )
    errors = validate_role_creation_action(action)
    if not errors:
        return action
    return replace(action, status="rejected", validation_errors=errors)


def role_creation_action_from_mapping(
    payload: Mapping[str, object],
) -> RoleCreationAction:
    """Parse a role-creation action from a mapping."""
    mapping = coerce_mapping(payload)
    role = _role_definition_from_mapping(coerce_mapping(mapping.get("role")))
    cards = tuple(
        _instruction_card_from_mapping(coerce_mapping(item))
        for item in _mapping_items(mapping.get("instruction_cards"))
    )
    guards = tuple(
        _role_guard_from_mapping(coerce_mapping(item))
        for item in _mapping_items(mapping.get("guards"))
    )
    return RoleCreationAction(
        action_id=coerce_string(mapping.get("action_id")) or f"role_create:{role.role_id}",
        role=role,
        instruction_cards=cards,
        guards=guards,
        requested_by=coerce_string(mapping.get("requested_by")) or "operator",
        status=coerce_string(mapping.get("status")) or "accepted",
        validation_errors=coerce_string_items(mapping.get("validation_errors")),
        schema_version=_int(mapping.get("schema_version")) or ROLE_CUSTOMIZATION_SCHEMA_VERSION,
        contract_id=coerce_string(mapping.get("contract_id")) or ROLE_CREATION_ACTION_CONTRACT_ID,
    )


def validate_role_creation_action(action: RoleCreationAction) -> tuple[str, ...]:
    """Validate role creation without creating new authority lanes."""
    errors: list[str] = []
    if not action.role.role_id:
        errors.append("missing_role_id")
    if action.role.base_workstream_id not in set(known_base_workstream_ids()):
        errors.append("unknown_base_workstream")
    if normalize_tandem_role(action.role.role_id) is not None:
        errors.append("custom_role_must_not_shadow_tandem_role")
    for card in action.instruction_cards:
        if card.role_id != action.role.role_id:
            errors.append(f"instruction_card_role_mismatch:{card.card_id}")
    for guard in action.guards:
        if guard.role_id != action.role.role_id:
            errors.append(f"role_guard_role_mismatch:{guard.guard_id}")
    for ref in action.role.slash_command_refs:
        normalized = ref.lower().lstrip("/")
        if any(marker in normalized for marker in _PROVIDER_SPECIFIC_COMMAND_MARKERS):
            errors.append(f"provider_specific_slash_command:{ref}")
    return tuple(dict.fromkeys(errors))


def _base_tandem_role_for_workstream(workstream_id: str) -> str:
    if workstream_id in {"reviewer", "architect", "quality_engineer"}:
        return "reviewer"
    if workstream_id in {"builder", "researcher", "knowledge_synthesizer"}:
        return "implementer"
    if workstream_id == "operator":
        return "operator"
    return ""


def _role_definition_from_mapping(payload: Mapping[str, object]) -> CustomRoleDefinition:
    return CustomRoleDefinition(
        role_id=normalize_custom_role_id(payload.get("role_id")),
        base_workstream_id=normalize_custom_role_id(payload.get("base_workstream_id")),
        display_name=coerce_string(payload.get("display_name")),
        description=coerce_string(payload.get("description")),
        base_tandem_role=coerce_string(payload.get("base_tandem_role")),
        capabilities=coerce_string_items(payload.get("capabilities")),
        instruction_card_ids=coerce_string_items(payload.get("instruction_card_ids")),
        guard_ids=coerce_string_items(payload.get("guard_ids")),
        slash_command_refs=coerce_string_items(payload.get("slash_command_refs")),
        active=bool(payload.get("active", True)),
        schema_version=_int(payload.get("schema_version")) or ROLE_CUSTOMIZATION_SCHEMA_VERSION,
        contract_id=coerce_string(payload.get("contract_id")) or CUSTOM_ROLE_DEFINITION_CONTRACT_ID,
    )


def _instruction_card_from_mapping(payload: Mapping[str, object]) -> RoleInstructionCard:
    return RoleInstructionCard(
        card_id=coerce_string(payload.get("card_id")),
        role_id=normalize_custom_role_id(payload.get("role_id")),
        instruction_kind=coerce_string(payload.get("instruction_kind")),
        rules=coerce_string_items(payload.get("rules")),
        guard_refs=coerce_string_items(payload.get("guard_refs")),
        source_ref=coerce_string(payload.get("source_ref")),
        active=bool(payload.get("active", True)),
        schema_version=_int(payload.get("schema_version")) or ROLE_CUSTOMIZATION_SCHEMA_VERSION,
        contract_id=coerce_string(payload.get("contract_id")) or ROLE_INSTRUCTION_CARD_CONTRACT_ID,
    )


def _role_guard_from_mapping(payload: Mapping[str, object]) -> RoleGuard:
    return RoleGuard(
        guard_id=coerce_string(payload.get("guard_id")),
        role_id=normalize_custom_role_id(payload.get("role_id")),
        enforcement_point=coerce_string(payload.get("enforcement_point")),
        violation_action=coerce_string(payload.get("violation_action")),
        rule_refs=coerce_string_items(payload.get("rule_refs")),
        severity=coerce_string(payload.get("severity")) or "error",
        active=bool(payload.get("active", True)),
        schema_version=_int(payload.get("schema_version")) or ROLE_CUSTOMIZATION_SCHEMA_VERSION,
        contract_id=coerce_string(payload.get("contract_id")) or ROLE_GUARD_CONTRACT_ID,
    )


def _mapping_items(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "CUSTOM_ROLE_DEFINITION_CONTRACT_ID",
    "ROLE_CREATION_ACTION_CONTRACT_ID",
    "ROLE_CUSTOMIZATION_SCHEMA_VERSION",
    "ROLE_GUARD_CONTRACT_ID",
    "ROLE_INSTRUCTION_CARD_CONTRACT_ID",
    "CustomRoleDefinition",
    "RoleCreationAction",
    "RoleGuard",
    "RoleInstructionCard",
    "build_role_creation_action",
    "known_base_workstream_ids",
    "normalize_custom_role_id",
    "role_creation_action_from_mapping",
    "validate_role_creation_action",
]
