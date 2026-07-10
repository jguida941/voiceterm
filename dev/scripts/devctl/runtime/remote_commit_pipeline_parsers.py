"""Parsing helpers kept out of the remote commit pipeline model."""

from __future__ import annotations

from .action_contracts import ActionResult, action_result_from_mapping
from .role_review_lifecycle import (
    RoleReviewAssignmentLifecycle,
    role_review_assignment_lifecycles_from_value,
)
from .value_coercion import coerce_mapping


def action_result_from_object(value: object) -> ActionResult | None:
    mapping = coerce_mapping(value)
    if not mapping:
        return None
    return action_result_from_mapping(mapping)


def role_review_lifecycles_from_object(
    value: object,
) -> tuple[RoleReviewAssignmentLifecycle, ...]:
    return role_review_assignment_lifecycles_from_value(value)


__all__ = [
    "RoleReviewAssignmentLifecycle",
    "action_result_from_object",
    "role_review_lifecycles_from_object",
]
