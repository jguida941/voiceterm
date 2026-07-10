"""Registry and lookup helpers for governed bypass lifecycles."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

UTC = timezone.utc

from .bypass_lifecycle_models import (
    BypassAuthorityScope,
    BypassLifecycle,
    BypassLifecycleState,
    BypassLifecycleStoreLoadResult,
    BypassReceipt,
)
from .jsonl_support import parse_json_line_dict

_GRANTED_SCOPES: Mapping[BypassAuthorityScope, frozenset[BypassAuthorityScope]] = {
    BypassAuthorityScope.AGENT_SPAWN_ONLY: frozenset(
        {BypassAuthorityScope.AGENT_SPAWN_ONLY}
    ),
    BypassAuthorityScope.EDIT_ONLY: frozenset(
        {
            BypassAuthorityScope.AGENT_SPAWN_ONLY,
            BypassAuthorityScope.EDIT_ONLY,
        }
    ),
    BypassAuthorityScope.EDIT_AND_COMMIT: frozenset(
        {
            BypassAuthorityScope.AGENT_SPAWN_ONLY,
            BypassAuthorityScope.EDIT_ONLY,
            BypassAuthorityScope.EDIT_AND_COMMIT,
        }
    ),
    BypassAuthorityScope.EDIT_COMMIT_AND_PUSH: frozenset(
        {
            BypassAuthorityScope.AGENT_SPAWN_ONLY,
            BypassAuthorityScope.EDIT_ONLY,
            BypassAuthorityScope.EDIT_AND_COMMIT,
            BypassAuthorityScope.EDIT_COMMIT_AND_PUSH,
        }
    ),
}


class BypassLifecycleRegistry:
    """In-process bypass rows issued during one reducer run."""

    def __init__(self) -> None:
        self._receipts: tuple[BypassReceipt, ...] = ()
        self._lifecycles: tuple[BypassLifecycle, ...] = ()

    def register_receipt(self, receipt: BypassReceipt) -> None:
        self._receipts = tuple(
            existing
            for existing in self._receipts
            if existing.receipt_id != receipt.receipt_id
        ) + (receipt,)

    def register_lifecycle(self, lifecycle: BypassLifecycle) -> None:
        self._lifecycles = tuple(
            existing
            for existing in self._lifecycles
            if existing.lifecycle_id != lifecycle.lifecycle_id
        ) + (lifecycle,)

    def lifecycles(self) -> tuple[BypassLifecycle, ...]:
        return self._lifecycles

    def find_receipt(self, receipt_id: str) -> BypassReceipt | None:
        for receipt in reversed(self._receipts):
            if receipt.receipt_id == receipt_id:
                return receipt
        return None


DEFAULT_BYPASS_REGISTRY = BypassLifecycleRegistry()


def registered_bypass_lifecycles() -> tuple[BypassLifecycle, ...]:
    """Return lifecycle rows issued during the current reducer run."""
    return DEFAULT_BYPASS_REGISTRY.lifecycles()


def load_bypass_lifecycles(path: Path) -> tuple[BypassLifecycle, ...]:
    result = load_bypass_lifecycles_with_errors(path)
    if result.errors:
        raise ValueError("; ".join(result.errors))
    return result.lifecycles


def load_bypass_lifecycles_with_errors(path: Path) -> BypassLifecycleStoreLoadResult:
    rows, read_errors = _load_bypass_jsonl(path)
    lifecycles: list[BypassLifecycle] = []
    errors: list[str] = list(read_errors)
    for index, payload in rows:
        try:
            lifecycles.append(BypassLifecycle.from_mapping(payload))
        except (TypeError, ValueError) as exc:
            errors.append(f"{path}: line {index}: invalid_bypass_lifecycle:{exc}")
    return BypassLifecycleStoreLoadResult(
        lifecycles=tuple(lifecycles),
        errors=tuple(errors),
    )


def active_bypass_lifecycles(
    *,
    store_path: Path | None = None,
    target_role: str = "",
    required_scope: BypassAuthorityScope = BypassAuthorityScope.EDIT_ONLY,
    now_utc: datetime | None = None,
) -> tuple[BypassLifecycle, ...]:
    """Load active bypass lifecycle rows from durable state plus this process."""
    lifecycles = list(registered_bypass_lifecycles())
    if store_path is not None:
        lifecycles.extend(load_bypass_lifecycles(store_path))
    deduped = {lifecycle.lifecycle_id: lifecycle for lifecycle in lifecycles}
    return tuple(
        lifecycle
        for lifecycle in deduped.values()
        if bypass_lifecycle_active(
            lifecycle,
            required_scope=required_scope,
            target_role=target_role,
            now_utc=now_utc,
        )
    )


def active_bypass_lifecycle_for_receipt_id(
    receipt_id: str,
    *,
    store_path: Path | None = None,
    required_scope: BypassAuthorityScope = BypassAuthorityScope.EDIT_ONLY,
    target_role: str = "",
    now_utc: datetime | None = None,
) -> BypassLifecycle | None:
    """Resolve one active lifecycle by typed receipt id."""
    normalized = receipt_id.strip()
    if not normalized:
        return None
    for lifecycle in reversed(
        active_bypass_lifecycles(
            store_path=store_path,
            required_scope=required_scope,
            target_role=target_role,
            now_utc=now_utc,
        )
    ):
        if lifecycle.receipt and lifecycle.receipt.receipt_id == normalized:
            return lifecycle
    return None


def bypass_lifecycle_active(
    lifecycle: BypassLifecycle,
    *,
    required_scope: BypassAuthorityScope = BypassAuthorityScope.EDIT_ONLY,
    target_role: str = "",
    now_utc: datetime | None = None,
) -> bool:
    """Return True when an active lifecycle can grant the requested scope."""
    if lifecycle.state is not BypassLifecycleState.ACTIVE:
        return False
    if target_role and lifecycle.request.target_role not in {"", target_role}:
        return False
    if lifecycle.receipt is None:
        return False
    return bypass_receipt_active(
        lifecycle.receipt,
        now_utc=now_utc,
    ) and bypass_receipt_grants_scope(lifecycle.receipt, required_scope)


def is_bypass_active(receipt_id: str, action_class: BypassAuthorityScope) -> bool:
    """Return True iff a registered receipt grants the action and is current."""
    receipt = DEFAULT_BYPASS_REGISTRY.find_receipt(receipt_id)
    if receipt is None:
        return False
    return bypass_receipt_active(receipt) and bypass_receipt_grants_scope(
        receipt, action_class
    )


def bypass_receipt_active(
    receipt: BypassReceipt, *, now_utc: datetime | None = None
) -> bool:
    """Return whether the receipt is currently usable."""
    if receipt.revoked_at_utc:
        return False
    if not receipt.expires_at_utc:
        return True
    expires_at = _parse_utc(receipt.expires_at_utc)
    if expires_at is None:
        return False
    effective_now = now_utc or datetime.now(UTC)
    if effective_now.tzinfo is None:
        effective_now = effective_now.replace(tzinfo=UTC)
    return expires_at > effective_now.astimezone(UTC)


def bypass_receipt_grants_scope(
    receipt: BypassReceipt, action_class: BypassAuthorityScope
) -> bool:
    """Return whether receipt scope includes the requested action class."""
    return action_class in _GRANTED_SCOPES[receipt.requested_authority_scope]


def _parse_utc(value: str) -> datetime | None:
    normalized = value.strip()
    if not normalized:
        return None
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _load_bypass_jsonl(
    path: Path,
) -> tuple[tuple[int, Mapping[str, object]], tuple[str, ...]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return (), ()
    errors: list[str] = []
    rows: list[tuple[int, Mapping[str, object]]] = []
    for index, line in enumerate(lines, start=1):
        payload = parse_json_line_dict(
            line,
            source=str(path),
            line_number=index,
            warning_sink=lambda message: errors.append(message),
        )
        if payload is not None:
            rows.append((index, payload))
    return tuple(rows), tuple(errors)


__all__ = [
    "DEFAULT_BYPASS_REGISTRY",
    "active_bypass_lifecycle_for_receipt_id",
    "active_bypass_lifecycles",
    "bypass_lifecycle_active",
    "bypass_receipt_active",
    "bypass_receipt_grants_scope",
    "is_bypass_active",
    "load_bypass_lifecycles",
    "load_bypass_lifecycles_with_errors",
    "registered_bypass_lifecycles",
]
