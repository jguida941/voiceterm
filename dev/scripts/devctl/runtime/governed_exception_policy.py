"""Policy and descriptor contracts for governed exceptions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

from .governed_exception_base import (
    EXCEPTION_CLASS_CONTRACT_ID,
    EXCEPTION_LIFECYCLE_STATUS_CONTRACT_ID,
    EXCEPTION_POLICY_CONTRACT_ID,
    GOVERNED_EXCEPTION_SCHEMA_VERSION,
    json_ready_dict,
)
from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)

ALLOWED_EXCEPTION_CLASS_IDS = frozenset(
    {
        "managed_projection_refresh_failure",
        "generated_surface_drift",
        "review_snapshot_refresh_failure",
        "known_false_positive_guard",
        "transient_lock_after_bounded_retry",
        "stale_projection_index",
    }
)

FORBIDDEN_EXCEPTION_CLASS_IDS = frozenset(
    {
        "security_secret_detection",
        "missing_subprocess_evidence",
        "remote_rejection_or_conflict",
        "destructive_migration",
        "unreviewed_authored_source_dirt",
        "stale_head_authorization",
        "changed_worktree_after_approval",
        "unknown_executor_result",
    }
)


@dataclass(frozen=True, slots=True)
class ExceptionClass:
    """Policy-visible exception class descriptor."""

    class_id: str
    description: str = ""
    allowed_by_default: bool = False
    forbidden: bool = False
    mutation_class: bool = False
    action_kinds: tuple[str, ...] = ()
    required_proof_refs: tuple[str, ...] = ()
    schema_version: int = GOVERNED_EXCEPTION_SCHEMA_VERSION
    contract_id: str = EXCEPTION_CLASS_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return json_ready_dict(asdict(self))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "ExceptionClass":
        mapping = coerce_mapping(payload)
        return cls(
            class_id=coerce_string(mapping.get("class_id")),
            description=coerce_string(mapping.get("description")),
            allowed_by_default=coerce_bool(mapping.get("allowed_by_default")),
            forbidden=coerce_bool(mapping.get("forbidden")),
            mutation_class=coerce_bool(mapping.get("mutation_class")),
            action_kinds=coerce_string_items(mapping.get("action_kinds")),
            required_proof_refs=coerce_string_items(mapping.get("required_proof_refs")),
            schema_version=coerce_int(mapping.get("schema_version"))
            or GOVERNED_EXCEPTION_SCHEMA_VERSION,
        )


@dataclass(frozen=True, slots=True)
class ExceptionLifecycleStatus:
    """Bounded lifecycle-status descriptor."""

    status: str
    terminal: bool = False
    allowed_next_statuses: tuple[str, ...] = ()
    schema_version: int = GOVERNED_EXCEPTION_SCHEMA_VERSION
    contract_id: str = EXCEPTION_LIFECYCLE_STATUS_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return json_ready_dict(asdict(self))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "ExceptionLifecycleStatus":
        mapping = coerce_mapping(payload)
        return cls(
            status=coerce_string(mapping.get("status")),
            terminal=coerce_bool(mapping.get("terminal")),
            allowed_next_statuses=coerce_string_items(mapping.get("allowed_next_statuses")),
            schema_version=coerce_int(mapping.get("schema_version"))
            or GOVERNED_EXCEPTION_SCHEMA_VERSION,
        )


@dataclass(frozen=True, slots=True)
class ExceptionPolicy:
    """Repo-pack exception policy projection used by validators."""

    policy_id: str = "default"
    allowed_exception_classes: tuple[str, ...] = field(
        default_factory=lambda: tuple(sorted(ALLOWED_EXCEPTION_CLASS_IDS))
    )
    forbidden_exception_classes: tuple[str, ...] = field(
        default_factory=lambda: tuple(sorted(FORBIDDEN_EXCEPTION_CLASS_IDS))
    )
    required_proof_by_action_kind: Mapping[str, tuple[str, ...]] | None = None
    operator_approval_rules: tuple[str, ...] = ()
    stale_head_policy: str = "fail_closed"
    dirty_worktree_policy: str = "evidence_required"
    remote_publish_policy: str = "remote_ref_and_post_push_required"
    security_guard_policy: str = "never_except"
    schema_version: int = GOVERNED_EXCEPTION_SCHEMA_VERSION
    contract_id: str = EXCEPTION_POLICY_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return json_ready_dict(asdict(self))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "ExceptionPolicy":
        mapping = coerce_mapping(payload)
        proof_by_action: dict[str, tuple[str, ...]] = {}
        proof_payload = mapping.get("required_proof_by_action_kind")
        if isinstance(proof_payload, Mapping):
            for key, value in proof_payload.items():
                proof_by_action[coerce_string(key)] = coerce_string_items(value)
        return cls(
            policy_id=coerce_string(mapping.get("policy_id")) or "default",
            allowed_exception_classes=coerce_string_items(mapping.get("allowed_exception_classes"))
            or tuple(sorted(ALLOWED_EXCEPTION_CLASS_IDS)),
            forbidden_exception_classes=coerce_string_items(mapping.get("forbidden_exception_classes"))
            or tuple(sorted(FORBIDDEN_EXCEPTION_CLASS_IDS)),
            required_proof_by_action_kind=proof_by_action or None,
            operator_approval_rules=coerce_string_items(mapping.get("operator_approval_rules")),
            stale_head_policy=coerce_string(mapping.get("stale_head_policy")) or "fail_closed",
            dirty_worktree_policy=coerce_string(mapping.get("dirty_worktree_policy")) or "evidence_required",
            remote_publish_policy=coerce_string(mapping.get("remote_publish_policy"))
            or "remote_ref_and_post_push_required",
            security_guard_policy=coerce_string(mapping.get("security_guard_policy")) or "never_except",
            schema_version=coerce_int(mapping.get("schema_version"))
            or GOVERNED_EXCEPTION_SCHEMA_VERSION,
        )


__all__ = [
    "ALLOWED_EXCEPTION_CLASS_IDS",
    "FORBIDDEN_EXCEPTION_CLASS_IDS",
    "ExceptionClass",
    "ExceptionLifecycleStatus",
    "ExceptionPolicy",
]
