"""Typed receipts for operator-authorized raw git commit and push paths."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from .bypass_lifecycle_registry import (
    active_bypass_lifecycle_for_receipt_id,
    active_bypass_lifecycles,
)
from .bypass_lifecycle_models import BypassAuthorityScope, BypassLifecycle
from .governed_exception_lifecycle import GovernedExceptionLifecycle
from .governed_exception_base import json_ready_dict
from .governed_exception_receipts import ExceptionReceipt
from .governed_exception_store import DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL
from .state_store_authority import (
    StateStoreWriteResult,
    append_json_mapping,
    read_json_mappings_strict,
)
from .value_coercion import coerce_string, coerce_string_items

DEFAULT_RAW_GIT_BYPASS_RECEIPT_STORE_REL = Path(
    "dev/state/raw_git_bypass_receipts.jsonl"
)
DEFAULT_BYPASS_LIFECYCLE_STORE_REL = Path("dev/state/bypass_lifecycles.jsonl")
RAW_GIT_BYPASS_GUARD_ID = "raw_git_bypass_receipt"
RAW_GIT_BYPASS_VALIDATION_PLAN_ID = "MP-378-ARCH-SELF-IMPROVEMENT-LOOP-P10"


class RawGitVerb(StrEnum):
    COMMIT = "commit"
    PUSH = "push"


class RawGitBypassAuthority(StrEnum):
    OPERATOR_WITNESSED = "operator_witnessed"
    BYPASS_LIFECYCLE_RECEIPT = "bypass_lifecycle_receipt"
    AGENT_LOOP_OPERATOR_OVERRIDE = "agent_loop_operator_override"


@dataclass(frozen=True, slots=True)
class RawGitBypassReceipt:
    receipt_id: str
    git_verb: RawGitVerb
    commit_sha: str = ""
    push_range: tuple[str, str] = ()
    affected_paths: tuple[str, ...] = ()
    bypass_authority: RawGitBypassAuthority = RawGitBypassAuthority.OPERATOR_WITNESSED
    bypass_lifecycle_id: str = ""
    governed_exception_id: str = ""
    operator_quote_evidence_ref: str = ""
    executed_at_utc: str = ""
    executed_by_actor: str = ""
    skipped_pre_hooks: tuple[str, ...] = ()
    git_args: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = "RawGitBypassReceipt"

    def to_dict(self) -> dict[str, object]:
        return json_ready_dict(asdict(self))

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> "RawGitBypassReceipt":
        payload = coerce_mapping(mapping)
        return cls(
            receipt_id=coerce_string(payload.get("receipt_id")),
            git_verb=raw_git_verb_from_value(payload.get("git_verb")),
            commit_sha=coerce_string(payload.get("commit_sha")),
            push_range=_push_range_from_value(payload.get("push_range")),
            affected_paths=coerce_string_items(payload.get("affected_paths")),
            bypass_authority=raw_git_authority_from_value(
                payload.get("bypass_authority")
            ),
            bypass_lifecycle_id=coerce_string(payload.get("bypass_lifecycle_id")),
            governed_exception_id=coerce_string(payload.get("governed_exception_id")),
            operator_quote_evidence_ref=coerce_string(
                payload.get("operator_quote_evidence_ref")
            ),
            executed_at_utc=coerce_string(payload.get("executed_at_utc")),
            executed_by_actor=coerce_string(payload.get("executed_by_actor")),
            skipped_pre_hooks=coerce_string_items(payload.get("skipped_pre_hooks")),
            git_args=coerce_string_items(payload.get("git_args")),
            schema_version=int(payload.get("schema_version") or 1),
            contract_id=coerce_string(payload.get("contract_id"))
            or "RawGitBypassReceipt",
        )


def build_raw_git_bypass_receipt(
    *,
    git_verb: RawGitVerb,
    executed_at_utc: str,
    executed_by_actor: str,
    bypass_authority: RawGitBypassAuthority,
    commit_sha: str = "",
    push_range: tuple[str, str] = (),
    affected_paths: tuple[str, ...] = (),
    bypass_lifecycle_id: str = "",
    governed_exception_id: str = "",
    operator_quote_evidence_ref: str = "",
    skipped_pre_hooks: tuple[str, ...] = (),
    git_args: tuple[str, ...] = (),
) -> RawGitBypassReceipt:
    receipt_id = raw_git_bypass_receipt_id(
        git_verb=git_verb,
        executed_at_utc=executed_at_utc,
        commit_sha=commit_sha,
        push_range=push_range,
        git_args=git_args,
    )
    return RawGitBypassReceipt(
        receipt_id=receipt_id,
        git_verb=git_verb,
        commit_sha=commit_sha,
        push_range=push_range,
        affected_paths=affected_paths,
        bypass_authority=bypass_authority,
        bypass_lifecycle_id=bypass_lifecycle_id,
        governed_exception_id=governed_exception_id,
        operator_quote_evidence_ref=operator_quote_evidence_ref,
        executed_at_utc=executed_at_utc,
        executed_by_actor=executed_by_actor,
        skipped_pre_hooks=skipped_pre_hooks,
        git_args=git_args,
    )


@dataclass(frozen=True, slots=True)
class RawGitBypassReceiptAppendResult:
    receipt: RawGitBypassReceipt
    receipt_write: StateStoreWriteResult
    governed_exception_write: StateStoreWriteResult | None = None

    @property
    def record_count(self) -> int:
        return self.receipt_write.record_count

    def to_dict(self) -> dict[str, object]:
        return {
            "receipt": self.receipt.to_dict(),
            "receipt_write": self.receipt_write.to_dict(),
            "governed_exception_write": (
                self.governed_exception_write.to_dict()
                if self.governed_exception_write is not None
                else None
            ),
        }


def raw_git_bypass_receipt_id(
    *,
    git_verb: RawGitVerb,
    executed_at_utc: str,
    commit_sha: str,
    push_range: tuple[str, str],
    git_args: tuple[str, ...],
) -> str:
    timestamp = (
        executed_at_utc.replace("-", "")
        .replace(":", "")
        .replace(".", "")
        .replace("+0000", "Z")
    )
    seed = "|".join((git_verb.value, executed_at_utc, commit_sha, *push_range, *git_args))
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"raw-git:{git_verb.value}:{timestamp}:{digest}"


def append_raw_git_bypass_receipt(
    path: Path,
    receipt: RawGitBypassReceipt,
    *,
    bypass_lifecycle_store_path: Path | None = None,
    governed_exception_store_path: Path | None = None,
) -> RawGitBypassReceiptAppendResult:
    linked_lifecycle = _validate_lifecycle_linkage(
        receipt,
        store_path=bypass_lifecycle_store_path or _sibling_state_path(
            path,
            DEFAULT_BYPASS_LIFECYCLE_STORE_REL.name,
        ),
    )
    governed_exception = build_raw_git_governed_exception_lifecycle(
        receipt,
        linked_lifecycle=linked_lifecycle,
    )
    receipt_to_write = replace(
        receipt,
        governed_exception_id=receipt.governed_exception_id
        or governed_exception.lifecycle_id,
    )
    exception_write = append_json_mapping(
        governed_exception_store_path
        or _sibling_state_path(
            path,
            DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL.name,
        ),
        governed_exception.to_dict(),
        store_id="GovernedExceptionLifecycle",
    )
    receipt_write = append_json_mapping(
        path,
        receipt_to_write.to_dict(),
        store_id="RawGitBypassReceipt",
    )
    return RawGitBypassReceiptAppendResult(
        receipt=receipt_to_write,
        receipt_write=receipt_write,
        governed_exception_write=exception_write,
    )


def read_raw_git_bypass_receipts(path: Path) -> tuple[RawGitBypassReceipt, ...]:
    return tuple(
        RawGitBypassReceipt.from_mapping(row)
        for row in read_json_mappings_strict(path)
    )


def raw_git_verb_from_value(value: object) -> RawGitVerb:
    raw = coerce_string(value)
    try:
        return RawGitVerb(raw)
    except ValueError as exc:
        raise ValueError(f"unknown_raw_git_verb: {raw}") from exc


def raw_git_authority_from_value(value: object) -> RawGitBypassAuthority:
    raw = coerce_string(value) or RawGitBypassAuthority.OPERATOR_WITNESSED.value
    try:
        return RawGitBypassAuthority(raw)
    except ValueError as exc:
        raise ValueError(f"unknown_raw_git_bypass_authority: {raw}") from exc


def coerce_mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return cast(Mapping[str, object], value)


def _push_range_from_value(value: object) -> tuple[str, str]:
    items = coerce_string_items(value)
    if len(items) < 2:
        return ()
    return (items[0], items[1])


def build_raw_git_governed_exception_lifecycle(
    receipt: RawGitBypassReceipt,
    *,
    linked_lifecycle: BypassLifecycle | None = None,
) -> GovernedExceptionLifecycle:
    head = receipt.commit_sha or (receipt.push_range[1] if receipt.push_range else "")
    lifecycle_id = receipt.governed_exception_id or f"gel:{receipt.receipt_id}"
    exception = ExceptionReceipt(
        receipt_id=f"exception:{receipt.receipt_id}",
        action_kind=f"vcs.{receipt.git_verb.value}",
        phase="raw_git_bypass_execution",
        guard_id=RAW_GIT_BYPASS_GUARD_ID,
        exception_class="operator_lifetime_bypass",
        operator_reason=(
            f"Operator-authorized raw git {receipt.git_verb.value} recorded by "
            f"RawGitBypassReceipt {receipt.receipt_id}."
        ),
        head=head,
        scope=receipt.bypass_authority.value,
        planned_finding_ingest_ref=f"raw_git_bypass_receipt:{receipt.receipt_id}",
        authority_evidence_refs=_authority_evidence_refs(receipt, linked_lifecycle),
        worktree_safety_evidence_refs=_worktree_safety_evidence_refs(receipt),
        validation_plan_id=RAW_GIT_BYPASS_VALIDATION_PLAN_ID,
        execution_status="operator_approved",
        remote_ref_verified=receipt.git_verb is RawGitVerb.PUSH and bool(receipt.push_range),
        post_push_proof_ref=(
            f"raw_git_bypass_receipt:{receipt.receipt_id}"
            if receipt.git_verb is RawGitVerb.PUSH and receipt.push_range
            else ""
        ),
        created_at_utc=receipt.executed_at_utc,
    )
    return GovernedExceptionLifecycle(
        lifecycle_id=lifecycle_id,
        status="operator_approved",
        exception=exception,
        planned_finding_ingest_ref=f"raw_git_bypass_receipt:{receipt.receipt_id}",
        validation_plan_id=RAW_GIT_BYPASS_VALIDATION_PLAN_ID,
        authority_evidence_refs=_authority_evidence_refs(receipt, linked_lifecycle),
        worktree_safety_evidence_refs=_worktree_safety_evidence_refs(receipt),
        system_map_contract_ids=(
            "RawGitBypassReceipt",
            "GovernedExceptionLifecycle",
            "BypassLifecycle",
        ),
        developer_loop_refs=tuple(
            ref
            for ref in (
                receipt.operator_quote_evidence_ref,
                f"raw_git_bypass_receipt:{receipt.receipt_id}",
            )
            if ref
        ),
        created_at_utc=receipt.executed_at_utc,
        updated_at_utc=receipt.executed_at_utc,
    )


def _validate_lifecycle_linkage(
    receipt: RawGitBypassReceipt,
    *,
    store_path: Path | None,
) -> BypassLifecycle | None:
    if receipt.bypass_authority is not RawGitBypassAuthority.BYPASS_LIFECYCLE_RECEIPT:
        return None
    requested_ref = receipt.bypass_lifecycle_id.strip()
    if not requested_ref:
        raise ValueError("bypass_lifecycle_id required for bypass_lifecycle_receipt")
    required_scope = _required_bypass_scope(receipt.git_verb)
    lifecycle = active_bypass_lifecycle_for_receipt_id(
        requested_ref,
        store_path=store_path,
        required_scope=required_scope,
    )
    if lifecycle is not None:
        return lifecycle
    for candidate in active_bypass_lifecycles(
        store_path=store_path,
        required_scope=required_scope,
    ):
        if candidate.lifecycle_id == requested_ref:
            return candidate
    raise ValueError("bypass_lifecycle_id not active or not found")


def _required_bypass_scope(verb: RawGitVerb) -> BypassAuthorityScope:
    if verb is RawGitVerb.COMMIT:
        return BypassAuthorityScope.EDIT_AND_COMMIT
    return BypassAuthorityScope.EDIT_COMMIT_AND_PUSH


def _authority_evidence_refs(
    receipt: RawGitBypassReceipt,
    linked_lifecycle: BypassLifecycle | None,
) -> tuple[str, ...]:
    refs = [
        receipt.operator_quote_evidence_ref,
        f"raw_git_bypass_receipt:{receipt.receipt_id}",
        f"bypass_authority:{receipt.bypass_authority.value}",
    ]
    if receipt.bypass_lifecycle_id:
        refs.append(f"bypass_lifecycle_ref:{receipt.bypass_lifecycle_id}")
    if linked_lifecycle is not None:
        refs.append(f"bypass_lifecycle:{linked_lifecycle.lifecycle_id}")
        if linked_lifecycle.receipt is not None:
            refs.append(f"bypass_receipt:{linked_lifecycle.receipt.receipt_id}")
    return tuple(ref for ref in refs if ref)


def _worktree_safety_evidence_refs(receipt: RawGitBypassReceipt) -> tuple[str, ...]:
    refs = [
        f"raw_git_verb:{receipt.git_verb.value}",
        f"affected_path_count:{len(receipt.affected_paths)}",
    ]
    if receipt.skipped_pre_hooks:
        refs.append("skipped_pre_hooks:" + ",".join(receipt.skipped_pre_hooks))
    if receipt.git_verb is RawGitVerb.PUSH and receipt.push_range:
        refs.append(f"push_range:{receipt.push_range[0]}..{receipt.push_range[1]}")
    if receipt.git_verb is RawGitVerb.COMMIT and receipt.commit_sha:
        refs.append(f"commit:{receipt.commit_sha}")
    return tuple(refs)


def _sibling_state_path(path: Path, filename: str) -> Path:
    if path.name:
        return path.with_name(filename)
    return Path("dev/state") / filename


__all__ = [
    "DEFAULT_BYPASS_LIFECYCLE_STORE_REL",
    "DEFAULT_RAW_GIT_BYPASS_RECEIPT_STORE_REL",
    "RawGitBypassAuthority",
    "RawGitBypassReceipt",
    "RawGitBypassReceiptAppendResult",
    "RawGitVerb",
    "append_raw_git_bypass_receipt",
    "build_raw_git_governed_exception_lifecycle",
    "build_raw_git_bypass_receipt",
    "raw_git_authority_from_value",
    "raw_git_bypass_receipt_id",
    "raw_git_verb_from_value",
    "read_raw_git_bypass_receipts",
]
