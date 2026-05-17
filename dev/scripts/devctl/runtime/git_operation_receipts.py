"""Typed receipts for git branch and tag mutations."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from .enum_compat import StrEnum
from .governed_exception_base import json_ready_dict
from .state_store_authority import (
    StateStoreWriteResult,
    append_json_mapping,
    read_json_mappings_strict,
)
from .value_coercion import coerce_string, coerce_string_items

DEFAULT_GIT_OPERATION_RECEIPT_STORE_REL = Path("dev/state/git_operation_receipts.jsonl")
TAG_RECEIPT_CONTRACT_ID = "TagReceipt"
BRANCH_OPERATION_RECEIPT_CONTRACT_ID = "BranchOperationReceipt"
GIT_OPERATION_RECEIPT_SCHEMA_VERSION = 1


class TagOperation(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class BranchOperation(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    CHECKOUT = "checkout"


class GitOperationStatus(StrEnum):
    RECORDED = "recorded"
    FAILED = "failed"
    SUPERSEDED = "superseded"


@dataclass(frozen=True, slots=True)
class TagReceipt:
    receipt_id: str
    tag_name: str
    operation: TagOperation
    target_sha: str
    previous_target_sha: str = ""
    tagger_actor: str = ""
    executed_at_utc: str = ""
    evidence_refs: tuple[str, ...] = ()
    status: GitOperationStatus = GitOperationStatus.RECORDED
    schema_version: int = GIT_OPERATION_RECEIPT_SCHEMA_VERSION
    contract_id: str = TAG_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return json_ready_dict(asdict(self))

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> "TagReceipt":
        return cls(
            receipt_id=coerce_string(mapping.get("receipt_id")),
            tag_name=coerce_string(mapping.get("tag_name")),
            operation=tag_operation_from_value(mapping.get("operation")),
            target_sha=coerce_string(mapping.get("target_sha")),
            previous_target_sha=coerce_string(mapping.get("previous_target_sha")),
            tagger_actor=coerce_string(mapping.get("tagger_actor")),
            executed_at_utc=coerce_string(mapping.get("executed_at_utc")),
            evidence_refs=coerce_string_items(mapping.get("evidence_refs")),
            status=git_operation_status_from_value(mapping.get("status")),
            schema_version=int(mapping.get("schema_version") or 1),
            contract_id=coerce_string(mapping.get("contract_id")) or TAG_RECEIPT_CONTRACT_ID,
        )


@dataclass(frozen=True, slots=True)
class BranchOperationReceipt:
    receipt_id: str
    branch_name: str
    operation: BranchOperation
    new_ref: str
    previous_ref: str = ""
    remote_name: str = ""
    executed_by_actor: str = ""
    executed_at_utc: str = ""
    evidence_refs: tuple[str, ...] = ()
    status: GitOperationStatus = GitOperationStatus.RECORDED
    schema_version: int = GIT_OPERATION_RECEIPT_SCHEMA_VERSION
    contract_id: str = BRANCH_OPERATION_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return json_ready_dict(asdict(self))

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> "BranchOperationReceipt":
        return cls(
            receipt_id=coerce_string(mapping.get("receipt_id")),
            branch_name=coerce_string(mapping.get("branch_name")),
            operation=branch_operation_from_value(mapping.get("operation")),
            new_ref=coerce_string(mapping.get("new_ref")),
            previous_ref=coerce_string(mapping.get("previous_ref")),
            remote_name=coerce_string(mapping.get("remote_name")),
            executed_by_actor=coerce_string(mapping.get("executed_by_actor")),
            executed_at_utc=coerce_string(mapping.get("executed_at_utc")),
            evidence_refs=coerce_string_items(mapping.get("evidence_refs")),
            status=git_operation_status_from_value(mapping.get("status")),
            schema_version=int(mapping.get("schema_version") or 1),
            contract_id=(
                coerce_string(mapping.get("contract_id"))
                or BRANCH_OPERATION_RECEIPT_CONTRACT_ID
            ),
        )


def build_tag_receipt(
    *,
    tag_name: str,
    operation: TagOperation,
    target_sha: str,
    executed_at_utc: str,
    tagger_actor: str,
    previous_target_sha: str = "",
    evidence_refs: Iterable[str] = (),
    status: GitOperationStatus = GitOperationStatus.RECORDED,
) -> TagReceipt:
    receipt_id = git_operation_receipt_id(
        contract_id=TAG_RECEIPT_CONTRACT_ID,
        name=tag_name,
        operation=operation.value,
        executed_at_utc=executed_at_utc,
        refs=(previous_target_sha, target_sha),
    )
    return TagReceipt(
        receipt_id=receipt_id,
        tag_name=tag_name,
        operation=operation,
        target_sha=target_sha,
        previous_target_sha=previous_target_sha,
        tagger_actor=tagger_actor,
        executed_at_utc=executed_at_utc,
        evidence_refs=tuple(evidence_refs),
        status=status,
    )


def build_branch_operation_receipt(
    *,
    branch_name: str,
    operation: BranchOperation,
    new_ref: str,
    executed_at_utc: str,
    executed_by_actor: str,
    previous_ref: str = "",
    remote_name: str = "",
    evidence_refs: Iterable[str] = (),
    status: GitOperationStatus = GitOperationStatus.RECORDED,
) -> BranchOperationReceipt:
    receipt_id = git_operation_receipt_id(
        contract_id=BRANCH_OPERATION_RECEIPT_CONTRACT_ID,
        name=branch_name,
        operation=operation.value,
        executed_at_utc=executed_at_utc,
        refs=(previous_ref, new_ref, remote_name),
    )
    return BranchOperationReceipt(
        receipt_id=receipt_id,
        branch_name=branch_name,
        operation=operation,
        new_ref=new_ref,
        previous_ref=previous_ref,
        remote_name=remote_name,
        executed_by_actor=executed_by_actor,
        executed_at_utc=executed_at_utc,
        evidence_refs=tuple(evidence_refs),
        status=status,
    )


def append_git_operation_receipt(
    path: Path,
    receipt: TagReceipt | BranchOperationReceipt,
) -> StateStoreWriteResult:
    return append_json_mapping(
        path,
        receipt.to_dict(),
        store_id=coerce_string(receipt.contract_id) or "GitOperationReceipt",
    )


def read_tag_receipts(path: Path) -> tuple[TagReceipt, ...]:
    return tuple(
        TagReceipt.from_mapping(row)
        for row in read_json_mappings_strict(path)
        if coerce_string(row.get("contract_id")) == TAG_RECEIPT_CONTRACT_ID
    )


def read_branch_operation_receipts(path: Path) -> tuple[BranchOperationReceipt, ...]:
    return tuple(
        BranchOperationReceipt.from_mapping(row)
        for row in read_json_mappings_strict(path)
        if coerce_string(row.get("contract_id")) == BRANCH_OPERATION_RECEIPT_CONTRACT_ID
    )


def git_operation_receipt_id(
    *,
    contract_id: str,
    name: str,
    operation: str,
    executed_at_utc: str,
    refs: Iterable[str] = (),
) -> str:
    timestamp = (
        executed_at_utc.replace("-", "")
        .replace(":", "")
        .replace(".", "")
        .replace("+0000", "Z")
    )
    seed = "|".join((contract_id, name, operation, executed_at_utc, *refs))
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"git-operation:{operation}:{timestamp}:{digest}"


def tag_operation_from_value(value: object) -> TagOperation:
    if isinstance(value, TagOperation):
        return value
    text = coerce_string(value) or TagOperation.CREATE.value
    return TagOperation(text)


def branch_operation_from_value(value: object) -> BranchOperation:
    if isinstance(value, BranchOperation):
        return value
    text = coerce_string(value) or BranchOperation.UPDATE.value
    return BranchOperation(text)


def git_operation_status_from_value(value: object) -> GitOperationStatus:
    if isinstance(value, GitOperationStatus):
        return value
    text = coerce_string(value) or GitOperationStatus.RECORDED.value
    return GitOperationStatus(text)


__all__ = [
    "BRANCH_OPERATION_RECEIPT_CONTRACT_ID",
    "DEFAULT_GIT_OPERATION_RECEIPT_STORE_REL",
    "GIT_OPERATION_RECEIPT_SCHEMA_VERSION",
    "TAG_RECEIPT_CONTRACT_ID",
    "BranchOperation",
    "BranchOperationReceipt",
    "GitOperationStatus",
    "TagOperation",
    "TagReceipt",
    "append_git_operation_receipt",
    "branch_operation_from_value",
    "build_branch_operation_receipt",
    "build_tag_receipt",
    "git_operation_receipt_id",
    "git_operation_status_from_value",
    "read_branch_operation_receipts",
    "read_tag_receipts",
    "tag_operation_from_value",
]
