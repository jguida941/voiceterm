"""Schema-spec helpers for worktree-orphan contract schemas."""

from __future__ import annotations

from typing import NamedTuple


class FieldSpec(NamedTuple):
    name: str
    value_type: str
    enum_values: tuple[str, ...] = ()
    const_value: str = ""
    item_type: str = ""
    item_ref: str = ""
    object_ref: str = ""


def spec(title: str, required: tuple[str, ...], *fields: FieldSpec):
    return (title, required, tuple(fields))


def field(
    name: str,
    value_type: str = "string",
    *,
    enum_values: tuple[str, ...] = (),
    const_value: str = "",
) -> FieldSpec:
    return FieldSpec(
        name=name,
        value_type=value_type,
        enum_values=enum_values,
        const_value=const_value,
    )


def array(
    name: str,
    *,
    item_type: str = "string",
    item_ref: str = "",
) -> FieldSpec:
    return FieldSpec(
        name=name,
        value_type="array",
        item_type="" if item_ref else item_type,
        item_ref=item_ref,
    )


def object_ref(name: str, contract_id: str) -> FieldSpec:
    return FieldSpec(name=name, value_type="object", object_ref=contract_id)


__all__ = ["FieldSpec", "array", "field", "object_ref", "spec"]
