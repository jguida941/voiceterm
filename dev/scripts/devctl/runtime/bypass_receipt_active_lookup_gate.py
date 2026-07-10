"""Typed gate verifying an active BypassReceipt exists for override prose.

Slice 5 of R313 A7 (T3): the final-response gate previously surfaced
``bypass_receipt_kind="BypassReceipt"`` inside ``TypedGateFailure`` and let
``is_active_edit_only_override`` allow continuation prose whenever an
``agent_decision`` carried loose flags (``operator_override_edit_allowed``,
``operator_override_active``, ``operator_override_scope == "edit-only"``).

That was a Type-2 thin proof: the kind string was named but no code verified
that an actual ``BypassReceipt`` lifecycle row existed and was active for the
edit-only scope. This module is the Type-5 composed proof: when override prose
is active, load active bypass lifecycles from the durable store, return the
matching ``BypassReceipt`` if one is found, and emit a typed
``BypassReceiptActiveLookupCheck`` with a machine-readable failure code when
none is present.

The reader does not mutate state. It only inspects active lifecycles via
``active_bypass_lifecycles`` and classifies the result.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .bypass_lifecycle_models import (
    DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
    BypassAuthorityScope,
    BypassLifecycle,
    BypassReceipt,
)
from .bypass_lifecycle_registry import active_bypass_lifecycles
from .enum_compat import StrEnum

BYPASS_RECEIPT_ACTIVE_LOOKUP_CHECK_CONTRACT_ID = "BypassReceiptActiveLookupCheck"
BYPASS_RECEIPT_ACTIVE_LOOKUP_CHECK_SCHEMA_VERSION = 1


class BypassReceiptActiveLookupFailureCode(StrEnum):
    """Machine-readable failure codes for the bypass-receipt active-lookup gate."""

    OK = "ok"
    BYPASS_RECEIPT_NOT_PRESENT = "bypass_receipt_not_present"
    BYPASS_RECEIPT_EXPIRED = "bypass_receipt_expired"
    BYPASS_RECEIPT_SCOPE_INSUFFICIENT = "bypass_receipt_scope_insufficient"


@dataclass(frozen=True, slots=True)
class BypassReceiptActiveLookupCheck:
    """Result of inspecting active bypass lifecycles for an override claim."""

    ok: bool
    failure_code: BypassReceiptActiveLookupFailureCode
    receipt: BypassReceipt | None = None
    lifecycle: BypassLifecycle | None = None
    required_scope: BypassAuthorityScope = BypassAuthorityScope.EDIT_ONLY
    target_role: str = ""
    schema_version: int = BYPASS_RECEIPT_ACTIVE_LOOKUP_CHECK_SCHEMA_VERSION
    contract_id: str = BYPASS_RECEIPT_ACTIVE_LOOKUP_CHECK_CONTRACT_ID


def require_active_bypass_receipt_for_override(
    *,
    repo_root: Path | None,
    required_scope: BypassAuthorityScope = BypassAuthorityScope.EDIT_ONLY,
    target_role: str = "",
    now_utc: datetime | None = None,
) -> BypassReceiptActiveLookupCheck:
    """Return a typed check classifying whether an active receipt is present.

    Loads active bypass lifecycles from the durable store (composed with any
    in-process registry rows) and returns the most recent active match. When
    no active match exists, the check fails with
    ``BYPASS_RECEIPT_NOT_PRESENT`` so callers can downgrade
    ``allow_final_response`` and refuse to honor loose override prose.
    """

    store_path: Path | None = None
    if repo_root is not None:
        candidate = repo_root / DEFAULT_BYPASS_LIFECYCLE_STORE_REL
        if candidate.exists():
            store_path = candidate

    lifecycles = active_bypass_lifecycles(
        store_path=store_path,
        target_role=target_role,
        required_scope=required_scope,
        now_utc=now_utc,
    )
    for lifecycle in reversed(lifecycles):
        if lifecycle.receipt is None:
            continue
        return BypassReceiptActiveLookupCheck(
            ok=True,
            failure_code=BypassReceiptActiveLookupFailureCode.OK,
            receipt=lifecycle.receipt,
            lifecycle=lifecycle,
            required_scope=required_scope,
            target_role=target_role,
        )
    return BypassReceiptActiveLookupCheck(
        ok=False,
        failure_code=BypassReceiptActiveLookupFailureCode.BYPASS_RECEIPT_NOT_PRESENT,
        required_scope=required_scope,
        target_role=target_role,
    )


__all__ = [
    "BYPASS_RECEIPT_ACTIVE_LOOKUP_CHECK_CONTRACT_ID",
    "BYPASS_RECEIPT_ACTIVE_LOOKUP_CHECK_SCHEMA_VERSION",
    "BypassReceiptActiveLookupCheck",
    "BypassReceiptActiveLookupFailureCode",
    "require_active_bypass_receipt_for_override",
]
