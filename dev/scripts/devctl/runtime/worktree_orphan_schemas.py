"""JSON schema generation for worktree-orphan slice-1 contracts."""

from __future__ import annotations

from dataclasses import dataclass

from .worktree_orphan_schema_core_specs import core_schema_specs
from .worktree_orphan_schema_runtime_specs import runtime_schema_specs
from .worktree_orphan_schema_support import FieldSpec

_JSON_SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"


@dataclass(frozen=True, slots=True)
class _ObjectSchema:
    title: str
    required: tuple[str, ...]
    properties: dict[str, dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        payload["$schema"] = _JSON_SCHEMA_URI
        payload["title"] = self.title
        payload["type"] = "object"
        payload["required"] = list(self.required)
        payload["properties"] = self.properties
        payload["additionalProperties"] = False
        return payload


def contract_json_schemas() -> dict[str, dict[str, object]]:
    """Return JSON schemas for every slice-1 worktree-orphan contract."""
    schemas: dict[str, dict[str, object]] = {}
    for contract_id, required, fields in (
        core_schema_specs() + runtime_schema_specs()
    ):
        schemas[contract_id] = _schema(
            contract_id,
            required=required,
            fields=fields,
            known_schemas=schemas,
        )
    return schemas


def _schema(
    title: str,
    *,
    required: tuple[str, ...],
    fields: tuple[FieldSpec, ...],
    known_schemas: dict[str, dict[str, object]],
) -> dict[str, object]:
    schema = _ObjectSchema(
        title=title,
        required=required,
        properties={
            field.name: _field_schema(field, known_schemas=known_schemas)
            for field in fields
        },
    )
    return schema.to_dict()


def _field_schema(
    field: FieldSpec,
    *,
    known_schemas: dict[str, dict[str, object]],
) -> dict[str, object]:
    if field.object_ref:
        return dict(known_schemas[field.object_ref])
    payload: dict[str, object] = {"type": field.value_type}
    if field.enum_values:
        payload["enum"] = list(field.enum_values)
    if field.const_value:
        payload["const"] = field.const_value
    if field.item_type:
        payload["items"] = {"type": field.item_type}
    if field.item_ref:
        payload["items"] = dict(known_schemas[field.item_ref])
    return payload


__all__ = ["contract_json_schemas"]
